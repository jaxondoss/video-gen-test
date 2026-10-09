# Dream life vision board: 30 s, 9:16, no text, no audio

A 720-frame (24 fps, 1080×1920, H.264, yuv420p, no audio) "laptop lifestyle" film built for $0.00: free
Cloudflare Workers AI stills, then upscaling, depth, parallax motion, transitions and grade, all done locally.

| File | What it is |
|---|---|
| `final.mp4` | the film (no audio track; add your music) |
| `contact_sheet.jpg` | all 28 shots, numbered |
| `preview_contact_strip.jpg` | one frame every 2 s of the final film |
| `beat_map.json`, `cuts.csv`, `markers.edl` | cut frames, timecodes, transitions, and the 120 BPM beat grid (every cut is on a beat) |
| `manifest.json` | every shot's prompt, negative, candidates (seed, model), pick and derived files |
| `models_report.md` | which models were tested, which are free and why, which were chosen |
| `style_bible.md` | the look, prompt prefix, negative prompt and color phases |
| `stills/final/` | the 27 picked stills at 1080×1920, plus the shot-28 grid |

## Requirements

Python 3.10+ with `numpy opencv-python-headless pillow requests onnxruntime huggingface_hub`, plus `ffmpeg`.

Environment variables: `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` (Workers AI permission), and network access
to `api.cloudflare.com`.

Local models in `/home/user/vg_models/` (paths are set at the top of `lib/upscale.py` and `lib/depth.py`):
- **Depth Anything V2 Small:** `onnx-community/depth-anything-v2-small`, file `onnx/model.onnx`, saved to `vg_models/da2/`.
- **Real-ESRGAN general x4v3:** the ONNX zip from Qualcomm AI Hub (URL in `models_report.md`), unzipped into `vg_models/esrgan/`.

## Pipeline

```bash
python3 gen_stills.py             # Phase 3: 2 candidates per shot (cached; finished shots are skipped)
python3 prepare.py                # pick -> Real-ESRGAN 1620x2880 canvas -> depth map -> 1080x1920 still
python3 make_contact_sheet.py     # contact_sheet.jpg
python3 timing.py                 # beat_map.json, cuts.csv, markers.edl
python3 build_video.py            # Phases 4 and 6: frames/ -> final.mp4 (existing frames are skipped)
python3 qa.py                     # ffprobe checks + preview_contact_strip.jpg
```

## Regenerating a single shot

1. Optionally edit the shot's subject text in `lib/shots.py`.
2. Generate new candidates with new seeds: `python3 gen_stills.py 13 --seeds=101,202`.
   They land in `stills/raw/shot13_s101.png` and so on, and are recorded in `manifest.json`.
3. Set the new pick in `PICKS` in `prepare.py` (e.g. `13: 101`), then run `python3 prepare.py 13`.
   That rebuilds the canvas, depth map and still for that shot only.
4. Re-render that shot's frames and re-encode: `python3 build_video.py --shots 13`.
   Shots next to a whip or light-leak transition share 3 frames across the cut, so re-render the neighbors too
   (e.g. `--shots 12,13,14`). Then run `python3 qa.py`.

If you change shot 1 or 27, also re-render shot 28 (and shot 1), because their grids show every still.

## Safety rails

- `lib/omni.py` refuses any model not on its verified-free list, and logs model + free justification to
  `logs/free_calls.log` before each call. It stops immediately on HTTP 402, and caches by prompt hash under `cache/`.
- Every prompt carries the negative `text, letters, words, logos, brand names, watermark, captions, license plates,
  signage, UI elements` plus face and money terms. Picks were checked by eye at full resolution for text, logos and
  faces; 6 shots were regenerated for that reason.

## Notes

- `final.mp4` in the repo is encoded at **CRF 17** (89 MB). The CRF 16 encode from the spec is 104 MB, over GitHub's
  100 MB file limit, and Git LFS uploads are blocked from the cloud session. To make a CRF 16 master, set `-crf` to 16 in
  `build_video.py` and run the pipeline (frames are rebuilt locally; they aren't stored in git).
- No AI video model was used: every shot is local 2.5D parallax (see `models_report.md`).
- The parallax is a continuous depth warp, not hard layers. Hard layers ghosted silhouettes in testing, and the
  backward warp has no holes, so no gap inpainting is needed.
