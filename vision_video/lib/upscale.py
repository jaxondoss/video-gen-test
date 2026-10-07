"""Real-ESRGAN general x4v3 (official Qualcomm AI Hub ONNX export, CPU), tiled 128px with overlap.
Crops to exact 9:16, upscales x4, then Lanczos to a 1.5x canvas (1620x2880) for camera moves."""
import glob, os, numpy as np, onnxruntime as ort
from PIL import Image

MODEL = glob.glob(os.path.expanduser("/home/user/vg_models/esrgan/**/*.onnx"), recursive=True)[0]
CANVAS = (1620, 2880)
_sess = None


def _session():
    global _sess
    if _sess is None:
        o = ort.SessionOptions(); o.intra_op_num_threads = os.cpu_count()
        _sess = ort.InferenceSession(MODEL, o)
    return _sess


def crop_916(im):
    w, h = im.size
    tw = round(h * 9 / 16)
    if tw <= w:
        x = (w - tw) // 2
        return im.crop((x, 0, x + tw, h))
    th = round(w * 16 / 9); y = (h - th) // 2
    return im.crop((0, y, w, y + th))


def esrgan_x4(im, tile=128, pad=12):
    s = _session(); name = s.get_inputs()[0].name
    a = np.asarray(im.convert("RGB"), dtype=np.float32) / 255.0
    H, W, _ = a.shape
    out = np.zeros((H * 4, W * 4, 3), np.float32)
    step = tile - 2 * pad
    ap = np.pad(a, ((pad, tile), (pad, tile), (0, 0)), mode="reflect")
    for y in range(0, H, step):
        for x in range(0, W, step):
            t = ap[y:y + tile, x:x + tile].transpose(2, 0, 1)[None]
            r = s.run(None, {name: t})[0][0].transpose(1, 2, 0)
            core = r[pad * 4:(pad + step) * 4, pad * 4:(pad + step) * 4]
            hh = min(step, H - y) * 4; ww = min(step, W - x) * 4
            out[y * 4:y * 4 + hh, x * 4:x * 4 + ww] = core[:hh, :ww]
    return Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8))


def to_canvas(src, dst):
    im = crop_916(Image.open(src).convert("RGB"))
    big = esrgan_x4(im)
    big.resize(CANVAS, Image.LANCZOS).save(dst, quality=95)
    return dst
