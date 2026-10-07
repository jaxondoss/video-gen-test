# Style bible: "Dream life" vision board

**Look:** candid quiet luxury, "someone's real camera roll", not rap-video flash. Taken from `references/`:
iPhone-candid framing, back-of-head and over-the-shoulder POVs (01 convertible, 05 chess), hazy pastel or golden
sunsets through floor-to-ceiling glass (04 trading desk), bright turquoise sea seen from a white yacht deck (02), and
the dark, monochrome "work" mood of 03 for Act 1 only.

## Master prefix (reused in every prompt)

> Candid luxury lifestyle photograph, shot on a full-frame camera with a 35mm lens, natural light, slightly imperfect
> framing like a real camera roll, shallow depth of field, subtle film grain, cinematic color, photorealistic,
> vertical 9:16 composition, high detail. Faceless: subject seen only from behind, as a silhouette, or as hands and
> wrist POV. Unbranded, no logos, no text.

SDXL reads only the first 77 tokens of a prompt, so each prompt is built as **subject → phase color → compact
prefix** (`candid camera-roll photo, 35mm lens, natural light, shallow depth of field, subtle film grain, cinematic,
photorealistic, seen from behind, faceless`). The full prefix above is the design intent the compact form encodes.

## Negative prompt (every image)

`text, letters, words, logos, brand names, watermark, captions, license plates, signage, UI elements` plus
`face, eyes, looking at camera, portrait, money, cash, cartoon, illustration, painting, 3d render, deformed hands,
extra fingers, blurry, lowres`.

## Recurring protagonist

Young man, athletic build, dark curly hair, dark clothing. Only ever from behind, in silhouette, or as hands/wrist.

## Color phases (prompt wording + final grade)

| Phase | Shots | Prompt wording | Grade target |
|---|---|---|---|
| A, effort | 1–3 | cold blue and teal, desaturated, dark, 3am, laptop glow | temp −0.35, sat 0.70, lifted blacks |
| B, transition | 4–9 | cool blue turning warm, warm light spilling in | temp ramps −0.15 → +0.15, sat 0.9 |
| C, arrival | 10–26 | warm golden hour, amber and teal, rich contrast (night shots: deep blue and amber city lights) | temp +0.25, sat 1.05, teal shadows |
| D, peace | 27–28 | soft warm golden light, calm, still | temp +0.3, sat 0.95, soft contrast |

## Finishing (one look for the whole film)

Light 35mm grain, soft halation on highlights, gentle vignette, slight bloom, subtle motion blur on camera moves.
