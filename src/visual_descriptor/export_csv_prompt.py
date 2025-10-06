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
            out.append(f"{st_col} {stitch}")
        elif st_col.lower() == "matching":
            out.append(f"matching {stitch}")
        else:
            out.append(stitch)
    if seams: out.append(seams)
    if hems: out.append(hems)
    if closure: out.append(closure)
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
            out.append(f"{st_col} {stitch}")
        elif st_col.lower() == "matching":
            out.append(f"matching {stitch}")
        else:
            out.append(stitch)
    if seams: out.append(seams)
    if hems: out.append(hems)
    if closure: out.append(closure)
    return out

def _fabric_phrase(fab: Dict[str, Any]) -> str:
    """Comprehensive fabric description."""
    if not isinstance(fab, dict): return ""
    parts = []
    if fab.get("type"):
        parts.append(fab["type"])
    if fab.get("texture"):
        parts.append(fab["texture"])
    if fab.get("weight"):
        parts.append(f"{fab['weight']}-weight")
    if fab.get("finish"):
        parts.append(fab["finish"])
    return ", ".join(parts)

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
    """Extract details from structured or string list."""
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
    return ", ".join(bits) if bits else ""

def prompt_line(rec: Dict[str, Any]) -> str:
    """
    Generate comprehensive prompt text with fabric, construction, and photography details.
    Format: garment | fabric | colors | construction | photography
    """
    # Work directly with the dict, don't convert to Record
    if isinstance(rec, Record):
        rec = rec.model_dump(mode="python", exclude_none=False)
    else:
        # Make a copy to avoid mutating the original
        rec = dict(rec)

    # 1. Garment core
    summary = _garment_summary(rec)
    
    # 2. Fabric
    fabric_str = _fabric_phrase(rec.get("fabric") or {})
    
    # 3. Silhouette & Fit
    silhouette = rec.get("silhouette", "")
    if silhouette:
        silhouette = str(silhouette).strip()
    fit = rec.get("fit_and_drape", "")
    if fit:
        fit = str(fit).strip()
    
    # 4. Colors
    color_primary = rec.get("color_primary", "")
    if color_primary:
        color_primary = str(color_primary).strip()
    color_secondary = rec.get("color_secondary", "")
    if color_secondary:
        color_secondary = str(color_secondary).strip()
    
    # Fallback to color_palette if top-level colors not set
    if not color_primary:
        palette = [c for c in (rec.get("color_palette") or []) if c]
        color_primary = palette[0] if len(palette) > 0 else ""
        if not color_secondary:
            color_secondary = palette[1] if len(palette) > 1 else ""
    
    color_parts = []
    if color_primary:
        if color_secondary:
            color_parts.append(f"{color_primary} with {color_secondary}")
        else:
            color_parts.append(color_primary)
    
    # Pattern detection
    colors_obj = rec.get("colors") or {}
    pattern = colors_obj.get("pattern") if isinstance(colors_obj, dict) else None
    if isinstance(pattern, dict) and pattern.get("type"):
        ptype = str(pattern.get("type", "")).replace("_", " ")
        fg = pattern.get("foreground", "")
        if fg:
            fg = str(fg)
        if ptype and fg:
            color_parts.append(f"{fg} {ptype}")
        elif ptype:
            color_parts.append(ptype)
    
    color_str = ", ".join(color_parts)
    
    # 5. Details
    details = _details_phrase(rec)
    
    # 6. Construction
    cons = rec.get("construction") or {}
    top_phrase = _piece_cons(cons.get("top") if isinstance(cons.get("top"), dict) else {})
    bot_phrase = _piece_cons(cons.get("bottom") if isinstance(cons.get("bottom"), dict) else {})
    glob_phrase = _global_cons(cons)
    
    cons_parts = []
    if top_phrase: 
        cons_parts.append(f"top: {', '.join(top_phrase)}")
    if bot_phrase: 
        cons_parts.append(f"bottom: {', '.join(bot_phrase)}")
    if not (top_phrase or bot_phrase) and glob_phrase:
        cons_parts.extend(glob_phrase)
    
    cons_str = " | ".join(cons_parts)
    
    # 7. Layers
    gc = rec.get("garment_components") or {}
    layers = gc.get("layers") or []
    layers = layers if isinstance(layers, list) else [layers]
    layers_str = ", ".join([str(x) for x in layers if x])
    
    # 8. Footwear
    fw = rec.get("footwear") or {}
    footwear_parts = []
    if fw.get("type"):
        if fw.get("color"):
            footwear_parts.append(f"{fw['color']} {fw['type']}")
        else:
            footwear_parts.append(str(fw['type']))
    footwear_str = ", ".join(footwear_parts)
    
    # 9. Photography
    model = rec.get("model") or {}
    cam = rec.get("camera") or {}
    env = rec.get("environment_lighting") or {}
    
    photo_parts = []
    
    # Pose
    pose = rec.get("pose")
    if pose:
        photo_parts.append(str(pose))
    
    # Model
    if model.get("framing"):
        photo_parts.append(str(model['framing']))
    if model.get("expression"):
        photo_parts.append(f"{model['expression']} expression")
    if model.get("gaze"):
        photo_parts.append(f"gaze {model['gaze']}")
    
    # Camera
    if cam.get("multiview") == "yes" and cam.get("views"):
        photo_parts.append(f"multi-view: {cam['views']}")
    elif cam.get("view"):
        photo_parts.append(f"{cam['view']} view")
    if cam.get("angle"):
        photo_parts.append(f"{cam['angle']} angle")
    
    # Lighting
    if env.get("setup"):
        photo_parts.append(str(env['setup']))
    if env.get("mood"):
        photo_parts.append(f"{env['mood']} mood")
    if env.get("background"):
        photo_parts.append(f"bg: {env['background']}")
    if rec.get("photo_style"):
        photo_parts.append(str(rec['photo_style']))
    
    photo_str = ", ".join(photo_parts)
    
    # Build Final Prompt
    blocks = []
    
    # Block 1: Garment + Fabric + Silhouette/Fit
    garment_block = [summary]
    if fabric_str:
        garment_block.append(fabric_str)
    if silhouette:
        garment_block.append(f"{silhouette} silhouette")
    if fit:
        garment_block.append(fit)
    blocks.append(" — ".join(garment_block))
    
    # Block 2: Colors + Pattern
    if color_str:
        blocks.append(f"Colors: {color_str}")
    
    # Block 3: Details
    if details:
        blocks.append(f"Details: {details}")
    
    # Block 4: Construction
    if cons_str:
        blocks.append(f"Construction: {cons_str}")
    
    # Block 5: Layers + Footwear
    extras = []
    if layers_str:
        extras.append(f"layers: {layers_str}")
    if footwear_str:
        extras.append(f"footwear: {footwear_str}")
    if extras:
        blocks.append(" | ".join(extras))
    
    # Block 6: Photography
    if photo_str:
        blocks.append(f"Photo: {photo_str}")
    
    return " || ".join(blocks)

# Export csv
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

        # Use top-level color_primary/color_secondary if available
        if not d.get("color_primary"):
            palette = [c for c in (d.get("color_palette") or []) if c]
            d["color_primary"] = palette[0] if len(palette) > 0 else None
        if not d.get("color_secondary"):
            palette = [c for c in (d.get("color_palette") or []) if c]
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