# NOTE: Requires transformers + torch and a machine with enough RAM/VRAM.
# This file shows the shape; swap to your preferred VLM.
from __future__ import annotations
from typing import Dict, Tuple
from pathlib import Path


class Blip2Captioner:
def __init__(self, model_name: str = "Salesforce/blip2-opt-2.7b", device: str | None = None):
# Lazy import to keep base install light
from transformers import Blip2Processor, Blip2ForConditionalGeneration
import torch
self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
self.processor = Blip2Processor.from_pretrained(model_name)
self.model = Blip2ForConditionalGeneration.from_pretrained(model_name, torch_dtype=torch.float16 if self.device=="cuda" else None)
self.model.to(self.device)


def _ask(self, image_path: Path, prompt: str) -> str:
from PIL import Image
import torch
image = Image.open(image_path).convert("RGB")
inputs = self.processor(images=image, text=prompt, return_tensors="pt").to(self.device)
out = self.model.generate(**inputs, max_new_tokens=200)
return self.processor.decode(out[0], skip_special_tokens=True)


def run(self, image_path: Path, pass_id: str = "A") -> Tuple[Dict, Dict]:
# In practice you'd inject the JSON schema and ask model to return JSON.
# For brevity here, we return a minimal dict and empty confidences.
prompt = {
"A": "Describe the garment (type, silhouette, fabric: type/texture/weight), colors, construction (seams, stitching, hems, closure), fit, styling, pose, lighting setup & mood, photo style. Reply JSON only.",
"B": "Focus ONLY on construction fields (seams, stitching, hems, closure). Reply JSON only with those fields.",
"C": "Focus ONLY on pose, environment_lighting (setup,mood), and photo_style. Reply JSON only with those fields.",
}[pass_id]
text = self._ask(image_path, prompt)
# You should parse/validate JSON here; for MVP we fall back to a tiny guess if parsing fails.
import json
try:
rec = json.loads(text)
except Exception:
rec = {"image_id": image_path.stem}
return rec, {}