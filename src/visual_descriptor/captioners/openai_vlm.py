# src/visual_descriptor/openai_vlm.py
from __future__ import annotations
import base64, json, os
from typing import Any, Dict
from pathlib import Path

from src.visual_descriptor.validators import sanitize_record

# If you use python-openai >= 1.0:
try:
    from openai import OpenAI  # type: ignore
except Exception:
    OpenAI = None  # type: ignore


SYSTEM_PROMPT = """\
You are a meticulous fashion visual descriptor. Return STRICT JSON only (no prose).
Rules:
- Use null for unknowns. NEVER emit the text "string or null".
- Focus on precise facts; avoid inventing closures or contrast stitching unless plainly visible.
- Always populate:
  * garment_type, silhouette, garment top/bottom + lengths
  * fabric: type, texture, weight, finish (matte / semi-gloss / glossy / satin)
  * construction: seams, stitching, hems, closure (global); use top/bottom section details when specific
  * color_palette: 1–2 dominant shades actually visible
  * pose (e.g., standing straight, walking, one hand on hip)
  * model.framing (full-body / three-quarter / half-body / close-up)
  * model.expression (neutral / soft smile / fierce / relaxed)
  * model.gaze (to camera / off-camera)
  * environment_lighting.setup and mood and background (plain studio sweep / draped fabric / runway / textured wall)
  * camera.view (front / back / side / three-quarter). If the image shows front & back at once, set camera.multiview="yes" and camera.views="front, back".
- Keep text concise and canonical.
"""

def _read(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

class OpenAIVLM:
    def __init__(self, model_name: str = "gpt-4o-mini"):
        if OpenAI is None:
            raise RuntimeError("OpenAI client not available in this environment.")
        self.client = OpenAI()
        self.model = os.getenv("OPENAI_VLM_MODEL", model_name)

    def describe(self, image_path: str) -> Dict[str, Any]:
        img_b64 = _read(image_path)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "input_text", "text": "Describe the garment according to the schema."},
                {"type": "input_image", "image_data": img_b64, "mime_type": "image/jpeg"},
            ]},
        ]

        # Responses API (adjust if you use Chat Completions)
        resp = self.client.responses.create(model=self.model, input=messages)
        raw = resp.output_text  # adapt to your client if needed
        data = json.loads(raw)

        # Final guardrail: sanitize & enrich with image heuristics
        return sanitize_record(data, image_path=image_path)