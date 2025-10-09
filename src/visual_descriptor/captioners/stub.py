# src/visual_descriptor/captioners/stub.py
from __future__ import annotations
from typing import Dict, Tuple
from pathlib import Path
from ..utils import (
    load_image_size,
    dominant_color_shades,
    estimate_warmth_from_palette,
    has_vertical_bright_line_center,
    has_midriff_gap,
)

# Minimal Fixed vocab
_SILHS = ["a-line","sheath","boxy","straight","fit-and-flare","oversized","bodycon","wrap"]
_PHOTO_STYLES = ["editorial studio","e-comm flat","runway","street style","lookbook"]
_POSES = ["standing","walking","three-quarter","seated","profile"]

class StubCaptioner:
    """
    Free, image-aware stub (no external APIs).
    Heuristics include:
      • dominant color shades via palette extraction (e.g., 'royal purple', 'amethyst', 'plum')
      • zipper hint: vertical bright line near center
      • two-piece hint: midriff gap detection (crop top + skirt)
    Returns (record, confidence_map). When pass_id != "A", only a subset of fields is returned.
    """
    def __init__(self, *_, **__):
        pass

    def run(self, image_path: Path, pass_id: str = "A") -> Tuple[Dict, Dict]:
        _w, _h = load_image_size(image_path)
        palette = dominant_color_shades(image_path, k=3)
        mood = estimate_warmth_from_palette(palette)
        has_zip = has_vertical_bright_line_center(image_path)
        two_piece = has_midriff_gap(image_path)

        # Defaults 
        garment = "dress"
        silhouette = "bodycon" if two_piece or ("purple" in palette or "royal purple" in palette) else "sheath"
        photo_style = "runway"
        pose = "walking"

        # Garment overrides
        if two_piece:
            garment = "two-piece set (crop top + skirt)"
        elif has_zip:
            garment = "jacket"  # NOTE: we only reach here if has_zip is True

        stitching = "contrast topstitch" if any(n in palette for n in ["white","gray"]) else "topstitch"
        seams = "panel seams" if silhouette in ["bodycon","sheath"] else "flat seams"
        closure = "zip" if has_zip else "none"

        
        # ───────────────────────────────────────────────────────────
        # PASS A — Global field "assessment"
        # ───────────────────────────────────────────────────────────
        base = {
            "image_id": image_path.stem,
            "garment_type": garment,
            "silhouette": silhouette,
            "fabric": {"type": "jersey", "texture": "smooth", "weight": "medium"},
            "color_palette": palette,
            "construction": {
                "seams": seams,
                "stitching": stitching,
                "hems": "clean finish",
                "closure": closure,
            },
            "details": (["exposed front zipper with ring pull"] if has_zip else []),
            "fit_and_drape": "structured, bodycon" if silhouette == "bodycon" else "soft drape",
            "styling": {"layering": None, "accessories": None},
            "pose": pose,
            "environment_lighting": {"setup": "softbox", "mood": mood},
            "photo_style": photo_style,
        }

        # ───────────────────────────────────────────────────────────
        # PASS B — Construction focus (returns subset + confidences)
        # ───────────────────────────────────────────────────────────
        if pass_id == "B":
            return (
                {"image_id": image_path.stem, "construction": base["construction"]},
                {"construction": {"stitching": 0.7, "seams": 0.65, "hems": 0.6, "closure": 0.7 if has_zip else 0.4}},
            )

        # ───────────────────────────────────────────────────────────
        # PASS C — Pose, lighting, camera work (subset + confidences)
        # ───────────────────────────────────────────────────────────
        if pass_id == "C":
            return (
                {
                    "image_id": image_path.stem,
                    "pose": base["pose"],
                    "environment_lighting": base["environment_lighting"],
                    "photo_style": base["photo_style"],
                },
                {"pose": 0.7, "environment_lighting": {"setup": 0.65, "mood": 0.6}, "photo_style": 0.6},
            )

        # Default (PASS A): broad caption + coarse confidences
        return (base, {"garment_type": 0.65, "silhouette": 0.7, "pose": 0.7, "photo_style": 0.65})
