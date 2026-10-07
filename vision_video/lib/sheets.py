"""Contact sheets: numbered thumbnail grids."""
from PIL import Image, ImageDraw, ImageFont


def _font(size):
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


def grid(items, out, cols=7, tw=180, label=True, bg=(18, 18, 18)):
    """items: list of (label, path). Labels are for review sheets only, never used in the video."""
    th = round(tw * 16 / 9)
    rows = (len(items) + cols - 1) // cols
    pad = 6
    sheet = Image.new("RGB", (cols * (tw + pad) + pad, rows * (th + pad) + pad), bg)
    d = ImageDraw.Draw(sheet); f = _font(max(14, tw // 9))
    for i, (lab, p) in enumerate(items):
        im = Image.open(p).convert("RGB")
        w, h = im.size; cw = round(h * 9 / 16)
        if cw < w:
            im = im.crop(((w - cw) // 2, 0, (w - cw) // 2 + cw, h))
        im = im.resize((tw, th), Image.LANCZOS)
        x = pad + (i % cols) * (tw + pad); y = pad + (i // cols) * (th + pad)
        sheet.paste(im, (x, y))
        if label:
            d.rectangle((x, y, x + tw // 3, y + tw // 6), fill=(0, 0, 0))
            d.text((x + 4, y + 2), str(lab), fill=(255, 255, 255), font=f)
    sheet.save(out, quality=90)
    return out
