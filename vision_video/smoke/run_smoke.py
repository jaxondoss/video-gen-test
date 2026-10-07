import sys, json; sys.path.insert(0, 'lib')
from omni import generate, FREE_MODELS
from PIL import Image
P = ("Candid luxury lifestyle photograph, shot on a full-frame camera with a 35mm lens, cinematic infinity pool edge "
     "overlooking a city skyline at golden hour, natural light, shallow depth of field, subtle film grain, photorealistic, vertical composition")
NEG = "text, letters, words, logos, brand names, watermark, captions, license plates, signage, UI elements, cartoon, painting, blurry"
res = {}
for m, steps in [("cf/sdxl-base", 20), ("cf/sdxl-lightning", 8), ("cf/flux-schnell", 6), ("hf/flux-schnell", 4)]:
    try:
        p, s, c = generate(m, P + ". Avoid: " + NEG if 'flux' in m else P, w=768, h=1344, seed=7, steps=steps, neg=NEG, timeout=150, retries=2)
        w, h = Image.open(p).size
        res[m] = {"ok": True, "native": f"{w}x{h}", "secs": round(s, 1), "file": str(p)}
    except Exception as e:
        res[m] = {"ok": False, "error": str(e)[:250]}
    print(m, res[m], flush=True)
json.dump(res, open('smoke/smoke_results.json', 'w'), indent=1)
