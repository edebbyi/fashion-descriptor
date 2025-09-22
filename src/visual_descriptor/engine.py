# src/visual_descriptor/engine.py
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List

from .multipass_merge import merge_pass
from .normalize_vocab import normalize_record
from .schema import Record
from .captioners import StubCaptioner, Blip2Captioner, OpenAIVLM as CaptionersOpenAIVLM
from .utils import img_hash, is_image

# Safe import (no-op if the symbol is absent in your validators.py)
try:
    from .validators import validate_record_colors
except Exception:
    def validate_record_colors(_rec):  # no-op fallback
        return


# --- adapter: lift VLM's nested colors/pattern into your existing fields ---
def _adapt_colors_from_vlm(rec: Dict[str, Any]) -> None:
    """
    Mutates rec in place.
    Expects possibly nested:
      rec['colors'] with keys primary/secondary/accents/pattern
      and/or a top-level rec['pattern'].
    Maps to your schema:
      - color_primary, color_secondary (top-level strings)
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
        # de-dup preserving order
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


# --- minimal type sanitizer to protect pydantic from VLM bools/etc ---
def _coerce_str(value: Any) -> str | None:
    """Return value if it's a non-empty string; otherwise None."""
    if isinstance(value, str):
        s = value.strip()
        return s if s else None
    return None  # Booleans, numbers, dicts, lists → None (schema expects str)

def _sanitize_types(rec: Dict[str, Any]) -> None:
    """
    In-place: ensure fields that the schema expects as strings are actually strings (or None).
    We only touch a few known culprits; everything else is left intact.
    """
    g = rec.get("garment")
    if not isinstance(g, dict):
        rec["garment"] = {}
        g = rec["garment"]

    # Known string fields in garment block and mirrored top-level shadows
    for key in ("top_style", "top", "top_sleeve", "bottom", "silhouette", "garment_type"):
        if key in rec:
            rec[key] = _coerce_str(rec.get(key))
        if key in g:
            g[key] = _coerce_str(g.get(key))

    # Construction sub-blocks sometimes get booleans too; keep strings or None
    cons = rec.get("construction")
    if isinstance(cons, dict):
        for key in ("seams", "stitching", "stitching_color", "hems", "closure"):
            if key in cons:
                cons[key] = _coerce_str(cons.get(key))
        # optional nested top/bottom construction pieces
        for piece_key in ("top", "bottom"):
            piece = cons.get(piece_key)
            if isinstance(piece, dict):
                for key in ("seams", "stitching", "stitching_color", "hems", "closure"):
                    if key in piece:
                        piece[key] = _coerce_str(piece.get(key))

    # details must be list[str] or absent
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
        # your GPT-4o wrapper lives in captioners.py
        if model == "openai" and CaptionersOpenAIVLM is not None:
            self.model = CaptionersOpenAIVLM()  # GPT-4o-backed VLM
            self.using_openai = True
        elif model == "blip2" and Blip2Captioner is not None:
            self.model = Blip2Captioner()
            self.using_openai = False
        else:
            self.model = StubCaptioner()
            self.using_openai = False

    def describe_image(self, path: Path, passes: List[str]) -> Dict[str, Any]:
        # coerce to Path in case a string sneaks in
        from pathlib import Path as _P
        path = _P(path)

        # base metadata
        base: Dict[str, Any] = {"image_id": path.stem, "source_hash": img_hash(path)}
        rec: Dict[str, Any] = base

        # run all VLM passes and merge
        for pid in passes:
            out, conf = self.model.run(path, pass_id=pid)
            rec = merge_pass(rec, out, conf, fields_scope=None)

        # give the pipeline the actual file path
        rec["image_path"] = str(path)

        # adapt nested colors/pattern from VLM into your schema
        _adapt_colors_from_vlm(rec)

        # sanitize details now (in case a VLM pass wrote objects there)
        dets = rec.get("details")
        if isinstance(dets, list):
            only_str = [d for d in dets if isinstance(d, str)]
            if only_str:
                rec["details"] = only_str
            else:
                rec.pop("details", None)
        elif dets is not None:
            rec.pop("details", None)

        # normalize vocab (lightweight)
        if self.normalize:
            rec = normalize_record(rec)

        # IMPORTANT: pixel/SLIC fallback is DISABLED. We trust GPT-4o only.

        # metadata + field defaults
        rec.setdefault("version", "vd_v1.0.0")
        rec.setdefault("confidence", {})
        rec.setdefault("footwear", {"type": None, "color": None})

        # sanitize types before schema validation
        _sanitize_types(rec)

        # optional color validation (non-fatal)
        try:
            validate_record_colors(rec)
        except Exception:
            pass

        # validate against schema (filter unknown keys)
        allowed = set(Record.model_fields.keys())
        r = Record(**{k: v for k, v in rec.items() if k in allowed})

        # include keys even if values are None
        return r.model_dump(mode="python", exclude_none=False)

    def enumerate_inputs(self, in_path: Path) -> List[Path]:
        # keep your original non-recursive behavior
        p = Path(in_path)
        if p.is_file():
            return [p] if is_image(p) else []
        return [q for q in p.iterdir() if is_image(q)]
