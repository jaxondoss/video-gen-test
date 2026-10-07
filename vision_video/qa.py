"""Phase 6 QA: ffprobe checks, black-frame scan, preview_contact_strip.jpg (one frame every 2 s)."""
import json, pathlib, subprocess, sys
import cv2, numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent / "lib"))
from sheets import grid

ROOT = pathlib.Path(__file__).parent
V = str(ROOT / "final.mp4")
p = json.loads(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", V],
                              capture_output=True, text=True, check=True).stdout)
vs = [s for s in p["streams"] if s["codec_type"] == "video"]
aud = [s for s in p["streams"] if s["codec_type"] == "audio"]
v = vs[0]
checks = {
    "codec h264": v["codec_name"] == "h264",
    "1080x1920": (v["width"], v["height"]) == (1080, 1920),
    "24 fps": v["r_frame_rate"] == "24/1",
    "720 frames": int(v["nb_read_frames"]) == 720,
    "30.000 s": abs(float(p["format"]["duration"]) - 30.0) < 1e-3,
    "yuv420p": v["pix_fmt"] == "yuv420p",
    "no audio": not aud,
}
cap = cv2.VideoCapture(V); means, idx, thumbs = [], 0, []
tmp = ROOT / "frames_preview"; tmp.mkdir(exist_ok=True)
while True:
    ok, fr = cap.read()
    if not ok:
        break
    means.append(float(fr.mean()))
    if idx % 48 == 24:  # every 2 s, mid-second
        f = tmp / f"t{idx // 24:02d}.jpg"; cv2.imwrite(str(f), fr); thumbs.append((f"{idx / 24:.0f}s", str(f)))
    idx += 1
black = [i for i, m in enumerate(means) if m < 6]
checks["no black frames (except final fade)"] = all(i >= 708 for i in black)
grid(thumbs, str(ROOT / "preview_contact_strip.jpg"), cols=len(thumbs), tw=180)
for k, ok in checks.items():
    print(("PASS " if ok else "FAIL ") + k)
print("frames:", idx, "duration:", p["format"]["duration"], "black frames:", black[:20])
sys.exit(0 if all(checks.values()) else 1)
