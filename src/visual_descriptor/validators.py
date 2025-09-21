# src/visual_descriptor/validators.py
from __future__ import annotations
from typing import Any, Dict, List, Optional

# Optional image heuristics
try:
    from PIL import Image, ImageFilter, ImageStat  # type: ignore
    import numpy as np  # type: ignore
    _PIL_OK = True
except Exception:
    _PIL_OK = False


# ---------- generic cleaning ----------

NUKES = {"string or null", "null", "none", "None", "", None}

def _clean(x: Any) -> Optional[str]:
    if x in NUKES:
        return None
    s = str(x).strip()
    if s.lower() in {"string or null", "null", "none"}:
        return None
    return s

def _drop_placeholders(d: Dict[str, Any]) -> None:
    for k, v in list(d.items()):
        if isinstance(v, dict):
            _drop_placeholders(v)
        elif isinstance(v, list):
            d[k] = [vv for vv in (_clean(x) for x in v) if vv]
        else:
            cv = _clean(v)
            d[k] = cv

def _dominant_color(palette: List[str]) -> Optional[str]:
    keep = [c for c in (palette or []) if c]
    if not keep: 
        return None
    if len(keep) == 1:
        return keep[0]
    # prefer chromatic over black/white when present
    for c in keep:
        if c.lower() not in {"black", "white"}:
            return c
    return keep[0]

def _ensure_shade_consistency(rec: Dict[str, Any]) -> None:
    pal = rec.get("color_palette") or []
    dom = _dominant_color(pal)
    if dom:
        rec["color_palette"] = [dom]


# ---------- construction & consistency ----------

def _resolve_construction(rec: Dict[str, Any]) -> None:
    cons = rec.get("construction") or {}
    top = cons.get("top") if isinstance(cons.get("top"), dict) else {}
    bottom = cons.get("bottom") if isinstance(cons.get("bottom"), dict) else {}

    # If global summary conflicts with section-level, keep section details
    for k in ("seams", "stitching", "hems", "closure"):
        s = cons.get(k)
        t = top.get(k) if isinstance(top, dict) else None
        b = bottom.get(k) if isinstance(bottom, dict) else None
        if any([t, b]) and s and s not in {t, b}:
            cons[k] = None

    # Remove vague closures (e.g., hidden button vs no button)
    for sect in (cons, top, bottom):
        if not isinstance(sect, dict):
            continue
        closure = (sect.get("closure") or "").lower()
        if "button" in closure and ("no button" in closure or "hidden" in closure):
            sect["closure"] = None

    rec["construction"] = cons

def _enforce_lengths(rec: Dict[str, Any]) -> None:
    gc = rec.get("garment_components") or {}
    details = rec.get("details") or []
    tl = gc.get("top_length")
    bl = gc.get("bottom_length")
    if tl:
        details = [d for d in details if not (("cropped" in d.lower()) and tl != "cropped")]
    if bl:
        details = [d for d in details if not (("midi" in d.lower()) and bl != "midi")]
    if details:
        rec["details"] = details

def _normalize_environment(rec: Dict[str, Any]) -> None:
    env = rec.get("environment_lighting") or {}
    if not env.get("setup"):
        env["setup"] = "studio lighting"
    if not env.get("mood"):
        env["mood"] = "neutral and clean"
    if not env.get("background"):
        env["background"] = "plain studio sweep"
    rec["environment_lighting"] = env


# ---------- image-driven heuristics ----------

def _estimate_finish(path: str) -> str:
    """Specular/edge heuristic -> matte / semi-gloss / glossy."""
    if not _PIL_OK:
        return "matte"
    im = Image.open(path).convert("RGB")
    g = im.convert("L")
    # very bright pixels as crude specular measure
    arr = np.asarray(g, dtype=np.uint8)
    p90 = np.percentile(arr, 90)
    bright = (arr > max(220, p90 + 15)).mean()
    edges = g.filter(ImageFilter.FIND_EDGES)
    e_mean = ImageStat.Stat(edges).mean[0] / 255.0
    score = 0.6 * float(bright) + 0.4 * float(e_mean)
    if score < 0.03:
        return "matte"
    if score < 0.09:
        return "semi-gloss"
    return "glossy"

def _detect_multiview(path: str) -> Dict[str, str]:
    """Detect side-by-side front/back layouts."""
    if not _PIL_OK:
        return {"multiview": "no"}
    im = Image.open(path).convert("L")
    w, h = im.size
    if w < h * 1.4:  # likely not a collage
        return {"multiview": "no"}
    left = im.crop((0, 0, w // 2, h)).filter(ImageFilter.FIND_EDGES)
    right = im.crop((w // 2, 0, w, h)).filter(ImageFilter.FIND_EDGES)
    l_score = ImageStat.Stat(left).sum[0] / (left.size[0] * left.size[1])
    r_score = ImageStat.Stat(right).sum[0] / (right.size[0] * right.size[1])
    if l_score > 2.0 and r_score > 2.0:
        return {"multiview": "yes", "views": "front, back", "view": None}
    return {"multiview": "no"}

def apply_image_heuristics(rec: Dict[str, Any], image_path: str) -> Dict[str, Any]:
    rec.setdefault("fabric", {})
    if not rec["fabric"].get("finish"):
        rec["fabric"]["finish"] = _estimate_finish(image_path)

    mv = _detect_multiview(image_path)
    rec.setdefault("camera", {})
    if mv.get("multiview") == "yes":
        rec["camera"]["multiview"] = "yes"
        rec["camera"]["views"] = mv.get("views", "front, back")
        rec["camera"]["view"] = None
        rec.setdefault("model", {})
        rec["model"].setdefault("framing", "full-body")
    else:
        rec["camera"]["multiview"] = "no"
        rec["camera"].setdefault("view", "front")

    rec.setdefault("environment_lighting", {})
    rec["environment_lighting"].setdefault("background", "plain studio sweep")
    return rec


# ---------- main entry ----------

def sanitize_record(rec: Dict[str, Any], image_path: Optional[str] = None) -> Dict[str, Any]:
    _drop_placeholders(rec)
    _ensure_shade_consistency(rec)
    _resolve_construction(rec)
    _enforce_lengths(rec)
    _normalize_environment(rec)
    if image_path:
        rec = apply_image_heuristics(rec, image_path)
    return rec