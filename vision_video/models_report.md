# Models report

**Total spend: $0.00.** Every upstream call is logged with its free justification in `logs/free_calls.log`, written
before the call is made. The client (`lib/omni.py`) refuses any model that isn't on its verified-free list.

## Discovery (OmniRoute 3.8.48, running locally at `localhost:20128`)

OmniRoute was installed in this session, with Hugging Face and Gemini connections added from the environment's keys.
Its `/v1/models` listing (129 models) exposed these image and video models:

| Provider | Model | Modality | OmniRoute free metadata |
|---|---|---|---|
| huggingface | FLUX.1-dev, FLUX.1-schnell, SDXL base 1.0 | image | `hasFree`: "Free Inference API" |
| pollinations | flux, zimage, klein (+ GPT Image models) | image | `hasFree`, keyless anonymous fallback (free tier lists text models only) |
| veoaifree-web | veo, seedance | video | `noAuth`, "Free video generation, 6 requests/hour" |
| gemini | text models only; no direct image route | – | free tier is text (1,500 req/day Gemini 2.5 Flash) |
| cloudflare-ai | chat models only; no image route in OmniRoute's registry | – | free 10,000 neurons/day |

## Candidates tested

Same prompt for each: cinematic infinity pool over a city skyline at golden hour, vertical, no text.

| Model | Route | Free basis | Result |
|---|---|---|---|
| Pollinations flux / zimage / klein | OmniRoute | keyless (no account to bill) | **401**: Pollinations now requires a key even for its free tier |
| HF FLUX.1-schnell, FLUX.1-dev, SDXL | OmniRoute | HF free account | **502**: OmniRoute calls the retired `api-inference.huggingface.co` (also blocked by this environment's network); `router.huggingface.co/hf-inference` returns 410 for these models |
| HF FLUX.1-schnell via nscale | direct, HF router | account is `isPro=false`, `canPay=false`, so it cannot be charged | **402**: this month's free credits are already used up |
| **Cloudflare SDXL base 1.0** | direct, Workers AI | Cloudflare's catalog lists **$0 per step** (beta) | ✅ native 768×1344, ~10 s, best candid photo look, no text artifacts |
| **Cloudflare SDXL Lightning** | direct, Workers AI | Cloudflare's catalog lists **$0 per step** (beta) | ✅ native 768×1344, ~4 s, more stylized, occasional faces |
| Cloudflare FLUX.1 schnell | direct, Workers AI | inside the free 10,000 neurons/day allocation (~58 per image) | ✅ sharpest and most detailed, but fixed 1024×1024 output (576 px wide after a 9:16 crop) |
| Leonardo Phoenix / Lucid Origin | – | priced per tile | not called |

Rate limits seen: none on Cloudflare during 75 generations (a few calls took 20 s).

## Choice

- **Primary: Cloudflare Workers AI `@cf/stabilityai/stable-diffusion-xl-base-1.0`**, 768×1344, 20 steps, with a
  negative prompt. Explicit $0 pricing, native vertical output, closest to the "real camera roll" references.
- **Fallback: Cloudflare Workers AI `@cf/bytedance/stable-diffusion-xl-lightning`**, also explicitly $0. It wasn't needed.
- Flux schnell was kept out because of its square-only output; its daily allocation is also capped locally at 5,000
  neurons in case it's ever enabled.

SDXL only reads the first 77 tokens of a prompt, so prompts put the subject first (see `style_bible.md`).

## Video models

**None used. Every shot is local 2.5D parallax.**
- `veoaifree-web` isn't an API: OmniRoute automates a third-party website's WordPress AJAX endpoint, under unclear
  terms and with a 6/hour limit. It was excluded rather than risk the terms or a flaky pipeline.
- No other free image-to-video model was exposed (Pollinations video needs a key; Cloudflare has no video models).

## Local, free, open-source tools

| Job | Tool |
|---|---|
| Upscaling | Real-ESRGAN general x4v3, official Qualcomm AI Hub ONNX export, onnxruntime CPU, 128 px tiles |
| Depth | Depth Anything V2 Small, `onnx-community/depth-anything-v2-small`, onnxruntime CPU (MiDaS v2.1 small kept as a fallback) |
| Motion, grade, transitions | NumPy + OpenCV |
| Encode and QA | ffmpeg / ffprobe 6.1 |

## Robustness

`lib/omni.py` has a per-call timeout (180 s), exponential backoff (4 → 120 s) on 408/429/5xx, stops immediately on
402, and caches every result under `cache/` by a hash of model, prompt, size, seed and steps, so nothing is generated
twice. `manifest.json` records every candidate, the pick and all derived files; re-running any script skips finished work.
