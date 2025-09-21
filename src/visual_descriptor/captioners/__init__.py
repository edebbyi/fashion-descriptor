# src/visual_descriptor/captioners/__init__.py
from .stub import StubCaptioner

OpenAIVLM = None
Blip2Captioner = None

# Try OpenAI captioner
try:
    from .openai_vlm import OpenAIVLM as _OpenAIVLM
    OpenAIVLM = _OpenAIVLM
except Exception as e:
    print("[captioners] OpenAIVLM import failed:", repr(e))

# Try BLIP-2 (optional)
try:
    from .blip2_hf import Blip2Captioner as _Blip2Captioner
    Blip2Captioner = _Blip2Captioner
except Exception as e:
    # it's fine if you don't have this file
    pass
