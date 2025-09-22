from __future__ import annotations
from typing import Dict, Any, List
from .schema import Record

# Clothing first, lighting last, prompt_text included
CSV_FIELDS: List[str] = [
    # Garment summary block
    "garment_type", "silhouette",
    "garment.top_style", "garment.top", "garment.top_sleeve",
    "garment.bottom",
    "garment_components.top_length", "garment_components.bottom_length",
    "garment_components.layers",
    # Construction
    "construction.top.seams", "construction.top.stitching", "construction.top.stitching_color",
    "construction.top.hems", "construction.top.closure",
    "construction.bottom.seams", "construction.bottom.stitching", "construction.bottom.stitching_color",
    "construction.bottom.hems", "construction.bottom.closure",
    "construction.seams", "construction.stitching", "construction.stitching_color",
    "construction.hems", "construction.closure",
    # Fabric & fit
    "fabric.type", "fabric.texture", "fabric.finish", "fabric.weight",
    "fit_and_drape",
    # Footwear
    "footwear.type", "footwear.color",
    # Colors
    "color_primary", "color_secondary",
    # Model / Camera
    "model.expression", "model.framing", "model.gaze",
    "camera.angle", "camera.view", "camera.views", "camera.multiview",
    # Photo meta
    "photo_style", "pose",
    "photo_metrics.specularity", "photo_metrics.translucency",
    # Environment lighting LAST
    "environment_lighting.background", "environment_lighting.mood", "environment_lighting.setup",
    # IDs + prompt
    "image_id", "prompt_text",
]

def _uniq(seq: List[str]) -> List[str]:
    out, seen = [], set()
    for s in seq:
        s2 = (s or "").strip()
        if not s2: continue
        low = s2.lower()
        if low in seen: continue
        out.append(s2); seen.add(low)
    return out

def _join(words: List[str]) -> str:
    return " ".join([w for w in words if w]).strip()

def _comma_join(parts: List[str]) -> str:
    parts = [p.strip() for p in parts if p and str(p).strip()]
    return ", ".join(parts)

def _piece_cons(piece: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    if not isinstance(piece, dict): return out
    seams = (piece.get("seams") or "").strip()
    stitch = (piece.get("stitching") or "").strip()
    st_col = (piece.get("stitching_color") or "").strip()
    hems = (piece.get("hems") or "").strip()
    closure = (piece.get("closure") or "").strip()
    if stitch:
        if st_col and st_col.lower() != "matching":
            out.append(f"{st_col} stitching ({stitch})")
        elif st_col.lower() == "matching":
            out.append(f"matching stitching ({stitch})")
        else:
            out.append(stitch)
    if seams: out.append(seams)
    if hems: out.append(f"hems: {hems}")
    if closure: out.append(f"closure: {closure}")
    return out

def _global_cons(cons: Dict[str, Any]) -> List[str]:
    if not isinstance(cons, dict): return []
    seams = (cons.get("seams") or "").strip()
    stitch = (cons.get("stitching") or "").strip()
    st_col = (cons.get("stitching_color") or "").strip()
    hems = (cons.get("hems") or "").strip()
    closure = (cons.get("closure") or "").strip()
    out: List[str] = []
    if stitch:
        if st_col and st_col.lower() != "matching":
            out.append(f"{st_col} stitching ({stitch})")
        elif st_col.lower() == "matching":
            out.append(f"matching stitching ({stitch})")
        else:
            out.append(stitch)
    if seams: out.append(seams)
    if hems: out.append(f"hems: {hems}")
    if closure: out.append(f"closure: {closure}")
    return out

def _fabric_phrase(fab: Dict[str, Any]) -> str:
    if not isinstance(fab, dict): return ""
    ftype = (fab.get("type") or "").strip()
    text = (fab.get("texture") or "").strip()
    weight = (fab.get("weight") or "").strip()
    finish = (fab.get("finish") or "").strip()
    bits: List[str] = []
    if ftype: bits.append(ftype)
    if text: bits.append(text)
    if weight: bits.append(f"{weight} weight")
    if finish: bits.append(f"{finish} finish")
    return _comma_join(bits)

def _garment_summary(rec: Dict[str, Any]) -> str:
    g = rec.get("garment") or {}
    gc = rec.get("garment_components") or {}
    garment_type = (rec.get("garment_type") or "").strip()
    silhouette = (rec.get("silhouette") or "").strip()
    top_style = (g.get("top_style") or "").strip()
    top = (g.get("top") or "").strip()
    bottom = (g.get("bottom") or "").strip()
    sleeve = (g.get("top_sleeve") or "").strip()
    top_len = (gc.get("top_length") or "").strip()
    bot_len = (gc.get("bottom_length") or "").strip()

    if garment_type and garment_type.lower() in {"dress", "jumpsuit", "romper", "catsuit"}:
        core = garment_type
        if sleeve: core = _join([sleeve, core])
        if bot_len: core = _join([core, bot_len])
        if silhouette: core = f"{core} ({silhouette})"
        return core

    upper = _join(_uniq([top_style or top, sleeve, top_len]))
    lower = _join(_uniq([bottom, bot_len]))
    parts = [p for p in [upper, lower] if p]
    if not parts:
        return _join([garment_type, silhouette]) or "garment look"
    if silhouette:
        return f"{' and '.join(parts)} ({silhouette})"
    return " and ".join(parts)

def _details_phrase(rec: Dict[str, Any]) -> str:
    """
    Prefer structured details if present; otherwise use the string list.
    """
    dets = rec.get("details_struct")
    if not dets:
        dets = rec.get("details")
    if not dets:
        return ""
    bits: List[str] = []
    for d in (dets if isinstance(dets, list) else []):
        if isinstance(d, dict):
            color = (d.get("color") or "").strip()
            label = (d.get("label") or d.get("kind") or "").strip()
            if color and label: bits.append(f"{color} {label}")
            elif color:         bits.append(color)
            elif label:         bits.append(label)
        elif isinstance(d, str):
            if d.strip(): bits.append(d.strip())
    return f"details: {', '.join(bits)}" if bits else ""

def prompt_line(rec: Dict[str, Any]) -> str:
    r = Record(**rec) if not isinstance(rec, Record) else rec
    rec = r.model_dump(mode="python", exclude_none=False)

    summary = _garment_summary(rec)
    fabric = _fabric_phrase(rec.get("fabric") or {})

    cons = rec.get("construction") or {}
    top_phrase = _piece_cons(cons.get("top") if isinstance(cons.get("top"), dict) else {})
    bot_phrase = _piece_cons(cons.get("bottom") if isinstance(cons.get("bottom"), dict) else {})
    glob_phrase = _global_cons(cons)
    cons_bits: List[str] = []
    if top_phrase: cons_bits.append(f"top: {_comma_join(top_phrase)}")
    if bot_phrase: cons_bits.append(f"bottom: {_comma_join(bot_phrase)}")
    if not (top_phrase or bot_phrase):
        cons_bits = glob_phrase

    colors = [c for c in (rec.get("color_palette") or []) if c]
    color_str = ""
    if colors:
        color_str = colors[0] if len(colors) == 1 else f"{colors[0]} + {colors[1]}"

    det_str = _details_phrase(rec)

    gc = rec.get("garment_components") or {}
    layers = gc.get("layers") or []
    layers = layers if isinstance(layers, list) else [layers]
    layers_str = _comma_join([x for x in layers if x])

    fw = rec.get("footwear") or {}
    footwear_str = (fw.get("type") or "").strip() or None
    if footwear_str and fw.get("color"):
        footwear_str = f"{footwear_str} ({fw.get('color')})"

    model = rec.get("model") or {}
    cam = rec.get("camera") or {}
    env = rec.get("environment_lighting") or {}

    blocks: List[str] = []
    head = summary
    if fabric:    head = f"{head} — {fabric}"
    if color_str: head = f"{head} — {color_str}"
    if det_str:   head = f"{head} — {det_str}"
    blocks.append(head)

    mid: List[str] = []
    if layers_str:   mid.append(f"layers: {layers_str}")
    if cons_bits:    mid.append(_comma_join(cons_bits))
    if footwear_str: mid.append(f"footwear: {footwear_str}")
    if mid: blocks.append("; ".join(mid))

    tail: List[str] = []
    if rec.get("pose"):           tail.append(rec["pose"])
    if model.get("framing"):      tail.append(model["framing"])
    if model.get("expression"):   tail.append(f"expression: {model['expression']}")
    if model.get("gaze"):         tail.append(f"gaze: {model['gaze']}")
    if cam.get("multiview") == "yes" and cam.get("views"):
        tail.append(f"views: {cam['views']}")
    elif cam.get("view"):
        tail.append(cam["view"])
    if env.get("setup"):          tail.append(env["setup"])
    if env.get("mood"):           tail.append(env["mood"])
    if env.get("background"):     tail.append(env["background"])
    if rec.get("photo_style"):    tail.append(rec["photo_style"])
    if tail: blocks.append(", ".join(tail))

    return "  ".join([b for b in blocks if b]).strip()

class CSVExporter:
    def __init__(self):
        self.rows: List[Dict[str, Any]] = []

    def _dig(self, d: Dict[str, Any], dotted: str) -> Any:
        cur = d
        for part in dotted.split("."):
            if not isinstance(cur, dict): return None
            cur = cur.get(part)
        return cur

    def add_flat(self, d: Dict[str, Any]) -> None:
        d = dict(d)

        # Backfill primary/secondary from descriptive palette
        palette = [c for c in (d.get("color_palette") or []) if c]
        if not d.get("color_primary"):
            d["color_primary"] = palette[0] if len(palette) > 0 else None
        if not d.get("color_secondary"):
            d["color_secondary"] = palette[1] if len(palette) > 1 else None

        d["prompt_text"] = prompt_line(d)

        # Reorder into CSV_FIELDS
        ordered: Dict[str, Any] = {}
        for key in CSV_FIELDS:
            if "." in key:
                ordered[key] = self._dig(d, key)
            else:
                ordered[key] = d.get(key)
        self.rows.append(ordered)

    def export(self) -> List[Dict[str, Any]]:
        return self.rows
