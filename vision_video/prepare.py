"""Record picks, upscale picks to 1620x2880 canvases (Real-ESRGAN), compute depth. Resumable."""
import json, sys, pathlib, numpy as np, cv2
sys.path.insert(0, "lib")
import upscale, depth

PICKS = {1: 11, 2: 23, 3: 37, 4: 23, 5: 11, 6: 23, 7: 51, 8: 11, 9: 23, 10: 51, 11: 11, 12: 23, 13: 51, 14: 11,
         15: 23, 16: 11, 17: 51, 18: 11, 19: 23, 20: 11, 21: 64, 22: 23, 23: 11, 24: 23, 25: 23, 26: 11, 27: 11}
ROOT = pathlib.Path(__file__).parent
man = json.loads((ROOT / "manifest.json").read_text())
only = {int(a) for a in sys.argv[1:]}
for sid, seed in PICKS.items():
    if only and sid not in only:
        continue
    e = man["shots"][str(sid)]
    raw = ROOT / f"stills/raw/shot{sid:02d}_s{seed}.png"
    canvas = ROOT / f"stills/canvas/shot{sid:02d}.jpg"
    dmap = ROOT / f"stills/depth/shot{sid:02d}.png"
    final = ROOT / f"stills/final/shot{sid:02d}.jpg"
    if e.get("pick") != seed:
        for p in (canvas, dmap, final):
            p.unlink(missing_ok=True)
    e["pick"] = seed
    if not canvas.exists():
        upscale.to_canvas(raw, canvas)
    if not dmap.exists():
        im = cv2.cvtColor(cv2.imread(str(canvas)), cv2.COLOR_BGR2RGB)
        d = depth.disparity(im)
        cv2.imwrite(str(dmap), (d * 65535).astype(np.uint16))
    if not final.exists():
        cv2.imwrite(str(final), cv2.resize(cv2.imread(str(canvas)), (1080, 1920), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 94])
    e.update(canvas=str(canvas.relative_to(ROOT)), depth=str(dmap.relative_to(ROOT)), still=str(final.relative_to(ROOT)),
             upscaler="Real-ESRGAN general x4v3 (ONNX, CPU) + Lanczos", depth_model="Depth Anything V2 Small (ONNX, CPU)")
    (ROOT / "manifest.json").write_text(json.dumps(man, indent=1))
    print("prepared", sid, flush=True)
