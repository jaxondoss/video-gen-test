"""Depth Anything V2 Small (onnx-community export) on CPU via onnxruntime. Returns disparity in [0,1], 1 = near."""
import os, numpy as np, onnxruntime as ort, cv2

MODEL = "/home/user/vg_models/da2/onnx/model.onnx"
_s = None


def disparity(rgb, short=518):
    """rgb: HxWx3 uint8. Output: HxW float32 in [0,1], smoothed, near = 1."""
    global _s
    if _s is None:
        o = ort.SessionOptions(); o.intra_op_num_threads = os.cpu_count()
        _s = ort.InferenceSession(MODEL, o)
    H, W = rgb.shape[:2]
    w = short; h = int(round(H / W * short / 14)) * 14
    x = cv2.resize(rgb, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    out = _s.run(None, {_s.get_inputs()[0].name: x.transpose(2, 0, 1)[None].astype(np.float32)})[0]
    d = out.reshape(out.shape[-2], out.shape[-1])
    lo, hi = np.percentile(d, 1), np.percentile(d, 99.5)
    d = np.clip((d - lo) / max(hi - lo, 1e-6), 0, 1).astype(np.float32)
    d = cv2.resize(d, (W, H), interpolation=cv2.INTER_CUBIC)
    return cv2.bilateralFilter(d, 9, 0.1, 9)
