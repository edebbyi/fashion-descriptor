# src/visual_descriptor/validators.py
from __future__ import annotations
from typing import Any, Dict, Optional, List, Tuple

try:
    from PIL import Image, ImageFilter, ImageStat, ImageOps, ImageChops
    _PIL_OK = True
except Exception:
    _PIL_OK = False

# ---------- image helpers ----------
def _avg_rgb(img: "Image.Image") -> Tuple[float, float, float]:
    stat = ImageStat.Stat(img)
    if len(stat.mean) >= 3:
        return tuple(stat.mean[:3])  # type: ignore
    m = stat.mean[0]
    return (m, m, m)

def _luma(rgb: Tuple[float, float, float]) -> float:
    r, g, b = rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def _estimate_stitching_color(img_path: str) -> Optional[str]:
    if not _PIL_OK:
        return None
    try:
        im = Image.open(img_path).convert("RGB")
    except Exception:
        return None

    base_l = _luma(_avg_rgb(im))
    edges = ImageOps.grayscale(im.filter(ImageFilter.FIND_EDGES))
    thresh = edges.point(lambda p: 255 if p > 80 else 0)
    if thresh.getbbox() is None:
        return None
    edge_rgb = Image.composite(im, Image.new("RGB", im.size, (0, 0, 0)), thresh)
    edge_l = _luma(_avg_rgb(edge_rgb))

    if edge_l - base_l > 30:
        return "contrast-light"
    if base_l - edge_l > 30:
        return "black" if edge_l < 40 else "contrast-dark"
    return "matching"

def _looks_like_curtain(img_path: str) -> bool:
    if not _PIL_OK:
        return False
    try:
        im = Image.open(img_path).convert("L").resize((256, 256))
    except Exception:
        return False
    edges = im.filter(ImageFilter.FIND_EDGES)
    cols = [sum(edges.getpixel((x, y)) for y in range(edges.height)) for x in range(edges.width)]
    mean = sum(cols) / len(cols)
    var = sum((c - mean) ** 2 for c in cols) / len(cols)
    cv = (var ** 0.5) / (mean + 1e-6)
    peaks = 0
    for i in range(1, len(cols) - 1):
        if cols[i] > cols[i - 1] and cols[i] > cols[i + 1] and cols[i] > mean * 1.25:
            peaks += 1
    return cv > 0.35 and peaks > 12

def _specularity_score(img_path: str) -> float:
    if not _PIL_OK:
        return 0.0
    try:
        im = Image.open(img_path).convert("RGB").resize((384, 384))
    except Exception:
        return 0.0

    gray = ImageOps.grayscale(im)
    edges = gray.filter(ImageFilter.FIND_EDGES)
    high_int = gray.point(lambda p: 255 if p > 220 else 0)
    high_edge = edges.point(lambda p: 255 if p > 40 else 0)

    # convert to binary to avoid mode errors
    high_int_bin = high_int.convert("1")
    high_edge_bin = high_edge.convert("1")

    both = ImageChops.logical_and(high_int_bin, high_edge_bin)
    hist = both.histogram()  # [black, white]
    white = hist[1] if len(hist) >= 2 else 0
    total = both.size[0] * both.size[1]
    return float(min(1.0, max(0.0, white / float(total + 1e-6))))

def _translucency_score(img_path: str) -> float:
    if not _PIL_OK:
        return 0.0
    try:
        im = Image.open(img_path).convert("L").resize((384, 384))
    except Exception:
        return 0.0
    mid = im.point(lambda p: 255 if 80 <= p <= 180 else 0)
    edges = im.filter(ImageFilter.FIND_EDGES)
    edges_mid = Image.composite(edges, Image.new("L", im.size, 0), mid)
    hist = edges_mid.histogram()
    score = sum(hist[40:]) / (sum(hist) + 1e-6)
    return float(max(0.0, min(1.0, score)))

# ---------- sanitizer ----------
def sanitize_record(rec: Dict[str, Any], image_path: Optional[str] = None) -> Dict[str, Any]:
    rec = dict(rec or {})
    rec.setdefault("garment", {})
    rec.setdefault("construction", {})
    rec.setdefault("garment_components", {})
    rec.setdefault("model", {})
    rec.setdefault("camera", {})
    rec.setdefault("environment_lighting", {})
    rec.setdefault("details", [])
    rec.setdefault("notes_uncertain", [])
    rec.setdefault("photo_metrics", {})

    # metrics
    if image_path:
        spec = _specularity_score(image_path)
        trans = _translucency_score(image_path)
        rec["photo_metrics"]["specularity"] = float(spec)
        rec["photo_metrics"]["translucency"] = float(trans)
    else:
        spec = float(rec.get("photo_metrics", {}).get("specularity", 0.0))

    # finish via specularity bands
    fab = rec.get("fabric") or {}
    finish = (fab.get("finish") or "").strip().lower() if isinstance(fab.get("finish"), str) else ""
    if not finish:
        fab["finish"] = "matte" if spec < 0.35 else ("semi-gloss" if spec <= 0.60 else "glossy")
    else:
        if spec < 0.35 and finish in {"gloss", "glossy", "semi-gloss"}:
            fab["finish"] = "matte"
        elif 0.35 <= spec <= 0.60 and finish in {"matte", "gloss", "glossy"}:
            fab["finish"] = "semi-gloss"
        elif spec > 0.60 and finish in {"matte", "semi-gloss"}:
            fab["finish"] = "glossy"
    rec["fabric"] = fab

    # stitching_color fallback
    if image_path:
        if not rec["construction"].get("stitching_color"):
            guess = _estimate_stitching_color(image_path)
            if guess:
                rec["construction"]["stitching_color"] = guess
        for part in ("top", "bottom"):
            blk = rec["construction"].get(part)
            if isinstance(blk, dict) and not blk.get("stitching_color"):
                guess = _estimate_stitching_color(image_path)
                if guess:
                    blk["stitching_color"] = guess
                    rec["construction"][part] = blk

    # background hint
    if image_path:
        env = rec.get("environment_lighting") or {}
        if not env.get("background") or env.get("background") == "plain studio sweep":
            if _looks_like_curtain(image_path):
                env["background"] = "white curtain / draped fabric"
        if not env.get("setup"):
            env["setup"] = "studio lighting"
        rec["environment_lighting"] = env

    # demote bomber unless rib knit cues exist
    top_style = (rec.get("garment") or {}).get("top_style")
    if isinstance(top_style, str) and top_style.strip().lower() == "bomber":
        dets = [str(d).lower() for d in (rec.get("details") or [])]
        ribby = any("ribbed hem" in d or "rib knit" in d or "ribbed cuffs" in d for d in dets)
        if not ribby:
            rec["garment"]["top_style"] = "jacket"

    # jacket inference: cropped + long-sleeve + zipper
    cons = rec.get("construction") or {}
    closure_global = str(cons.get("closure") or "").lower()
    top_blk = cons.get("top") if isinstance(cons.get("top"), dict) else {}
    closure_top = str((top_blk or {}).get("closure") or "").lower()
    has_zip = ("zip" in closure_global) or ("zip" in closure_top)
    sleeve = (rec.get("garment") or {}).get("top_sleeve")
    has_long_sleeve = isinstance(sleeve, str) and "long" in sleeve
    gc = rec.get("garment_components") or {}
    top_len = (gc.get("top_length") or "").lower() if isinstance(gc.get("top_length"), str) else ""
    is_cropped = top_len in {"cropped", "short"}
    is_hoodie = (rec.get("garment") or {}).get("top_style") == "hoodie"
    if has_zip and has_long_sleeve and is_cropped and not is_hoodie:
        rec["garment"]["top"] = rec["garment"].get("top") or "jacket"
        rec["garment"]["top_style"] = "crop jacket"

    # dress silhouette nudge
    if isinstance(rec.get("garment_type"), str) and "dress" in rec["garment_type"].lower():
        if gc.get("bottom_length") and gc.get("top_length"):
            gc["top_length"] = None
        sil = (rec.get("silhouette") or "").strip().lower()
        flowy = isinstance(rec.get("fit_and_drape"), str) and "flowy" in rec.get("fit_and_drape", "").lower()
        longish = (gc.get("bottom_length") or "").lower() in {"midi", "ankle", "maxi", "floor"}
        if flowy and longish and (not sil or sil == "straight"):
            rec["silhouette"] = "A-line"
        rec["garment_components"] = gc

    # camera multiview canonicalization
    pose = (rec.get("pose") or "").lower() if isinstance(rec.get("pose"), str) else ""
    cam = rec.get("camera") or {}
    view = (cam.get("view") or "").lower() if isinstance(cam.get("view"), str) else ""
    if "to camera" in pose and view == "back":
        cam["view"] = "front"
    if cam.get("multiview") == "yes":
        views = (cam.get("views") or "") if isinstance(cam.get("views"), str) else ""
        toks = [t.strip().lower() for t in views.split(",") if t.strip()]
        seen = []
        for t in ["front", "three-quarter", "side", "back"]:
            if t in toks and t not in seen:
                seen.append(t)
        if seen:
            cam["views"] = ", ".join(seen)
    rec["camera"] = cam

    # palette cap
    cp = [c for c in (rec.get("color_palette") or []) if c]
    cp_unique = []
    for c in cp:
        if c not in cp_unique:
            cp_unique.append(c)
    rec["color_palette"] = cp_unique[:2] if len(cp_unique) > 2 else cp_unique

    # footwear hint (leave as-is; optional)

    # layers hygiene
    layers = gc.get("layers")
    if isinstance(layers, list):
        drop = {"jacket", "pants", "trousers", "dress", "skirt", "shorts", "hoodie", "top", "bottom"}
        gc["layers"] = [x for x in layers if str(x).strip().lower() not in drop]
        rec["garment_components"] = gc

    # zipper vs double-breasted conflict
    if has_zip:
        dets = [str(d) for d in (rec.get("details") or [])]
        filtered = [d for d in dets if "double-breasted" not in d.lower()]
        if len(filtered) != len(dets):
            rec["details"] = filtered
            rec["notes_uncertain"].append("Removed 'double-breasted' due to zipper closure.")

    # bottom inference → skirt
    bottom_name = (rec.get("garment") or {}).get("bottom")
    bottom_len = (gc.get("bottom_length") or "").lower()
    seams_txt = ""
    if isinstance(cons.get("bottom"), dict):
        seams_txt = (cons.get("bottom", {}).get("seams") or "") + " " + (cons.get("bottom", {}).get("stitching") or "")
    seams_txt = seams_txt.lower()
    if (not bottom_name) and bottom_len in {"mini", "short"} and any(k in seams_txt for k in ["side seam", "visible seam", "contrast", "stitch"]):
        rec["garment"]["bottom"] = "skirt"
        rec["notes_uncertain"].append("Inferred bottom as 'skirt' from short length + seams/stitching cues.")

    # background default
    env = rec.get("environment_lighting") or {}
    if not env.get("background"):
        env["background"] = "plain studio sweep"
    rec["environment_lighting"] = env

    return rec

# --- append at end of validators.py ---
from typing import Dict, Any

def validate_record_colors(rec: Dict[str, Any]) -> None:
    """Lightweight sanity check for new colors/pattern fields."""
    if not isinstance(rec, dict):
        raise ValueError("record must be a dict")

    colors = rec.get("colors")
    if colors is not None and not isinstance(colors, dict):
        raise ValueError("colors must be a dict or omitted")

    if isinstance(colors, dict):
        base = colors.get("base")
        if base is not None and not isinstance(base, list):
            raise ValueError("colors.base must be a list")
        if isinstance(base, list):
            for sw in base:
                if not isinstance(sw, dict):
                    raise ValueError("each item in colors.base must be a dict")
                if "fraction" in sw and sw["fraction"] is not None and sw["fraction"] < 0:
                    raise ValueError("colors.base.fraction must be >= 0")

        accents = colors.get("accents")
        if accents is not None and not isinstance(accents, list):
            raise ValueError("colors.accents must be a list")
        if isinstance(accents, list):
            for a in accents:
                if not isinstance(a, dict):
                    raise ValueError("each item in colors.accents must be a dict")

    pattern = rec.get("pattern")
    if pattern is not None and not isinstance(pattern, dict):
        raise ValueError("pattern must be a dict or omitted")
