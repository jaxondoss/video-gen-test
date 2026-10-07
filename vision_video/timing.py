"""Phase 5: beat_map.json, cuts.csv and markers.edl (CMX3600) from the shot list. 24 fps, 120 BPM = 12 frames/beat."""
import csv, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent / "lib"))
from shots import SHOTS

ROOT = pathlib.Path(__file__).parent
FPS, BPM = 24, 120
FPB = FPS * 60 // BPM  # 12


def tc(f):  # SMPTE timecode, 24 fps non-drop
    return f"{f // (FPS * 3600):02d}:{f // (FPS * 60) % 60:02d}:{f // FPS % 60:02d}:{f % FPS:02d}"


cuts, f = [], 0
for sid, n, phase, subj, move, trans in SHOTS:
    cuts.append({"shot": sid, "frame": f, "time_s": round(f / FPS, 3), "timecode": tc(f), "frames": n,
                 "end_frame": f + n - 1, "transition_in": trans, "camera_move": move, "phase": phase,
                 "on_beat": f % FPB == 0, "beat_index": f / FPB})
    f += n
assert f == 720 and all(c["on_beat"] for c in cuts)
beats = [{"beat": b, "frame": b * FPB, "time_s": round(b * FPB / FPS, 3), "bar": b // 4 + 1, "beat_in_bar": b % 4 + 1,
          "downbeat": b % 4 == 0} for b in range(720 // FPB)]
acts = [{"act": 1, "name": "Effort", "frames": [0, 119]}, {"act": 2, "name": "The door opens", "frames": [120, 287]},
        {"act": 3, "name": "Peak", "frames": [288, 599]}, {"act": 4, "name": "Peace and resolve", "frames": [600, 719]}]
(ROOT / "beat_map.json").write_text(json.dumps({"fps": FPS, "bpm": BPM, "frames_per_beat": FPB, "total_frames": 720,
    "duration_s": 30.0, "acts": acts, "cuts": cuts, "beat_grid": beats,
    "notes": "Every cut lands on a beat. Transitions straddle the cut by at most 3 frames each side. "
             "Shot 28 holds still for its last 24 frames and fades to black over the final 12."}, indent=1))
with open(ROOT / "cuts.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["shot", "start_frame", "end_frame", "frames", "start_time_s", "timecode", "beat_index", "transition_in", "camera_move", "phase"])
    for c in cuts:
        w.writerow([c["shot"], c["frame"], c["end_frame"], c["frames"], c["time_s"], c["timecode"], int(c["beat_index"]), c["transition_in"], c["camera_move"], c["phase"]])
lines = ["TITLE: VISION BOARD MARKERS", "FCM: NON-DROP FRAME", ""]
for i, c in enumerate(cuts, 1):
    rec_out = tc(c["end_frame"] + 1)
    lines += [f"{i:03d}  AX       V     C        {tc(c['frame'])} {rec_out} {tc(c['frame'])} {rec_out}",
              f"* FROM CLIP NAME: final.mp4", f"* LOC: {tc(c['frame'])} YELLOW  SHOT {c['shot']} {c['transition_in'].upper()}", ""]
(ROOT / "markers.edl").write_text("\n".join(lines))
print("cuts", len(cuts), "beats", len(beats))
