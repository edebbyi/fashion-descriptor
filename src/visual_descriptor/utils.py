# src/visual_descriptor/utils.py
from pathlib import Path
from PIL import Image
import hashlib
import numpy as np

def img_hash(path: Path) -> str:
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def is_image(p: Path) -> bool:
    return p.suffix.lower() in [".jpg", ".jpeg", ".png"]

def load_image_size(path: Path) -> tuple[int, int]:
    with Image.open(path) as im:
        return im.size

# ---- image helpers -----------------------------------------------------------

def _load_rgb_np(path: Path, target=256) -> np.ndarray:
    with Image.open(path) as im:
        im = im.convert("RGB")
        # keep aspect ratio, shortest side = target
        w, h = im.size
        scale = target / min(w, h)
        im = im.resize((int(w * scale), int(h * scale)))
        return np.asarray(im, dtype=np.uint8)

def _rgb_to_hsv(rgb: np.ndarray) -> np.ndarray:
    # rgb in [0,255] -> hsv with H in [0,360), S,V in [0,1]
    arr = rgb.astype(np.float32) / 255.0
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    maxc = np.max(arr, axis=-1)
    minc = np.min(arr, axis=-1)
    v = maxc
    s = np.where(maxc == 0, 0.0, (maxc - minc) / (maxc + 1e-6))
    rc = (maxc - r) / (maxc - minc + 1e-6)
    gc = (maxc - g) / (maxc - minc + 1e-6)
    bc = (maxc - b) / (maxc - minc + 1e-6)
    h = np.zeros_like(maxc)
    h = np.where((maxc == r), (bc - gc), h)
    h = np.where((maxc == g), 2.0 + (rc - bc), h)
    h = np.where((maxc == b), 4.0 + (gc - rc), h)
    h = (h / 6.0) % 1.0
    h = h * 360.0
    hsv = np.stack([h, s, v], axis=-1)
    return hsv

def _kmeans(x: np.ndarray, k=3, iters=6, seed=0) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(x), size=min(k, len(x)), replace=False)
    centers = x[idx].astype(np.float32)
    for _ in range(iters):
        d = ((x[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        labels = d.argmin(axis=1)
        for i in range(centers.shape[0]):
            pts = x[labels == i]
            if len(pts) > 0:
                centers[i] = pts.mean(axis=0)
    # sort by cluster size desc
    sizes = np.bincount(labels, minlength=centers.shape[0])
    order = np.argsort(-sizes)
    return centers[order], sizes[order]

def _purple_shade(h, s, v) -> str:
    # h: 0..360, s/v: 0..1
    if s < 0.25 and v > 0.8: return "lavender"
    if v < 0.35: return "plum"
    if 290 <= h <= 320 and s > 0.55: return "violet"
    if 300 < h <= 345 and s > 0.55: return "magenta"
    if 260 <= h <= 290 and s > 0.5 and 0.45 <= v <= 0.85: return "royal purple"
    return "amethyst"

def _shade_name(h, s, v) -> str:
    # families by hue
    if 260 <= h <= 345:  # purples/magentas
        return _purple_shade(h, s, v)
    if 200 <= h < 260:  # blues
        if v < .35: return "navy"
        return "blue"
    if 150 <= h < 200: return "teal"
    if 90 <= h < 150: return "green"
    if 60 <= h < 90: return "olive"
    if 40 <= h < 60: return "gold"
    if 20 <= h < 40: return "orange"
    if 5 <= h < 20: return "red"
    # neutrals by saturation/value
    if v > .9 and s < .1: return "white"
    if v < .2: return "black"
    if s < .2 and .2 < v < .9: return "gray"
    return "beige"

def dominant_color_shades(path: Path, k: int = 3) -> list[str]:
    rgb = _load_rgb_np(path, target=256)
    hsv = _rgb_to_hsv(rgb)
    flat = hsv.reshape(-1, 3)
    centers, sizes = _kmeans(flat, k=min(k, 5))
    shades = []
    for c in centers[:k]:
        name = _shade_name(float(c[0]), float(c[1]), float(c[2]))
        if name not in shades:
            shades.append(name)
    return shades[:k]

def has_vertical_bright_line_center(path: Path) -> bool:
    """Heuristic for an exposed front zipper: long bright thin vertical line near center."""
    arr = _load_rgb_np(path, target=256)
    gray = (0.299*arr[...,0] + 0.587*arr[...,1] + 0.114*arr[...,2]).astype(np.uint8)
    h, w = gray.shape[:2]
    cx0, cx1 = int(w*0.45), int(w*0.55)
    band = gray[:, cx0:cx1]
    # threshold "bright"
    bright = (band > 210).astype(np.uint8)
    # longest vertical run of bright pixels in any column
    longest = 0
    for x in range(bright.shape[1]):
        col = bright[:, x]
        # compute max consecutive run length
        run, best = 0, 0
        for px in col:
            if px:
                run += 1
                best = max(best, run)
            else:
                run = 0
        longest = max(longest, best)
    return longest > int(h * 0.35)  # ≥35% of height

def has_midriff_gap(path: Path) -> bool:
    """Detect a horizontal band with low primary-color coverage (crop-top + skirt)."""
    rgb = _load_rgb_np(path, target=256)
    hsv = _rgb_to_hsv(rgb)
    h, w = hsv.shape[:2]
    # get primary hue from overall median
    primary_h = np.median(hsv[...,0])
    mask = np.abs((hsv[...,0] - primary_h + 180) % 360 - 180) < 20  # within ±20°
    mask &= (hsv[...,1] > 0.25)  # saturated (garment)
    row_cov = mask.mean(axis=1)  # fraction per row
    # look for a trough in the middle third
    top, bot = int(h*0.30), int(h*0.75)
    mid = row_cov[top:bot]
    if len(mid) == 0: return False
    # trough if any 8+ consecutive rows < 0.25 while regions above and below > 0.55
    low = mid < 0.25
    run = 0
    trough = False
    for v in low:
        run = run + 1 if v else 0
        if run >= 8:
            trough = True
            break
    return bool(trough)
    
def estimate_warmth_from_palette(names: list[str]) -> str:
    warm = {"red","orange","gold","yellow","tan","beige","brown","cocoa","blush","pink","ivory"}
    cool = {"blue","navy","teal","cyan","green","olive","purple","violet","gray","white","black"}
    score = sum(1 for n in names if n in warm) - sum(1 for n in names if n in cool)
    if score >= 1: return "warm"
    if score <= -1: return "cool"
    return "neutral"
