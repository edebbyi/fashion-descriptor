# src/visual_descriptor/captioners/__init__.py
from __future__ import annotations

__all__ = [
"schema", "engine", "multipass_merge", "normalize_vocab", "export_csv_prompt"
]

# Lightweight stubs so imports never explode if optional models aren't installed.
class StubCaptioner:
    def run(self, image_path, pass_id="A"):
        # Return a minimal, obviously-fake record (helps detect if stub is used).
        out = {
            "image_id": image_path.stem,
            "garment_type": None,
            "garment": {"top": None, "bottom": None},
            "garment_components": {"top_length": None, "bottom_length": None, "layers": []},
            "fabric": {"type": None, "texture": None, "weight": None, "finish": None},
            "construction": {
                "seams": None, "stitching": None, "stitching_color": None, "hems": None, "closure": None,
                "top": None, "bottom": None
            },
            "color_palette": [],
            "pose": None,
            "environment_lighting": {"setup": None, "mood": None, "background": None},
            "photo_style": None,
            "footwear": {"type": None, "color": None},
            "model": {"framing": None, "expression": None, "gaze": None},
            "camera": {"view": None, "multiview": None, "views": None, "angle": None},
            "details": [],
            "notes_uncertain": [],
            "photo_metrics": {},
        }
        conf = {"garment_type": 0.1}
        return out, conf

try:
    from .openai_vlm import OpenAIVLM  # our actual VLM
except Exception as e:
    OpenAIVLM = None  # if import fails we fall back to StubCaptioner

# BLIP2 optional hook (not required)
try:
    from .blip2 import Blip2Captioner  # if you implement later
except Exception:
    Blip2Captioner = None
