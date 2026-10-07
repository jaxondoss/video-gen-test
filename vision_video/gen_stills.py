"""Phase 3: 2 candidates per shot, resumable via manifest.json. Usage: python3 gen_stills.py [shot ids...] [--seeds a,b]"""
import json, sys, pathlib, shutil
sys.path.insert(0, "lib")
from omni import generate
from shots import SHOTS, NEG, prompt

ROOT = pathlib.Path(__file__).parent
MAN = ROOT / "manifest.json"
man = json.loads(MAN.read_text()) if MAN.exists() else {"shots": {}}
args = [a for a in sys.argv[1:] if not a.startswith("--")]
seeds = [11, 23]
for a in sys.argv[1:]:
    if a.startswith("--seeds="):
        seeds = [int(x) for x in a.split("=")[1].split(",")]
want = {int(a) for a in args} or {s[0] for s in SHOTS if s[3]}
for s in SHOTS:
    sid = s[0]
    if sid not in want or not s[3]:
        continue
    entry = man["shots"].setdefault(str(sid), {})
    entry.update(frames=s[1], phase=s[2], motion=s[4], transition=s[5], prompt=prompt(s), negative=NEG)
    cands = entry.setdefault("candidates", [])
    for seed in seeds:
        if any(c["seed"] == seed and pathlib.Path(c["file"]).exists() for c in cands):
            continue
        for model, steps in (("cf/sdxl-base", 20), ("cf/sdxl-lightning", 8)):
            try:
                p, secs, cached = generate(model, prompt(s), 768, 1344, seed=seed, steps=steps, neg=NEG)
                dst = ROOT / "stills" / "raw" / f"shot{sid:02d}_s{seed}.png"
                shutil.copy(p, dst)
                cands.append({"seed": seed, "model": model, "file": str(dst.relative_to(ROOT)), "secs": round(secs, 1)})
                print(f"shot {sid} seed {seed} {model} {secs:.0f}s", flush=True)
                break
            except Exception as e:
                print(f"shot {sid} seed {seed} {model} FAILED: {str(e)[:120]}", flush=True)
        MAN.write_text(json.dumps(man, indent=1))
