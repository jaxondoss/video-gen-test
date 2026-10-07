"""Pinterest-style masonry grid of all stills (no text, no UI). Used by shot 1 (zoom in), shot 28 (pull back)
and the contact sheet. Shots 1 and 27 sit in the center column as exact 9:16 tiles, so zooming into either
tile fills the 1080x1920 frame exactly."""
import cv2, numpy as np

W, H, M, G, COLS = 1080, 1920, 10, 10, 5
CW = (W - 2 * M - (COLS - 1) * G) / COLS  # 204 px
COLUMNS = [[2, 5, 8, 11, 14], [4, 7, 10, 13, 16, 19], [9, 1, 27, 23],
           [6, 12, 15, 18, 21, 24], [3, 17, 20, 22, 25, 26]]
FIXED = {1, 27}
RATIOS = [16 / 9, 4 / 3, 3 / 2, 5 / 4, 16 / 9, 4 / 3]  # h/w, cycled for variety


def layout():
    """Returns {shot: (x, y, w, h)} in 1080x1920 grid coordinates."""
    rects = {}
    for ci, col in enumerate(COLUMNS):
        hs = [CW * 16 / 9 if s in FIXED else CW * RATIOS[(s + ci) % len(RATIOS)] for s in col]
        avail = H - 2 * M - (len(col) - 1) * G
        fixed = sum(h for s, h in zip(col, hs) if s in FIXED)
        flex = sum(h for s, h in zip(col, hs) if s not in FIXED)
        k = (avail - fixed) / flex
        y = M
        for s, h in zip(col, hs):
            h = h if s in FIXED else h * k
            rects[s] = (M + ci * (CW + G), y, CW, h)
            y += h + G
    return rects


def crop_to(img, aspect_hw):
    h, w = img.shape[:2]
    if h / w > aspect_hw:
        nh = int(round(w * aspect_hw)); y = (h - nh) // 2
        return img[y:y + nh]
    nw = int(round(h / aspect_hw)); x = (w - nw) // 2
    return img[:, x:x + nw]


class Grid:
    def __init__(self, tiles):
        """tiles: {shot: HxWx3 float32 image (any size, ideally 1080x1920)}"""
        self.rects = layout()
        self.src = {}
        for s, (x, y, w, h) in self.rects.items():
            im = crop_to(tiles[s], h / w)
            self.src[s] = [im, cv2.resize(im, (int(w * 2), int(h * 2)), interpolation=cv2.INTER_AREA)]

    def fixed_point(self, shot):
        """Zoom fixed point F so that at z_end the shot's tile exactly fills the frame."""
        x, y, w, h = self.rects[shot]
        z_end = W / w
        T = np.array([x + w / 2, y + h / 2]); C = np.array([W / 2, H / 2])
        return (C - z_end * T) / (1 - z_end), z_end

    def render(self, z=1.0, F=(0.0, 0.0), bg=0.06):
        out = np.full((H, W, 3), bg, np.float32)
        F = np.asarray(F, np.float64)
        for s, (x, y, w, h) in self.rects.items():
            x0, y0 = F + z * (np.array([x, y]) - F)
            ww, hh = w * z, h * z
            if x0 > W or y0 > H or x0 + ww < 0 or y0 + hh < 0:
                continue
            im = self.src[s][1] if ww <= self.src[s][1].shape[1] else self.src[s][0]
            sx, sy = ww / im.shape[1], hh / im.shape[0]
            Mx = np.float32([[sx, 0, x0], [0, sy, y0]])
            warped = cv2.warpAffine(im, Mx, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(-1, -1, -1))
            mask = warped[..., :1] >= 0
            out = np.where(mask, warped, out)
        return out
