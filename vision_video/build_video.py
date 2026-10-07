"""Phases 4-6: render 720 frames (parallax, transitions, grade) to frames/, then encode final.mp4.
Resumable: existing frames are skipped. `python3 build_video.py --shots 12,13` re-renders only those shots."""
import json, pathlib, subprocess, sys, math
import cv2, numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent / "lib"))
import render as R
from grid import Grid
from shots import SHOTS

ROOT = pathlib.Path(__file__).parent
FR = ROOT / "frames"
RAMP = {12, 16, 19, 25}  # Act 3 speed ramps (time remap + frame blending)
GRID_ZOOM_F = 12          # first 12 frames of shot 1
PULLBACK_F, FADE_F = 36, 12


def starts():
    s, out = 0, {}
    for sh in SHOTS:
        out[sh[0]] = s
        s += sh[1]
    return out


START = starts()
INFO = {sh[0]: sh for sh in SHOTS}


def load_layers(sid):
    c = cv2.imread(str(ROOT / f"stills/canvas/shot{sid:02d}.jpg"))
    d = cv2.imread(str(ROOT / f"stills/depth/shot{sid:02d}.png"), cv2.IMREAD_UNCHANGED).astype(np.float32) / 65535
    return R.Layers(c, d)


def finals():
    return {sid: cv2.imread(str(ROOT / f"stills/final/shot{sid:02d}.jpg")).astype(np.float32) / 255
            for sid in INFO if INFO[sid][3]}


def shot_frames(sid, L):
    """Yields (local index, raw BGR float frame) for one shot."""
    n, move = INFO[sid][1], INFO[sid][4]
    if sid == 1:
        body = n - GRID_ZOOM_F
        tiles = finals(); tiles[1] = R.render_shot_frame(L, move, 0, body, 1)
        g = Grid(tiles); F, z_end = g.fixed_point(1)
        for i in range(GRID_ZOOM_F):
            u = R.ease_io(i / (GRID_ZOOM_F - 1))
            z = math.exp(math.log(z_end) * u)
            yield i, g.render(z, F) * (0.55 + 0.45 * u)
        for i in range(body):
            yield GRID_ZOOM_F + i, R.render_shot_frame(L, move, i, body, 1)
    elif sid == 28:
        L27 = load_layers(27)
        tiles = finals(); tiles[27] = R.render_shot_frame(L27, INFO[27][4], INFO[27][1] - 1, INFO[27][1], 27)
        g = Grid(tiles); F, z_end = g.fixed_point(27)
        for i in range(n):
            u = R.ease_io(min(i / (PULLBACK_F - 1), 1.0))
            z = math.exp(math.log(z_end) * (1 - u))
            f = g.render(z, F)
            if i >= n - FADE_F:
                f = f * (1 - (i - (n - FADE_F) + 1) / FADE_F)
            yield i, f
    else:
        for i in range(n):
            yield i, R.render_shot_frame(L, move, i, n, sid, ramp=sid in RAMP)


def transitions(gf, frame, sid, i):
    """Post-grade transitions around cuts (each spans < 8 frames)."""
    n = INFO[sid][1]
    nxt = INFO.get(sid + 1)
    # incoming side of this shot's cut
    kind = INFO[sid][5]
    if kind == "light_leak" and i < 3:
        frame = R.light_leak(frame, 0.85 * (1 - i / 3.5), gf / 24, sid)
    if kind == "whip" and i < 3:
        frame = R.whip(frame, (1.0, 0.55, 0.2)[i], +1)
    # outgoing side (next shot's transition)
    if nxt and i >= n - 3:
        j = i - (n - 3)  # 0,1,2
        if nxt[5] == "light_leak":
            frame = R.light_leak(frame, 0.85 * (j + 1) / 3.5, gf / 24, sid)
        if nxt[5] == "whip":
            frame = R.whip(frame, (0.3, 0.65, 1.0)[j], -1)
    return frame


def pre_grade(frame, sid, i):
    n = INFO[sid][1]
    if sid == 3:  # screen glow fades out toward the match cut
        frame = frame * (1 - 0.5 * R.ease_io(max(0, i - (n - 14)) / 13))
    if sid == 4 and i < 6:  # warm light floods in through the jet door
        frame = frame * (1 + 0.5 * (1 - i / 6))
    return frame


def render(only=None):
    FR.mkdir(exist_ok=True)
    for sh in SHOTS:
        sid, n = sh[0], sh[1]
        if only and sid not in only:
            continue
        s0 = START[sid]
        if not only and all((FR / f"{s0 + i:04d}.jpg").exists() for i in range(n)):
            continue
        L = load_layers(sid) if sid != 28 else None
        for i, raw in shot_frames(sid, L):
            gf = s0 + i
            out = R.grade(pre_grade(raw, sid, i), gf, night=sh[2] == "Cn")
            out = transitions(gf, out, sid, i)
            cv2.imwrite(str(FR / f"{gf:04d}.jpg"), (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8),
                        [cv2.IMWRITE_JPEG_QUALITY, 96])
        print(f"shot {sid} rendered ({n} frames)", flush=True)


def encode():
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", str(FR / "%04d.jpg"), "-frames:v", "720",
           "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p", "-an",
           "-movflags", "+faststart", str(ROOT / "final.mp4")]
    subprocess.run(cmd, check=True)
    print("encoded final.mp4")


if __name__ == "__main__":
    only = None
    if "--shots" in sys.argv:
        only = {int(x) for x in sys.argv[sys.argv.index("--shots") + 1].split(",")}
    render(only)
    if len(list(FR.glob("*.jpg"))) >= 720:
        encode()
