# src/visual_descriptor/captioners/openai_vlm.py
from __future__ import annotations
from typing import Any, Dict, Optional, List
from pathlib import Path
import base64, json, os

try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # type: ignore


# ───────────────────────────────────────────────────────────
# Fashion-optimized system prompts for OpenAI
# ───────────────────────────────────────────────────────────
SYSTEM_CORE = (
    "You are a vision assistant that returns STRICT JSON ONLY. "
    "If unsure, use null. Do not guess. Do not include any text outside JSON."
)

def _image_to_data_url(path: Path) -> str:
    ext = path.suffix.lower().lstrip(".")
    mime = "image/jpeg" if ext in {"jpg", "jpeg"} else f"image/{ext or 'jpeg'}"
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


# ───────────────────────────────────────────────────────────
# PASS A — Global field assessment
# ───────────────────────────────────────────────────────────
A_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "garment_type": {"type": ["string","null"]},
        "silhouette": {"type": ["string","null"]},
        "fabric": {
            "type": "object",
            "properties": {
                "type": {"type": ["string","null"]},
                "texture": {"type": ["string","null"]},
                "weight": {"type": ["string","null"]},
                "finish": {"type": ["string","null"]}
            },
            "additionalProperties": False
        },
        "garment": {
            "type": "object",
            "properties": {
                "top_style": {"type": ["string","null"]},
                "top": {"type": ["string","null"]},
                "top_sleeve": {"type": ["string","null"]},
                "bottom": {"type": ["string","null"]}
            },
            "additionalProperties": False
        },
        "garment_components": {
            "type": "object",
            "properties": {
                "top_length": {"type": ["string","null"]},
                "bottom_length": {"type": ["string","null"]},
                "layers": {"type": "array","items": {"type":"string"}}
            },
            "additionalProperties": False
        },
        "fit_and_drape": {"type": ["string","null"]},
        "footwear": {
            "type": "object",
            "properties": {
                "type": {"type": ["string","null"]},
                "color": {"type": ["string","null"]}
            },
            "additionalProperties": False
        },
        "colors": {
            "type": "object",
            "properties": {
                "primary": {"type": ["string","null"]},
                "secondary": {"type": ["string","null"]},
                "base": {
                    "type": "array",
                    "maxItems": 5,
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": ["string","null"]},
                            "hex": {"type": ["string","null"]},
                            "fraction": {"type": ["number","null"]}
                        },
                        "additionalProperties": False
                    }
                },
                "accents": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role": {"type": "string", "enum": ["stitching","drawstring","logo","hardware","trim","buttons","zipper_tape","piping","laces"]},
                            "name": {"type": ["string","null"]},
                            "color": {"type": ["string","null"]},
                            "hex": {"type": ["string","null"]},
                            "fraction": {"type": ["number","null"]}
                        },
                        "required": ["role"],
                        "additionalProperties": False
                    }
                },
                "pattern": {
                    "type": ["object","null"],
                    "properties": {
                        "type": {"type": ["string","null"], "enum": ["polka_dot","stripe","plaid","check","colorblock",None]},
                        "foreground": {"type": ["string","null"]},
                        "background": {"type": ["string","null"]},
                        "ratio_foreground": {"type": ["number","null"]},
                        "orientation": {"type": ["string","null"], "enum": ["vertical","horizontal","diagonal","n/a",None]}
                    },
                    "additionalProperties": False
                }
            },
            "additionalProperties": False
        },
        "pose": {"type": ["string","null"]},
        "photo_style": {"type": ["string","null"]},
        "model": {
            "type": "object",
            "properties": {
                "framing": {"type": ["string","null"]},
                "expression": {"type": ["string","null"]},
                "gaze": {"type": ["string","null"]}
            },
            "additionalProperties": False
        },
        "camera": {
            "type": "object",
            "properties": {
                "view": {"type": ["string","null"]},
                "multiview": {"type": ["string","null"]},
                "views": {"type": ["string","null"]},
                "angle": {"type": ["string","null"]}
            },
            "additionalProperties": False
        },
        "environment_lighting": {
            "type": "object",
            "properties": {
                "setup": {"type": ["string","null"]},
                "mood": {"type": ["string","null"]},
                "background": {"type": ["string","null"]}
            },
            "additionalProperties": False
        }
    },
    "additionalProperties": False
}
A_SYSTEM = (
    SYSTEM_CORE +
    " Capture global garment fields conservatively. "
    "Only set colors/pattern when visually obvious (e.g., clear dots/stripes). "
    "Return STRICT JSON only."
)

# ───────────────────────────────────────────────────────────
# PASS B — Construction only
# ───────────────────────────────────────────────────────────
B_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "construction": {
            "type": "object",
            "properties": {
                "seams": {"type": ["string","null"]},
                "stitching": {"type": ["string","null"]},
                "stitching_color": {"type": ["string","null"]},
                "hems": {"type": ["string","null"]},
                "closure": {"type": ["string","null"]},
                "top": {
                    "type": "object",
                    "properties": {
                        "seams": {"type": ["string","null"]},
                        "stitching": {"type": ["string","null"]},
                        "stitching_color": {"type": ["string","null"]},
                        "hems": {"type": ["string","null"]},
                        "closure": {"type": ["string","null"]}
                    },
                    "additionalProperties": False
                },
                "bottom": {
                    "type": "object",
                    "properties": {
                        "seams": {"type": ["string","null"]},
                        "stitching": {"type": ["string","null"]},
                        "stitching_color": {"type": ["string","null"]},
                        "hems": {"type": ["string","null"]},
                        "closure": {"type": ["string","null"]}
                    },
                    "additionalProperties": False
                }
            },
            "additionalProperties": False
        }
    },
    "additionalProperties": False
}
B_SYSTEM = SYSTEM_CORE + " Refine construction only. Do not change unrelated fields. Return STRICT JSON only."

# ───────────────────────────────────────────────────────────
# PASS C — Pose & Lighting only
# ───────────────────────────────────────────────────────────
C_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "pose": {"type": ["string","null"]},
        "model": {
            "type": "object",
            "properties": {
                "framing": {"type": ["string","null"]},
                "expression": {"type": ["string","null"]},
                "gaze": {"type": ["string","null"]}
            },
            "additionalProperties": False
        },
        "camera": {
            "type": "object",
            "properties": {
                "view": {"type": ["string","null"]},
                "multiview": {"type": ["string","null"]},
                "views": {"type": ["string","null"]},
                "angle": {"type": ["string","null"]}
            },
            "additionalProperties": False
        },
        "environment_lighting": {
            "type": "object",
            "properties": {
                "setup": {"type": ["string","null"]},
                "mood": {"type": ["string","null"]},
                "background": {"type": ["string","null"]}
            },
            "additionalProperties": False
        }
    },
    "additionalProperties": False
}
C_SYSTEM = SYSTEM_CORE + " Refine pose/model/camera/environment lighting only. Return STRICT JSON only."


class OpenAIVLM:
    """
    Vision VLM using GPT-4o.
    Tries Responses API + JSON Schema; falls back to Chat Completions + json_object.
    """
    def __init__(self, model_name: str = "gpt-4o"):
        if OpenAI is None:
            raise RuntimeError("openai SDK not available. Install `openai` and set OPENAI_API_KEY.")
        self.client = OpenAI()
        self.model = model_name

    # Unified call
    def _call(self, system_text: str, schema: Dict[str, Any], image_path: Path) -> Dict[str, Any]:
        data_url = _image_to_data_url(image_path)

        # 1) Try Responses API with JSON Schema
        try:
            resp = self.client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": system_text},
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": "Return STRICT JSON per schema."},
                            {"type": "input_image", "image_url": data_url},
                        ],
                    },
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": "pass_payload", "schema": schema, "strict": True},
                },
            )
            return json.loads(resp.output_text)
        except TypeError as e:
            # Older SDK: Responses.create doesn't accept response_format
            if "response_format" not in str(e):
                raise
            # fall through to chat.completions
        except AttributeError:
            # Older SDK with no Responses API; fall through
            pass
        except Exception:
            # Any other Responses error → try chat fallback
            pass

        # 2) Chat Completions fallback with json_object (older SDKs)
        schema_as_text = json.dumps(schema)
        messages = [
            {"role": "system", "content": system_text + " You MUST return JSON that validates against this JSON Schema: " + schema_as_text},
            {"role": "user", "content": [
                {"type": "text", "text": "Extract fields and return STRICT JSON only."},
                {"type": "image_url", "image_url": {"url": data_url}}
            ]},
        ]
        chat = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0
        )
        content = chat.choices[0].message.content or "{}"
        try:
            return json.loads(content)
        except Exception:
            return {}

    # Pass switch
    def run(self, path: Path, pass_id: str = "A") -> tuple[Dict[str, Any], Optional[float]]:
        p = (pass_id or "A").upper().strip()
        if p == "A":
            out = self._call(A_SYSTEM, A_SCHEMA, path)
            return out, (0.8 if out else 0.0)
        if p == "B":
            out = self._call(B_SYSTEM, B_SCHEMA, path)
            return out, (0.8 if out else 0.0)
        if p == "C":
            out = self._call(C_SYSTEM, C_SCHEMA, path)
            return out, (0.8 if out else 0.0)
        return {}, None