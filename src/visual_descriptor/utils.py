from __future__ import annotations
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import hashlib

# Optional image/array libs
try:
    from PIL import Image, ImageFilter, ImageStat
    _PIL_OK = True
except Exception:
    _PIL_OK = False
    Image = None  # type: ignore

try:
    import numpy as np
    _NP_OK = True
except Exception:
    _NP_OK = False


# Basic utilities

def img_hash(p: Path) -> str:
    """Stable content hash (first 16 hex chars of SHA-256)."""
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]

def is_image(p: Path) -> bool:
    """Check if a file is a valid image based on extension and system file filtering."""
    # Filter out system and hidden files
    if p.name.startswith('._') or p.name.startswith('.DS_Store') or p.name.startswith('Thumbs.db'):
        return False
    return p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}

def load_image_size(path: Path) -> tuple[int, int]:
    if not _PIL_OK:
        return (0, 0)
    with Image.open(path) as im:
        return im.size


# Image processing helpers

def _load_rgb_np(path: Path, target: int = 256) -> "np.ndarray":
    """Load image as RGB numpy array, resize to target on shortest side."""
    if not (_PIL_OK and _NP_OK):
        raise RuntimeError("NumPy/Pillow not available for _load_rgb_np")
    with Image.open(path) as im:
        im = im.convert("RGB")
        # Keep aspect ratio: shortest side -> target
        w, h = im.size
        scale = float(target) / float(min(w, h)) if min(w, h) > 0 else 1.0
        im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))))
        return np.asarray(im, dtype=np.uint8)

def _rgb_to_hsv(rgb: "np.ndarray") -> "np.ndarray":
    """Convert RGB [0,255] to HSV: H in [0,360), S,V in [0,1]."""
    if not _NP_OK:
        raise RuntimeError("NumPy not available for _rgb_to_hsv")
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

def _kmeans(x: "np.ndarray", k: int = 3, iters: int = 6, seed: int = 0) -> tuple["np.ndarray", "np.ndarray"]:
    """Simple k-means clustering. Returns (centers, sizes) sorted by cluster size."""
    if not _NP_OK:
        raise RuntimeError("NumPy not available for _kmeans")
    rng = np.random.default_rng(seed)
    k_eff = max(1, min(k, len(x)))
    idx = rng.choice(len(x), size=k_eff, replace=False)
    centers = x[idx].astype(np.float32)
    for _ in range(max(1, iters)):
        d = ((x[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        labels = d.argmin(axis=1)
        for i in range(centers.shape[0]):
            pts = x[labels == i]
            if len(pts) > 0:
                centers[i] = pts.mean(axis=0)
    sizes = np.bincount(labels, minlength=centers.shape[0])
    order = np.argsort(-sizes)
    return centers[order], sizes[order]

# Color naming logic

def _purple_shade(h: float, s: float, v: float) -> str:
    """Distinguish purple shades by HSV values."""
    if s < 0.25 and v > 0.8: return "lavender"
    if v < 0.35: return "plum"
    if 290 <= h <= 320 and s > 0.55: return "violet"
    if 300 < h <= 345 and s > 0.55: return "magenta"
    if 260 <= h <= 290 and s > 0.5 and 0.45 <= v <= 0.85: return "royal purple"
    return "amethyst"

def _shade_name(h: float, s: float, v: float) -> str:
    """Map HSV to human-readable color name."""
    # Color families by hue
    if 260 <= h <= 345:  # purples/magentas
        return _purple_shade(h, s, v)
    if 200 <= h < 260:  # blues
        return "navy" if v < 0.35 else "blue"
    if 150 <= h < 200:
        return "teal"
    if 90 <= h < 150:
        return "green"
    if 60 <= h < 90:
        return "olive"
    if 40 <= h < 60:
        return "gold"
    if 20 <= h < 40:
        return "orange"
    if 5 <= h < 20:
        return "red"
    # Neutrals by saturation/value
    if v > 0.9 and s < 0.1:
        return "white"
    if v < 0.2:
        return "black"
    if s < 0.2 and 0.2 < v < 0.9:
        return "gray"
    return "beige"

def dominant_color_shades(path: Path, k: int = 3) -> list[str]:
    """Return up to k shade names ('violet', 'plum', 'navy')."""
    if not (_PIL_OK and _NP_OK):
        return []
    rgb = _load_rgb_np(path, target=256)
    hsv = _rgb_to_hsv(rgb)
    flat = hsv.reshape(-1, 3)
    centers, sizes = _kmeans(flat, k=min(k, 5))
    shades: list[str] = []
    for c in centers[:k]:
        name = _shade_name(float(c[0]), float(c[1]), float(c[2]))
        if name not in shades:
            shades.append(name)
    return shades[:k]

def has_vertical_bright_line_center(path: Path) -> bool:
    """Check for exposed front zipper: long bright vertical line near center."""
    if not (_PIL_OK and _NP_OK):
        return False
    arr = _load_rgb_np(path, target=256)
    gray = (0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2])
    gray = gray.astype("uint8")
    h, w = gray.shape[:2]
    cx0, cx1 = int(w * 0.45), int(w * 0.55)
    band = gray[:, cx0:cx1]
    bright = (band > 210).astype("uint8")
    # Longest vertical run of bright pixels in any column
    longest = 0
    for x in range(bright.shape[1]):
        col = bright[:, x]
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
    """Detect horizontal band with low color coverage (crop-top + skirt gap)."""
    if not (_PIL_OK and _NP_OK):
        return False
    rgb = _load_rgb_np(path, target=256)
    hsv = _rgb_to_hsv(rgb)
    H = hsv[..., 0]
    S = hsv[..., 1]
    h, w = hsv.shape[:2]
    primary_h = float(np.median(H))
    mask = (np.abs((H - primary_h + 180) % 360 - 180) < 20) & (S > 0.25)
    row_cov = mask.mean(axis=1)  # Fraction per row
    # Middle band
    top, bot = int(h * 0.30), int(h * 0.75)
    mid = row_cov[top:bot] if bot > top else row_cov
    if len(mid) == 0:
        return False
    # Gap detected if 8+ consecutive rows < 0.25 coverage
    low = mid < 0.25
    run = 0
    for v in low:
        run = run + 1 if v else 0
        if run >= 8:
            return True
    return False

def estimate_warmth_from_palette(names: list[str]) -> str:
    """Score palette as warm/cool/neutral based on color names."""
    warm = {"red", "orange", "gold", "yellow", "tan", "beige", "brown", "cocoa", "blush", "pink", "ivory"}
    cool = {"blue", "navy", "teal", "cyan", "green", "olive", "purple", "violet", "gray", "white", "black"}
    score = sum(1 for n in names if n in warm) - sum(1 for n in names if n in cool)
    if score >= 1:
        return "warm"
    if score <= -1:
        return "cool"
    return "neutral"


# Multiview detection

def _detect_multiview(path: str) -> Dict[str, Optional[str]]:
    """Detect side-by-side front/back layouts using edge density and gutter detection."""
    if not _PIL_OK:
        return {"multiview": "no", "views": None, "view": None}

    im = Image.open(path).convert("L")
    w, h = im.size

    # Wide images are more likely to be collages
    wide = w >= int(1.5 * h)

    # Split halves and compute edge density
    left = im.crop((0, 0, w // 2, h)).filter(ImageFilter.FIND_EDGES)
    right = im.crop((w // 2, 0, w, h)).filter(ImageFilter.FIND_EDGES)
    l_score = ImageStat.Stat(left).sum[0] / max(1, (left.size[0] * left.size[1]))
    r_score = ImageStat.Stat(right).sum[0] / max(1, (right.size[0] * right.size[1]))

    # Look for vertical gutter between panels (very dark or very bright)
    midband = im.crop((w // 2 - max(2, w // 200), 0, w // 2 + max(2, w // 200), h))
    mid_mean = ImageStat.Stat(midband).mean[0]
    gutter = (mid_mean < 20) or (mid_mean > 235)

    # Check if both halves have similar edge density
    both_present = l_score > 1.5 and r_score > 1.5
    ratio = (l_score / r_score) if r_score else 0.0
    balanced = 0.6 <= ratio <= 1.7

    if (wide and both_present and balanced) or (gutter and both_present):
        return {"multiview": "yes", "views": "front, back", "view": None}

    return {"multiview": "no", "views": None, "view": None}