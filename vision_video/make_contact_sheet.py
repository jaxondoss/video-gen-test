"""contact_sheet.jpg: all 28 shots numbered (shot 28 = the grid composite, graded warm like the film's ending)."""
import pathlib, sys, cv2, numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent / "lib"))
from grid import Grid
from sheets import grid as sheet
import render as R

ROOT = pathlib.Path(__file__).parent
tiles = {s: cv2.imread(str(ROOT / f"stills/final/shot{s:02d}.jpg")).astype(np.float32) / 255 for s in range(1, 28)}
g28 = R.grade(Grid(tiles).render(1.0, (0, 0)), 700)
cv2.imwrite(str(ROOT / "stills/final/shot28_grid.jpg"), (g28 * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 94])
items = [(s, str(ROOT / f"stills/final/shot{s:02d}.jpg")) for s in range(1, 28)] + [(28, str(ROOT / "stills/final/shot28_grid.jpg"))]
sheet(items, str(ROOT / "contact_sheet.jpg"), cols=7, tw=220)
print("contact_sheet.jpg")
