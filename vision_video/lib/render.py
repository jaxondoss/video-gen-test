"""2.5D parallax renderer, procedural transitions and the film-wide grade. All local (NumPy + OpenCV)."""
import math
import cv2
import numpy as np

W, H = 1080, 1920
WORK = (1350, 2400)          # working canvas (1.25x output), downsampled from the 1620x2880 Real-ESRGAN canvas
BASE = W / WORK[0]           # 0.8: work px -> output px at zoom 1
OVERSCAN = 1.15              # base zoom so layer parallax and roll never reveal edges


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def ease_io(t):  # ease-in-out cubic
    t = min(max(t, 0.0), 1.0)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_ramp(t):  # speed ramp: fast attack, long slow tail (time remap)
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3.2


# move -> (zoom0, zoom1, tx0, tx1, ty0, ty1, roll0, roll1); translations in output px, roll in degrees
MOVES = {
    "push_in":         (1.00, 1.10, 0, 0, 6, -6, 0, 0),
    "push_in_slow":    (1.00, 1.06, 0, 0, 0, -4, 0, 0),
    "push_in_slowest": (1.00, 1.045, 0, 0, 3, -3, 0, 0),
    "pull_out":        (1.10, 1.00, 0, 0, -6, 6, 0, 0),
    "drift":           (1.03, 1.04, -18, 18, 6, -6, 0, 0),
    "slide_left":      (1.04, 1.04, 40, -40, 0, 0, 0, 0),
    "slide_right":     (1.04, 1.04, -40, 40, 0, 0, 0, 0),
    "orbit":           (1.04, 1.07, 34, -34, 0, 0, -0.8, 0.8),
    "sweep":           (1.05, 1.08, 48, -48, 0, 0, 0.6, -0.4),
}


class Layers:
    """Continuous 2.5D parallax: every pixel's zoom, pan and roll is scaled by its depth (near pixels move more).
    Solved by backward mapping (output pixel -> source pixel, two fixed-point iterations on depth), so the
    result has no holes and no layer seams; occlusion edges stretch the background slightly instead of
    tearing. The disparity map is max-filtered so foreground edges stay crisp."""

    K_FAR, K_NEAR = 0.72, 1.40

    def __init__(self, canvas_bgr, disparity):
        img = cv2.resize(canvas_bgr, WORK, interpolation=cv2.INTER_AREA)
        d = cv2.resize(disparity, WORK, interpolation=cv2.INTER_LINEAR).astype(np.float32)
        d = cv2.dilate(d, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
        self.img = img.astype(np.float32) / 255.0
        self.d = cv2.GaussianBlur(d, (0, 0), 2.0)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        self.qx, self.qy = xx - W / 2, yy - H / 2

    def _inverse(self, k, zoom, tx, ty, roll):
        s = BASE * OVERSCAN * np.exp(k * math.log(zoom))
        a = -np.deg2rad(roll) * k
        vx, vy = self.qx - tx * k, self.qy - ty * k
        c, sn = np.cos(a), np.sin(a)
        px = (c * vx - sn * vy) / s + WORK[0] / 2
        py = (sn * vx + c * vy) / s + WORK[1] / 2
        return px.astype(np.float32), py.astype(np.float32)

    def render(self, zoom, tx, ty, roll):
        k = np.float32(1.0)
        for _ in range(2):
            px, py = self._inverse(k, zoom, tx, ty, roll)
            dd = cv2.remap(self.d, px, py, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            k = self.K_FAR + (self.K_NEAR - self.K_FAR) * dd
        px, py = self._inverse(k, zoom, tx, ty, roll)
        return cv2.remap(self.img, px, py, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


def camera(move, p, t_sec, seed):
    z0, z1, x0, x1, y0, y1, r0, r1 = MOVES[move]
    zoom = math.exp(math.log(z0) + (math.log(z1) - math.log(z0)) * p)
    tx, ty, roll = x0 + (x1 - x0) * p, y0 + (y1 - y0) * p, r0 + (r1 - r0) * p
    # candid handheld sway: 1-2 px, low frequency
    ph = seed * 1.7
    tx += 1.4 * math.sin(2 * math.pi * 0.37 * t_sec + ph) + 0.6 * math.sin(2 * math.pi * 0.83 * t_sec + 2 * ph)
    ty += 1.1 * math.sin(2 * math.pi * 0.29 * t_sec + 3 * ph) + 0.5 * math.sin(2 * math.pi * 0.71 * t_sec + ph)
    roll += 0.08 * math.sin(2 * math.pi * 0.21 * t_sec + ph)
    return zoom, tx, ty, roll


def render_shot_frame(layers, move, i, n, seed, ramp=False, extra_tx=0.0):
    """Frame i of an n-frame shot, with sub-frame motion blur scaled to camera speed."""
    curve = ease_ramp if ramp else ease_io

    def params(fi):
        p = curve(fi / max(n - 1, 1))
        z, tx, ty, r = camera(move, p, fi / 24.0, seed)
        return z, tx + extra_tx, ty, r

    a, b = params(i - 0.5), params(i + 0.5)
    speed = abs(b[1] - a[1]) + abs(b[2] - a[2]) + abs(math.log(b[0] / a[0])) * 1400 + abs(b[3] - a[3]) * 18
    n_sub = 1 if speed < 1.2 else (3 if speed < 5 else 5)
    if n_sub == 1:
        return layers.render(*params(i))
    acc = np.zeros((H, W, 3), np.float32)
    for k in range(n_sub):
        acc += layers.render(*params(i - 0.5 + (k + 0.5) / n_sub))
    return acc / n_sub


# ---------- transitions ----------

def light_leak(frame, strength, t_sec, seed):
    """Animated warm gradient blob, screen-blended."""
    yy, xx = np.mgrid[0:H // 4, 0:W // 4].astype(np.float32)
    cx = (0.15 + 0.7 * ((t_sec * 1.9 + seed * 0.31) % 1.0)) * W / 4
    cy = (0.25 + 0.15 * math.sin(seed + t_sec * 3)) * H / 4
    g = np.exp(-(((xx - cx) / (W / 4 * 0.55)) ** 2 + ((yy - cy) / (H / 4 * 0.45)) ** 2))
    g = cv2.resize(g, (W, H), interpolation=cv2.INTER_CUBIC)[..., None]
    leak = g * np.array([0.25, 0.55, 1.0], np.float32) * strength  # BGR: warm orange
    return 1 - (1 - frame) * (1 - np.clip(leak, 0, 1))


def whip(frame, amount, direction=1):
    """Whip-pan: horizontal shift plus directional motion blur. amount in [0,1]."""
    if amount <= 0:
        return frame
    shift = direction * amount * 140
    M = np.float32([[1, 0, shift], [0, 1, 0]])
    f = cv2.warpAffine(frame, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    k = max(3, int(amount * 90) | 1)
    kernel = np.zeros((1, k), np.float32); kernel[0, :] = 1.0 / k
    return cv2.filter2D(f, -1, kernel, borderType=cv2.BORDER_REFLECT)


# ---------- grade + finishing ----------

#            frame: (temp, sat, contrast, lift, exposure)
GRADE_KEYS = [(0, (-0.60, 0.60, 1.00, 0.030, 0.82)),
              (110, (-0.55, 0.64, 1.00, 0.030, 0.84)),
              (124, (-0.20, 0.85, 1.03, 0.015, 1.00)),
              (287, (0.15, 0.97, 1.06, 0.010, 1.00)),
              (300, (0.22, 1.05, 1.08, 0.000, 1.00)),
              (598, (0.24, 1.05, 1.08, 0.000, 1.00)),
              (612, (0.30, 0.96, 1.00, 0.020, 1.02)),
              (719, (0.32, 0.95, 1.00, 0.020, 1.02))]


def grade_params(f):
    for (fa, a), (fb, b) in zip(GRADE_KEYS, GRADE_KEYS[1:]):
        if fa <= f <= fb:
            t = (f - fa) / (fb - fa)
            return tuple(x + (y - x) * t for x, y in zip(a, b))
    return GRADE_KEYS[-1][1]


_vig = None


def _vignette():
    global _vig
    if _vig is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / math.sqrt(2)
        _vig = (1 - 0.32 * r ** 2.2)[..., None].astype(np.float32)
    return _vig


def grade(img, f, night=False, rng=None):
    """img: HxWx3 float32 BGR in [0,1]. Continuous cold-to-warm grade plus grain, halation, bloom, vignette."""
    temp, sat, con, lift, expo = grade_params(f)
    if night:
        temp, sat = temp - 0.22, sat * 0.95
    x = img * expo
    b, g, r = x[..., 0], x[..., 1], x[..., 2]
    x = np.stack([b * (1 - 0.12 * temp), g * (1 + 0.015 * temp), r * (1 + 0.10 * temp)], -1)
    l = (0.114 * x[..., 0] + 0.587 * x[..., 1] + 0.299 * x[..., 2])[..., None]
    x = l + (x - l) * sat
    x = lift + x * (1 - lift)
    x = 0.5 + (x - 0.5) * con
    l = np.clip(0.114 * x[..., 0] + 0.587 * x[..., 1] + 0.299 * x[..., 2], 0, 1)[..., None]
    x = x + (1 - l) ** 2 * np.array([0.030, 0.012, -0.010], np.float32)          # teal shadows
    x = x + l ** 2 * np.array([-0.012, 0.016, 0.040], np.float32) * max(temp, 0) * 2  # amber highlights
    # halation + bloom (computed at quarter res)
    small = cv2.resize(np.clip(x, 0, 1), (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    ls = (0.114 * small[..., 0] + 0.587 * small[..., 1] + 0.299 * small[..., 2])
    hl = np.clip((ls - 0.72) / 0.28, 0, 1)
    hal = cv2.GaussianBlur(hl, (0, 0), 5)[..., None] * np.array([0.10, 0.30, 0.95], np.float32)
    blo = cv2.GaussianBlur(small * hl[..., None], (0, 0), 10)
    glow = cv2.resize(hal * 0.16 + blo * 0.10, (W, H), interpolation=cv2.INTER_CUBIC)
    x = x + glow
    x = x * _vignette()
    # 35mm grain: clumped luminance noise
    rng = rng or np.random.default_rng(f)
    n = rng.standard_normal((H // 2, W // 2)).astype(np.float32)
    n = cv2.resize(n, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
    x = x + n * 0.018 * (0.6 + 0.4 * (1 - l))
    return np.clip(x, 0, 1)
