from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List

from .multipass_merge import merge_pass
from .normalize_vocab import normalize_record
from .schema import Record
from .captioners import StubCaptioner, Blip2Captioner, OpenAIVLM as CaptionersOpenAIVLM, GeminiVLM as CaptionersGeminiVLM
from .utils import img_hash, is_image

try:
    from .validators import validate_record_colors
except Exception:
    def validate_record_colors(_rec): 
        return


# Adapt VLM color output to schema format
def _adapt_colors_from_vlm(rec: Dict[str, Any]) -> None:
    """
    Mutates rec in place.
    Maps nested colors/pattern to schema fields:
      - color_primary, color_secondary
      - details: compact strings like 'black polka dots', 'brown buttons'
    """
    colors = rec.get("colors")
    if isinstance(colors, dict):
        prim = colors.get("primary")
        sec = colors.get("secondary")
        if isinstance(prim, str) and prim.strip():
            rec["color_primary"] = prim.strip()
        if isinstance(sec, str) and sec.strip():
            rec["color_secondary"] = sec.strip()

        det_bits: List[str] = []
        accents = colors.get("accents") or []
        if isinstance(accents, list):
            for a in accents:
                if not isinstance(a, dict):
                    continue
                role = (a.get("role") or "").strip()
                col = (a.get("name") or a.get("color") or "").strip()
                if role and col:
                    det_bits.append(f"{col} {role}")

        pattern = colors.get("pattern") if "pattern" in colors else rec.get("pattern")
        if isinstance(pattern, dict):
            ptype = (pattern.get("type") or "").strip()

            def _name(node: Any) -> str:
                if isinstance(node, dict):
                    return (node.get("name") or node.get("color") or "").strip()
                if isinstance(node, str):
                    return node.strip()
                return ""

            fg = _name(pattern.get("foreground"))
            if ptype in {"polka_dot", "polka dots", "polka-dot"} and fg:
                det_bits.append(f"{fg} polka dots")
            elif ptype in {"stripe", "striped"} and fg:
                det_bits.append(f"{fg} stripes")
            elif ptype in {"plaid", "check"}:
                det_bits.append(f"{(fg + ' ') if fg else ''}{ptype}".strip())
            elif ptype == "colorblock":
                det_bits.append("colorblock")

        existing = rec.get("details")
        if not (isinstance(existing, list) and all(isinstance(x, str) for x in existing)):
            existing = []
        # De-dup preserving order
        seen = set()
        out = []
        for s in existing + det_bits:
            s2 = (s or "").strip()
            if not s2:
                continue
            low = s2.lower()
            if low in seen:
                continue
            seen.add(low)
            out.append(s2)
        if out:
            rec["details"] = out
        else:
            rec.pop("details", None)


def _coerce_str(value: Any) -> str | None:
    """Return value if it's a non-empty string; otherwise None."""
    if isinstance(value, str):
        s = value.strip()
        return s if s else None
    return None  

# Ensure string fields are actually strings (not booleans/etc)
def _sanitize_types(rec: Dict[str, Any]) -> None:
    g = rec.get("garment")
    if not isinstance(g, dict):
        rec["garment"] = {}
        g = rec["garment"]

    # Known string fields in garment block
    for key in ("top_style", "top", "top_sleeve", "bottom", "silhouette", "garment_type"):
        if key in rec:
            rec[key] = _coerce_str(rec.get(key))
        if key in g:
            g[key] = _coerce_str(g.get(key))

    cons = rec.get("construction")
    if isinstance(cons, dict):
        for key in ("seams", "stitching", "stitching_color", "hems", "closure"):
            if key in cons:
                cons[key] = _coerce_str(cons.get(key))
        for piece_key in ("top", "bottom"):
            piece = cons.get(piece_key)
            if isinstance(piece, dict):
                for key in ("seams", "stitching", "stitching_color", "hems", "closure"):
                    if key in piece:
                        piece[key] = _coerce_str(piece.get(key))

    # Details must be list[str] or absent
    dets = rec.get("details")
    if isinstance(dets, list):
        only_str = [d for d in dets if isinstance(d, str)]
        if only_str:
            rec["details"] = only_str
        else:
            rec.pop("details", None)
    elif dets is not None:
        rec.pop("details", None)


class Engine:
    def __init__(self, model: str = "stub", normalize: bool = True):
        self.normalize = normalize
        
        # Choose backend: gemini > openai > blip2 > stub
        if model == "gemini" and CaptionersGeminiVLM is not None:
            self.model = CaptionersGeminiVLM()
            self.using_gemini = True
        elif model == "openai" and CaptionersOpenAIVLM is not None:
            self.model = CaptionersOpenAIVLM()
            self.using_gemini = False
        elif model == "blip2" and Blip2Captioner is not None:
            self.model = Blip2Captioner()
            self.using_gemini = False
        else:
            self.model = StubCaptioner()
            self.using_gemini = False

    def describe_image(self, path: Path, passes: List[str]) -> Dict[str, Any]:
        from pathlib import Path as _P
        path = _P(path)

        # Base metadata
        base: Dict[str, Any] = {"image_id": path.stem, "source_hash": img_hash(path)}
        rec: Dict[str, Any] = base

        # Run all VLM passes and merge
        for pid in passes:
            out, conf = self.model.run(path, pass_id=pid)
            rec = merge_pass(rec, out, conf, fields_scope=None)

        rec["image_path"] = str(path)

        # Adapt nested colors/pattern from VLM into schema
        _adapt_colors_from_vlm(rec)

        # Sanitize details
        dets = rec.get("details")
        if isinstance(dets, list):
            only_str = [d for d in dets if isinstance(d, str)]
            if only_str:
                rec["details"] = only_str
            else:
                rec.pop("details", None)
        elif dets is not None:
            rec.pop("details", None)

        # Normalize vocab
        if self.normalize:
            rec = normalize_record(rec)

        # Note: pixel/SLIC fallback is disabled. VLM only.

        # Metadata + field defaults
        rec.setdefault("version", "vd_v1.0.0")
        rec.setdefault("confidence", {})
        rec.setdefault("footwear", {"type": None, "color": None})

        _sanitize_types(rec)

        # Optional color validation 
        try:
            validate_record_colors(rec)
        except Exception:
            pass

        # Validate against schema
        allowed = set(Record.model_fields.keys())
        r = Record(**{k: v for k, v in rec.items() if k in allowed})

        output = r.model_dump(mode="python", exclude_none=False)
        
        # Generate and add prompt_text
        try:
            from .export_csv_prompt import prompt_line
            output["prompt_text"] = prompt_line(output)
        except Exception as e:
            output["prompt_text"] = f"{output.get('garment_type', 'garment')} - {output.get('image_id', '')}"
        
        return output

    def enumerate_inputs(self, in_path: Path) -> List[Path]:
        p = Path(in_path)
        if p.is_file():
            return [p] if is_image(p) else []
        return [q for q in p.iterdir() if is_image(q)]