# src/visual_descriptor/captioners/gemini_vlm.py
from __future__ import annotations
from typing import Any, Dict, Optional, Tuple
from pathlib import Path
import json, os, base64

try:
    import google.generativeai as genai
    GENAI_OK = True
except Exception:
    GENAI_OK = False
    genai = None  # type: ignore


# ───────────────────────────────────────────────────────────
# Fashion-optimized system prompts for Gemini
# ───────────────────────────────────────────────────────────

FASHION_SYSTEM_CORE = """You are an expert fashion analyst and technical designer with deep knowledge of:
- Garment construction (seams, stitching techniques, closures, hems)
- Fabric identification (fiber types, textures, weights, finishes)
- Silhouette classification and fit analysis
- Color theory and pattern recognition
- Fashion photography composition and lighting

Return ONLY valid JSON. Be precise and confident in your assessments. Use null only when truly uncertain."""

# ───────────────────────────────────────────────────────────
# PASS A — Global assessment (comprehensive)
# ───────────────────────────────────────────────────────────
A_PROMPT = """Analyze this fashion image comprehensively and return STRICT JSON matching this schema:

{
  "garment_type": "string or null (dress/two-piece/jumpsuit/etc)",
  "silhouette": "string or null (bodycon/A-line/straight/oversized/fit-and-flare)",
  
  "fabric": {
    "type": "string or null (jersey/denim/wool/silk/cotton/satin/knit/leather/etc)",
    "texture": "string or null (smooth/ribbed/quilted/brushed/textured/cable-knit)",
    "weight": "string or null (light/medium/heavy)",
    "finish": "string or null (matte/semi-gloss/glossy/shiny)"
  },
  
  "garment": {
    "top_style": "string or null (hoodie/jacket/blazer/cardigan/crop top/tank/tee)",
    "top": "string or null (shirt/blouse/sweater/jacket)",
    "top_sleeve": "string or null (long sleeve/short sleeve/sleeveless/3/4 sleeve)",
    "bottom": "string or null (pants/skirt/shorts/trousers/jeans)"
  },
  
  "garment_components": {
    "top_length": "string or null (cropped/waist/hip/thigh/longline/tunic)",
    "bottom_length": "string or null (mini/short/midi/ankle/maxi/floor)",
    "layers": ["array of visible layer names"]
  },
  
  "fit_and_drape": "string or null (structured/relaxed/oversized/tailored/flowy/bodycon)",
  
  "footwear": {
    "type": "string or null (sneakers/heels/boots/sandals/flats)",
    "color": "string or null"
  },
  
  "colors": {
    "primary": "string or null (main garment color)",
    "secondary": "string or null (second most prominent color)",
    "base": [
      {
        "name": "string or null (color name)",
        "hex": "string or null (#RRGGBB format)",
        "fraction": "number or null (0.0-1.0 representing % of garment)"
      }
    ],
    "accents": [
      {
        "role": "stitching|drawstring|logo|hardware|trim|buttons|zipper_tape|piping|laces",
        "name": "string or null",
        "color": "string or null",
        "hex": "string or null",
        "fraction": "number or null"
      }
    ],
    "pattern": {
      "type": "polka_dot|stripe|plaid|check|colorblock|null",
      "foreground": "string or null (pattern color)",
      "background": "string or null (base color)",
      "ratio_foreground": "number or null (0.0-1.0)",
      "orientation": "vertical|horizontal|diagonal|n/a|null"
    }
  },
  
  "pose": "string or null (standing/walking/seated/three-quarter/facing camera)",
  "photo_style": "string or null (editorial/e-commerce/runway/street style/lookbook)",
  
  "model": {
    "framing": "string or null (full body/three-quarter/waist up/close up)",
    "expression": "string or null (neutral/smiling/serious/confident)",
    "gaze": "string or null (direct/away/down/side)"
  },
  
  "camera": {
    "view": "string or null (front/back/side/three-quarter)",
    "multiview": "string or null (yes/no)",
    "views": "string or null (comma-separated if multiview)",
    "angle": "string or null (eye level/high angle/low angle)"
  },
  
  "environment_lighting": {
    "setup": "string or null (studio/natural light/softbox/ring light)",
    "mood": "string or null (bright/warm/cool/dramatic/neutral)",
    "background": "string or null (plain sweep/gradient/textured/location)"
  }
}

CRITICAL INSTRUCTIONS:
1. For colors: Be specific with names (use shades like "royal purple", "navy", "burgundy" not just "purple", "blue", "red")
2. For patterns: Only set if clearly visible (polka dots, stripes, etc). Otherwise null
3. For fabric.type: Be specific (jersey, denim, wool blend, satin, etc)
4. For construction details: Look for visible seams, topstitching, contrast stitching
5. For garment_type: Be precise (crop top + skirt vs dress vs two-piece set)
6. Return ONLY the JSON object, no markdown, no explanations"""

# ───────────────────────────────────────────────────────────
# PASS B — Construction focus (seams, stitching, closures)
# ───────────────────────────────────────────────────────────
B_PROMPT = """Focus ONLY on construction details. Examine closely for:
- Seam types (flat-felled, French, princess, panel, raglan)
- Stitching (topstitch, contrast stitch, decorative, reinforced)
- Stitching color (matching, contrast-light, contrast-dark, white, black)
- Hems (raw edge, rolled, blind, topstitched, lettuce edge)
- Closures (zipper, buttons, hooks, drawstring, elastic, tie, snap, none)

Return STRICT JSON:

{
  "construction": {
    "seams": "string or null (describe seam type and placement)",
    "stitching": "string or null (topstitch/contrast/decorative/reinforced)",
    "stitching_color": "string or null (matching/contrast-light/contrast-dark/white/black)",
    "hems": "string or null (describe hem finish)",
    "closure": "string or null (zipper/buttons/drawstring/elastic/none)",
    
    "top": {
      "seams": "string or null",
      "stitching": "string or null",
      "stitching_color": "string or null",
      "hems": "string or null",
      "closure": "string or null"
    },
    
    "bottom": {
      "seams": "string or null",
      "stitching": "string or null",
      "stitching_color": "string or null",
      "hems": "string or null",
      "closure": "string or null"
    }
  }
}

Look for:
- Exposed zippers with contrast tape or metal hardware
- Contrast topstitching (especially in different colors)
- Panel seams that define the silhouette
- Hem finishes (clean finish, raw edge, rolled)
- Button/snap plackets

Return ONLY the JSON object."""

# ───────────────────────────────────────────────────────────
# PASS C — Pose, lighting, camera work
# ───────────────────────────────────────────────────────────
C_PROMPT = """Focus ONLY on photography, pose, and presentation. Analyze:

POSE & MODEL:
- Body position (standing straight, walking, seated, twisted, dynamic)
- Model framing (full body, 3/4 length, waist-up, close-up)
- Facial expression (neutral, confident, playful, serious, editorial)
- Gaze direction (direct to camera, away, downward, side glance)

CAMERA:
- Primary view angle (front, back, side profile, three-quarter turn)
- Is this a multi-view layout? (side-by-side front/back)
- Camera angle (eye level, high angle looking down, low angle looking up)

LIGHTING & ENVIRONMENT:
- Lighting setup (studio softbox, natural window light, ring light, dramatic side light)
- Lighting mood (bright and airy, warm and golden, cool and crisp, dramatic high contrast)
- Background (plain studio sweep, gradient, textured wall, outdoor location, white curtain)

Return STRICT JSON:

{
  "pose": "string or null (describe pose clearly)",
  
  "model": {
    "framing": "full body|three-quarter|waist up|close up|null",
    "expression": "string or null",
    "gaze": "direct|away|down|side|null"
  },
  
  "camera": {
    "view": "front|back|side|three-quarter|null",
    "multiview": "yes|no|null",
    "views": "string or null (e.g., 'front, back')",
    "angle": "eye level|high angle|low angle|null"
  },
  
  "environment_lighting": {
    "setup": "string or null (studio softbox/natural light/ring light/etc)",
    "mood": "string or null (bright/warm/cool/dramatic/neutral)",
    "background": "string or null (plain sweep/gradient/textured/location)"
  }
}

Return ONLY the JSON object."""


class GeminiVLM:
    """
    Gemini Flash 2.5 vision captioner optimized for fashion analysis.
    Uses fashion-expert prompts for high-quality garment descriptions.
    """
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        if not GENAI_OK:
            raise RuntimeError("google-generativeai not available. Install: pip install google-generativeai")
        
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable required")
        
        # CRITICAL FIX: Strip whitespace to prevent "illegal header value" gRPC errors
        # This fixes the error: "validate_metadata_from_plugin: INTERNAL:Illegal header value"
        api_key = api_key.strip()
        
        genai.configure(api_key=api_key)
        
        # Use Gemini 2.0 Flash (experimental) - best vision model as of Jan 2025
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": 0.1,  # Low temp for consistent, precise outputs
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
        )
    
    def _image_to_part(self, path: Path) -> Dict[str, Any]:
        """Convert image to Gemini-compatible part."""
        mime_type = "image/jpeg"
        if path.suffix.lower() in {".png"}:
            mime_type = "image/png"
        elif path.suffix.lower() in {".webp"}:
            mime_type = "image/webp"
        
        image_data = path.read_bytes()
        return {
            "mime_type": mime_type,
            "data": image_data
        }
    
    def _call(self, user_prompt: str, image_path: Path) -> Dict[str, Any]:
        """Make a single Gemini API call with image + prompt."""
        try:
            # Build the prompt parts
            parts = [
                user_prompt,
                self._image_to_part(image_path)
            ]
            
            # Generate response
            response = self.model.generate_content(parts)
            
            # Extract JSON from response
            text = response.text.strip()
            
            # Remove markdown code fences if present
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            # Parse JSON
            try:
                return json.loads(text)
            except json.JSONDecodeError as e:
                print(f"[gemini] JSON parse error: {e}")
                print(f"[gemini] Raw response: {text[:500]}")
                return {}
        
        except Exception as e:
            print(f"[gemini] API error: {e}")
            return {}
    
    def run(self, path: Path, pass_id: str = "A") -> Tuple[Dict[str, Any], Optional[float]]:
        """
        Run vision analysis on image.
        
        Args:
            path: Path to image file
            pass_id: Which pass to run (A=global, B=construction, C=pose/lighting)
        
        Returns:
            (result_dict, confidence_score)
        """
        p = (pass_id or "A").upper().strip()
        
        if p == "A":
            out = self._call(A_PROMPT, path)
            return out, (0.9 if out else 0.0)
        
        elif p == "B":
            out = self._call(B_PROMPT, path)
            return out, (0.9 if out else 0.0)
        
        elif p == "C":
            out = self._call(C_PROMPT, path)
            return out, (0.9 if out else 0.0)
        
        return {}, None