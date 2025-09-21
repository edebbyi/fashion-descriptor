# src/visual_descriptor/normalize_vocab.py
from __future__ import annotations
from typing import Dict

LOWER_MAP = {
    "three quarter": "three-quarter",
    "3/4": "three-quarter",
    "full body": "full-body",
    "semi gloss": "semi-gloss",
    "satin finish": "satin",
    "mat": "matte",
}

BAN = {"string or null", "null", "none", "None", ""}

def _norm_token(s: str) -> str:
    if not s:
        return ""
    s2 = s.strip()
    if s2 in BAN or s2.lower() in BAN:
        return ""
    s2 = s2.replace("–", "-").replace("—", "-")
    s2_low = s2.lower()
    for k, v in LOWER_MAP.items():
        if k in s2_low:
            return v
    return s2

def normalize_text(s: str | None) -> str:
    """Canonicalize small variants; remove banned placeholders."""
    if s is None:
        return ""
    return _norm_token(s)