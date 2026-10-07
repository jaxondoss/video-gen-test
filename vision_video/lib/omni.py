"""Free image backends: prompt-hash cache, exponential backoff, per-call timeout, and a free-use
log line before every upstream call (hard rule 1). Anything not in FREE_MODELS is refused.

OmniRoute (localhost:20128) was used for discovery; its own image routes can't reach a working
upstream here (see models_report.md), so these backends call the same free providers directly."""
import base64, datetime, hashlib, json, os, pathlib, time
import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
CACHE = ROOT / "cache"
LOGS = ROOT / "logs"
CF = f"https://api.cloudflare.com/client/v4/accounts/{os.environ.get('CLOUDFLARE_ACCOUNT_ID','')}/ai/run/"
NEURON_CAP_PER_DAY = 5000  # well under Cloudflare's 10,000/day free allocation

FREE_MODELS = {
    "cf/sdxl-base": ("@cf/stabilityai/stable-diffusion-xl-base-1.0",
                     "Cloudflare catalog lists price $0 per step (beta)."),
    "cf/sdxl-lightning": ("@cf/bytedance/stable-diffusion-xl-lightning",
                          "Cloudflare catalog lists price $0 per step (beta)."),
    "cf/flux-schnell": ("@cf/black-forest-labs/flux-1-schnell",
                        "Inside Cloudflare's free 10,000 neurons/day allocation (all plans); capped locally at 5,000/day."),
    "hf/flux-schnell": ("black-forest-labs/FLUX.1-schnell",
                        "HF free account (isPro=false, canPay=false): monthly free credits only, cannot be charged."),
}


def _key(model, prompt, size, seed, steps):
    return hashlib.sha256(json.dumps([model, prompt, size, seed, steps]).encode()).hexdigest()[:20]


def _neurons_today(add=0.0):
    f = LOGS / "neurons.json"
    d = json.loads(f.read_text()) if f.exists() else {}
    day = datetime.date.today().isoformat()
    d[day] = d.get(day, 0) + add
    f.write_text(json.dumps(d))
    return d[day]


def _flux_neurons(steps):  # 1024x1024 = 4 tiles x 4.8 + steps x 9.6 (Cloudflare pricing)
    return 4 * 4.8 + steps * 9.6


def _call(model, prompt, w, h, seed, steps, neg, timeout):
    mid = FREE_MODELS[model][0]
    if model.startswith("cf/"):
        hdr = {"Authorization": f"Bearer {os.environ['CLOUDFLARE_API_TOKEN']}"}
        if model == "cf/flux-schnell":  # fixed 1024x1024, no seed parameter
            body = {"prompt": prompt, "steps": steps}
        else:
            body = {"prompt": prompt, "seed": seed, "width": w, "height": h, "num_steps": steps,
                    "negative_prompt": neg, "guidance": 7.0}
        r = requests.post(CF + mid, headers=hdr, json=body, timeout=timeout)
        if r.ok and r.headers.get("content-type", "").startswith("image/"):
            return r, r.content
        if r.ok:
            return r, base64.b64decode(r.json()["result"]["image"])
        return r, None
    hdr = {"Authorization": f"Bearer {os.environ['HF_TOKEN']}"}
    body = {"model": mid, "prompt": prompt, "size": f"{w}x{h}", "response_format": "b64_json", "seed": seed}
    r = requests.post("https://router.huggingface.co/nscale/v1/images/generations", headers=hdr, json=body, timeout=timeout)
    return r, (base64.b64decode(r.json()["data"][0]["b64_json"]) if r.ok else None)


def generate(model, prompt, w=768, h=1344, seed=0, steps=20, neg="", timeout=180, retries=5):
    """Returns (path, seconds, cached). Raises on final failure."""
    if model not in FREE_MODELS:
        raise PermissionError(f"{model} is not on the verified-free list; refusing to call it")
    CACHE.mkdir(exist_ok=True); LOGS.mkdir(exist_ok=True)
    out = CACHE / f"{_key(model, prompt, (w, h), seed, steps)}.png"
    if out.exists():
        return out, 0.0, True
    if model == "cf/flux-schnell" and _neurons_today() + _flux_neurons(steps) > NEURON_CAP_PER_DAY:
        raise PermissionError("local Cloudflare neuron cap reached for today; switch to the fallback")
    with (LOGS / "free_calls.log").open("a") as f:
        f.write(f"{datetime.datetime.utcnow().isoformat()}Z {model} ({FREE_MODELS[model][0]}) {w}x{h} seed={seed} :: {FREE_MODELS[model][1]}\n")
    delay, last = 4, None
    for _ in range(retries):
        t0 = time.time()
        try:
            r, data = _call(model, prompt, w, h, seed, steps, neg, timeout)
            if data:
                out.write_bytes(data)
                if model == "cf/flux-schnell":
                    _neurons_today(_flux_neurons(steps))
                return out, time.time() - t0, False
            if r.status_code == 402:
                raise PermissionError(f"402 from {model}: free quota exhausted, not retrying")
            if r.status_code not in (408, 429, 500, 502, 503, 504):
                raise RuntimeError(f"{r.status_code} {r.text[:300]}")
            last = f"{r.status_code} {r.text[:200]}"
        except (requests.Timeout, requests.ConnectionError) as e:
            last = repr(e)
        time.sleep(delay)
        delay = min(delay * 2, 120)
    raise RuntimeError(f"{model} failed after {retries} tries: {last}")
