# src/visual_descriptor/captioners/openai_vlm.py
from __future__ import annotations
from typing import Any, Dict, Optional, Tuple
from pathlib import Path
import base64, json, os

try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # type: ignore


# ───────────────────────────────────────────────────────────
# Fashion-optimized system prompts for OpenAI
# ───────────────────────────────────────────────────────────

FASHION_SYSTEM_CORE = """You are an expert fashion analyst and technical designer with deep knowledge of:
- Garment construction (seams, stitching techniques, closures, hems)
- Fabric identification (fiber types, textures, weights, finishes)
- Silhouette classification and fit analysis
- Color theory and pattern recognition
- Fashion photography composition and lighting

Return ONLY valid JSON matching the provided schema. Be precise and confident in your assessments. Use null only when truly uncertain."""


# ───────────────────────────────────────────────────────────
# Helper: Convert image to base64 data URL
# ───────────────────────────────────────────────────────────

def _image_to_data_url(path: Path) -> str:
    """Convert image file to base64 data URL for OpenAI API."""
    ext = path.suffix.lower().lstrip(".")
    mime = "image/jpeg" if ext in {"jpg", "jpeg"} else f"image/{ext or 'jpeg'}"
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


# ───────────────────────────────────────────────────────────
# PASS A — Global field assessment
# ───────────────────────────────────────────────────────────

A_PROMPT = """Analyze this fashion image comprehensively and return STRICT JSON matching the provided schema.

**What to analyze:**

GARMENT IDENTIFICATION:
- Type: dress/two-piece/jumpsuit/jacket/pants/skirt/etc
- Silhouette: bodycon/A-line/straight/oversized/fit-and-flare/wrap
- Top style: hoodie/jacket/blazer/cardigan/crop top/tank/tee
- Top details: shirt/blouse/sweater type, sleeve length
- Bottom: pants/skirt/shorts/trousers/jeans
- Component lengths: cropped/waist/hip/midi/maxi

FABRIC ANALYSIS:
- Type: jersey/denim/wool/silk/cotton/satin/knit/leather (be specific)
- Texture: smooth/ribbed/quilted/brushed/textured/cable-knit
- Weight: light/medium/heavy
- Finish: matte/semi-gloss/glossy/shiny

FIT & DRAPE:
- How the garment sits: structured/relaxed/oversized/tailored/flowy/bodycon

COLORS & PATTERNS:
- Primary color (main garment color - be specific: "royal purple" not just "purple")
- Secondary color (second most prominent)
- Base colors: up to 5 color swatches with names, hex codes, and coverage fractions
- Accent colors: stitching/drawstring/logo/hardware/trim/buttons/zipper tape/piping
- Pattern detection: polka dots, stripes, plaid, checks, colorblocks
- Pattern details: foreground/background colors, scale, density, orientation

FOOTWEAR:
- Type: sneakers/heels/boots/sandals/flats
- Color if visible

PHOTOGRAPHY:
- Pose: standing/walking/seated/three-quarter/facing camera
- Photo style: editorial/e-commerce/runway/street style/lookbook
- Model framing: full body/three-quarter/waist up/close up
- Model expression: neutral/smiling/serious/confident
- Model gaze: direct/away/down/side
- Camera view: front/back/side/three-quarter
- Multi-view: yes/no (side-by-side front/back layouts)
- Camera angle: eye level/high angle/low angle
- Lighting setup: studio/natural light/softbox/ring light
- Lighting mood: bright/warm/cool/dramatic/neutral
- Background: plain sweep/gradient/textured/location

CRITICAL INSTRUCTIONS:
1. For colors: Use specific shade names (royal purple, navy, burgundy - not just purple, blue, red)
2. For patterns: Only set if clearly visible. Otherwise use null
3. For fabric.type: Be precise (jersey, denim, wool blend, not just "fabric")
4. For construction: Look for visible seams, topstitching, contrast stitching
5. For garment_type: Be exact (crop top + skirt vs dress vs two-piece set)
6. Return ONLY the JSON object matching the schema"""

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


# ───────────────────────────────────────────────────────────
# PASS B — Construction focus (seams, stitching, closures)
# ───────────────────────────────────────────────────────────

B_PROMPT = """Focus ONLY on construction details. Return STRICT JSON matching the provided schema.

**Examine closely for:**

SEAM TYPES & PLACEMENT:
- Flat-felled seams (clean finish on both sides)
- French seams (enclosed raw edges)
- Princess seams (vertical shaping seams from shoulder/armhole to hem)
- Panel seams (vertical or horizontal divisions)
- Raglan seams (diagonal from underarm to neckline)
- Side seams, center seams, yoke seams

STITCHING TECHNIQUES:
- Topstitch (visible stitching on garment exterior)
- Contrast stitching (different color from fabric)
- Decorative stitching (ornamental patterns)
- Reinforced stitching (extra strength at stress points)
- Edgestitching (very close to seam or edge)

STITCHING COLOR:
- Matching (same as fabric color)
- Contrast-light (lighter than base fabric)
- Contrast-dark (darker than base fabric)  
- White (specific white thread)
- Black (specific black thread)

HEM FINISHES:
- Raw edge (unfinished, intentionally frayed)
- Rolled hem (narrow, rolled finish)
- Blind hem (invisible from exterior)
- Topstitched hem (visible stitching)
- Lettuce edge (wavy, stretched finish)
- Clean finish (serged or bound)

CLOSURES:
- Zipper (exposed, concealed, or decorative)
- Buttons (functional or decorative)
- Hooks and eyes
- Drawstring
- Elastic waistband
- Tie closure
- Snaps
- None (pull-on style)

**Look for these specific details:**
- Exposed zippers with contrast tape or metal hardware
- Contrast topstitching (especially in different colors)
- Panel seams that define the silhouette
- Hem finishes (clean, raw edge, rolled)
- Button/snap plackets and their orientation

Return ONLY the JSON object matching the schema."""

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


# ───────────────────────────────────────────────────────────
# PASS C — Pose, lighting, camera work
# ───────────────────────────────────────────────────────────

C_PROMPT = """Focus ONLY on photography, pose, and presentation. Return STRICT JSON matching the provided schema.

**Analyze these aspects:**

POSE & BODY POSITION:
- Standing straight (neutral stance)
- Walking (in motion, mid-stride)
- Seated (sitting pose)
- Twisted or turned (dynamic positioning)
- Three-quarter turn (angled between front and side)
- Profile (full side view)
- Hand positioning and gestures

MODEL FRAMING:
- Full body (head to feet visible)
- Three-quarter length (head to knees/mid-thigh)
- Waist-up (upper body only)
- Close-up (detail shot, partial garment)

FACIAL EXPRESSION:
- Neutral (no emotion, editorial)
- Confident (strong, assertive)
- Playful (fun, energetic)
- Serious (intense, focused)
- Smiling (happy, approachable)
- Editorial (high-fashion, storytelling)

GAZE DIRECTION:
- Direct to camera (engaging viewer)
- Away from camera (looking off)
- Downward (looking down)
- Side glance (looking to side)

CAMERA VIEW:
- Front (facing camera directly)
- Back (rear view)
- Side profile (90° from camera)
- Three-quarter (45° angle)

MULTI-VIEW DETECTION:
- Is this a side-by-side layout? (front + back, or multiple angles)
- If yes, list the views shown (e.g., "front, back")

CAMERA ANGLE:
- Eye level (camera at model's eye height - most common)
- High angle (camera looking down)
- Low angle (camera looking up)

LIGHTING SETUP:
- Studio softbox (even, diffused lighting)
- Natural window light (soft, directional daylight)
- Ring light (circular, even illumination)
- Dramatic side light (strong shadows, contrast)
- Overhead lighting (top-down illumination)

LIGHTING MOOD:
- Bright and airy (high key, cheerful)
- Warm and golden (sunset tones, cozy)
- Cool and crisp (blue tones, clean)
- Dramatic high contrast (strong shadows)
- Neutral (balanced, natural)

BACKGROUND:
- Plain studio sweep (seamless white/gray backdrop)
- Gradient (color transition)
- Textured wall (brick, concrete, wood)
- Outdoor location (street, park, building)
- White curtain or draped fabric

Return ONLY the JSON object matching the schema."""

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


# ───────────────────────────────────────────────────────────
# OpenAI VLM Captioner Class
# ───────────────────────────────────────────────────────────

class OpenAIVLM:
    """
    GPT-4o vision captioner optimized for fashion analysis.
    
    Uses OpenAI's Responses API with JSON Schema validation for structured output.
    Falls back to Chat Completions API for older SDK versions.
    
    Features:
    - Dual API approach (Responses + fallback)
    - Strict JSON Schema validation
    - Fashion-expert prompts for high-quality descriptions
    - Temperature 0 for consistent outputs
    """
    
    def __init__(self, model_name: str = "gpt-4o"):
        """
        Initialize OpenAI VLM captioner.
        
        Args:
            model_name: OpenAI model to use (default: gpt-4o)
        
        Raises:
            RuntimeError: If openai SDK not installed or OPENAI_API_KEY not set
        """
        if OpenAI is None:
            raise RuntimeError(
                "openai SDK not available. Install: pip install openai\n"
                "Set OPENAI_API_KEY environment variable"
            )
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable required")
        
        self.client = OpenAI(api_key=api_key.strip())
        self.model = model_name
    
    def _call(self, user_prompt: str, schema: Dict[str, Any], image_path: Path) -> Dict[str, Any]:
        """
        Make a single OpenAI API call with image + prompt.
        
        Strategy:
        1. Try Responses API with strict JSON Schema (newest SDK)
        2. Fall back to Chat Completions with json_object mode (older SDK)
        
        Args:
            user_prompt: Fashion analysis instructions
            schema: JSON Schema for response validation
            image_path: Path to image file
        
        Returns:
            Parsed JSON response as dict
        """
        data_url = _image_to_data_url(image_path)

        # ───────────────────────────────────────────────────────────
        # ATTEMPT 1: Responses API with JSON Schema (preferred)
        # ───────────────────────────────────────────────────────────
        try:
            resp = self.client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": FASHION_SYSTEM_CORE},
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": user_prompt},
                            {"type": "input_image", "image_url": data_url},
                        ],
                    },
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "fashion_analysis",
                        "schema": schema,
                        "strict": True
                    },
                },
            )
            return json.loads(resp.output_text)
        
        except TypeError as e:
            # Older SDK: Responses.create doesn't accept response_format
            if "response_format" not in str(e):
                raise
            # Fall through to chat completions
        
        except AttributeError:
            # Older SDK with no Responses API
            pass
        
        except Exception as e:
            # Any other Responses error → try chat fallback
            print(f"[openai] Responses API failed: {e}, trying Chat Completions...")

        # ───────────────────────────────────────────────────────────
        # ATTEMPT 2: Chat Completions with json_object (fallback)
        # ───────────────────────────────────────────────────────────
        schema_text = json.dumps(schema, indent=2)
        system_prompt = (
            f"{FASHION_SYSTEM_CORE}\n\n"
            f"You MUST return JSON that validates against this schema:\n"
            f"```json\n{schema_text}\n```"
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": data_url}}
                ]
            },
        ]
        
        chat = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0  # Deterministic for consistency
        )
        
        content = chat.choices[0].message.content or "{}"
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"[openai] JSON parse error: {e}")
            print(f"[openai] Raw response: {content[:500]}")
            return {}
    
    def run(self, path: Path, pass_id: str = "A") -> Tuple[Dict[str, Any], Optional[float]]:
        """
        Run vision analysis on fashion image.
        
        Args:
            path: Path to image file
            pass_id: Which analysis pass to run (A/B/C)
                - A: Global garment analysis (type, fabric, colors, photography)
                - B: Construction details (seams, stitching, closures)
                - C: Pose and lighting (photography, camera, environment)
        
        Returns:
            Tuple of (result_dict, confidence_score)
            Confidence is 0.8 if successful, 0.0 if failed
        """
        p = (pass_id or "A").upper().strip()
        
        # ───────────────────────────────────────────────────────────
        # PASS A: Global field assessment
        # ───────────────────────────────────────────────────────────
        if p == "A":
            out = self._call(A_PROMPT, A_SCHEMA, path)
            return out, (0.8 if out else 0.0)
        
        # ───────────────────────────────────────────────────────────
        # PASS B: Construction details only
        # ───────────────────────────────────────────────────────────
        elif p == "B":
            out = self._call(B_PROMPT, B_SCHEMA, path)
            return out, (0.8 if out else 0.0)
        
        # ───────────────────────────────────────────────────────────
        # PASS C: Pose, lighting, camera work
        # ───────────────────────────────────────────────────────────
        elif p == "C":
            out = self._call(C_PROMPT, C_SCHEMA, path)
            return out, (0.8 if out else 0.0)
        
        # Unknown pass ID
        return {}, None