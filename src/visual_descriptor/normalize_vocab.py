# src/visual_descriptor/normalize_vocab.py
from __future__ import annotations
from typing import Dict, Any, Optional, List

TOP_LENGTH_MAP: Dict[str, str] = {
    "cropped": "cropped", "crop": "cropped",
    "waist": "waist", "hip": "hip", "thigh": "thigh",
    "longline": "longline", "tunic": "tunic",
}
BOTTOM_LENGTH_MAP: Dict[str, str] = {
    "mini": "mini", "short": "short", "midi": "midi", "mid": "midi",
    "ankle": "ankle", "maxi": "maxi", "floor": "floor",
}

FABRIC_TYPE_MAP: Dict[str, str] = {
    "denim": "denim", "cotton": "cotton", "wool": "wool", "wool blend": "wool blend",
    "leather": "leather", "faux leather": "faux leather", "suede": "suede",
    "jersey": "jersey", "knit": "knit", "satin": "satin", "silk": "silk",
    "linen": "linen", "polyester": "polyester", "polyester blend": "polyester blend",
    "nylon": "nylon", "nylon blend": "nylon blend", "mesh": "mesh",
}
FABRIC_TEXTURE_MAP: Dict[str, str] = {
    "smooth": "smooth", "ribbed": "ribbed", "quilted": "quilted", "brushed": "brushed",
    "fuzzy": "fuzzy", "plush": "plush", "matte": "matte", "shiny": "shiny",
    "reflective": "shiny", "textured": "textured", "cable-knit": "cable-knit",
}
FABRIC_WEIGHT_MAP: Dict[str, str] = {
    "light": "light", "lightweight": "light", "medium": "medium",
    "midweight": "medium", "heavy": "heavy", "heavyweight": "heavy",
}

# Shades: at least 4 per primary
COLOR_MAP: Dict[str, str] = {
    # neutrals
    "off white": "ivory", "off-white": "ivory", "cream": "ivory",
    "ivory": "ivory", "white": "white", "black": "black",
    "gray": "gray", "grey": "gray", "charcoal": "gray",
    "tan": "tan", "beige": "beige", "camel": "camel",
    "brown": "brown", "chocolate": "brown",

    # purple family
    "purple": "purple", "violet": "violet", "plum": "plum", "eggplant": "eggplant",
    "lavender": "lavender", "lilac": "lilac", "amethyst": "amethyst",

    # red family
    "red": "red", "crimson": "crimson", "maroon": "maroon", "burgundy": "burgundy",

    # blue family
    "blue": "blue", "navy": "navy", "royal blue": "royal blue", "sky blue": "sky blue",

    # green family
    "green": "green", "olive": "olive", "forest": "forest", "mint": "mint",

    # yellow/orange
    "yellow": "yellow", "mustard": "mustard", "gold": "gold", "lemon": "lemon",
    "orange": "orange", "rust": "rust", "peach": "peach", "apricot": "apricot",
}

STITCHING_COLOR_MAP: Dict[str, str] = {
    "match": "matching", "matching": "matching",
    "white": "white", "black": "black",
    "contrast": "contrast", "contrast-light": "contrast-light", "light contrast": "contrast-light",
    "contrast dark": "contrast-dark", "contrast-dark": "contrast-dark",
}

SINGLE_PIECE_EXACT: set[str] = {
    "dress", "jumpsuit", "romper", "catsuit", "bodysuit",
    "coat", "trench coat", "jacket", "cardigan", "blazer",
    "sweater", "hoodie", "sweatshirt",
    "skirt", "shorts", "pants", "trousers", "jeans", "leggings",
}

def _norm(val: Optional[str], mapping: Dict[str, str]) -> Optional[str]:
    if not val:
        return val
    key = str(val).strip().lower()
    return mapping.get(key, val)

def _norm_list(values: List[str], mapping: Dict[str, str]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for v in values or []:
        nv = _norm(v, mapping) or v
        if isinstance(nv, str):
            nv = nv.strip()
        if nv and nv.lower() not in seen:
            out.append(nv)
            seen.add(nv.lower())
    return out

def _clean_placeholders(val: Any) -> Any:
    if isinstance(val, str):
        s = val.strip().lower()
        if s in {"string", "string|null", "null", "none", "unknown"}:
            return None
    return val

def normalize_record(r: Dict[str, Any]) -> Dict[str, Any]:
    # Normalize colors
    if isinstance(r.get("color_palette"), list):
        r["color_palette"] = _norm_list(r["color_palette"], COLOR_MAP)

    # Normalize fabric (and add satin inference)
    fab = dict(r.get("fabric") or {})
    # normalize to our controlled vocab where applicable
    fab["type"]    = _norm(fab.get("type"), FABRIC_TYPE_MAP)
    fab["texture"] = _norm(fab.get("texture"), FABRIC_TEXTURE_MAP)
    fab["weight"]  = _norm(fab.get("weight"), FABRIC_WEIGHT_MAP)
    # finish stays as-is; just ensure consistent casing when we inspect it
    r["fabric"] = fab

    # --- FIX: define ftype/finish/texture before using them; write back to r ---
    ftype   = (fab.get("type") or "").strip().lower()
    finish  = (fab.get("finish") or "").strip().lower()
    texture = (fab.get("texture") or "").strip().lower()

    # infer more specific textile when VLM returns generic buckets
    # shiny + smooth + generic → satin
    if (ftype in {"", "synthetic", "poly", "polyester", "unknown"}
        and finish == "shiny" and texture == "smooth"):
        fab["type"] = "satin"
        r["fabric"] = fab

    # Normalize stitching color
    cons = dict(r.get("construction") or {})
    cons["stitching_color"] = _norm(cons.get("stitching_color"), STITCHING_COLOR_MAP)
    for part in ("top", "bottom"):
        blk = cons.get(part)
        if isinstance(blk, dict):
            blk["stitching_color"] = _norm(blk.get("stitching_color"), STITCHING_COLOR_MAP)
            cons[part] = blk
    r["construction"] = cons

    # Normalize garment components
    gc = dict(r.get("garment_components") or {})
    gc["top_length"] = _norm(gc.get("top_length"), TOP_LENGTH_MAP)
    gc["bottom_length"] = _norm(gc.get("bottom_length"), BOTTOM_LENGTH_MAP)
    if isinstance(gc.get("layers"), list):
        gc["layers"] = [x for x in gc["layers"] if _clean_placeholders(x)]
    else:
        gc["layers"] = []
    # If single-piece garment type, we don't force null top/bottom (designer wants jacket/pants captured)
    r["garment_components"] = gc

    # Clean placeholders across record
    for key, value in list(r.items()):
        if isinstance(value, str):
            r[key] = _clean_placeholders(value)
        elif isinstance(value, list):
            cleaned = [_clean_placeholders(v) for v in value]
            r[key] = [c for c in cleaned if c]
        elif isinstance(value, dict):
            for k2, v2 in list(value.items()):
                value[k2] = _clean_placeholders(v2)

    return r