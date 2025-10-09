# shared_init.py
"""
Shared initialization for all Streamlit pages.
"""
import streamlit as st
import os
import sys
from pathlib import Path

repo_root = Path(__file__).parent.resolve()

# Add repo root to path if not already present
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

def init_session_state():
    """Initialize all session state variables if they don't exist."""
    
    # API Keys
    if "gemini_api_key" not in st.session_state:
        st.session_state.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
    
    if "openai_api_key" not in st.session_state:
        st.session_state.openai_api_key = os.getenv("OPENAI_API_KEY", "")
    
    # API Key validation status
    if "gemini_key_valid" not in st.session_state:
        st.session_state.gemini_key_valid = None  # None = not tested, True/False = result
    
    if "openai_key_valid" not in st.session_state:
        st.session_state.openai_key_valid = None
    
    # Analysis data
    if "analyzed_images" not in st.session_state:
        st.session_state.analyzed_images = []
    
    if "collection" not in st.session_state:
        st.session_state.collection = []
    
    if "engine" not in st.session_state:
        st.session_state.engine = None
    
    # Settings
    if "default_model" not in st.session_state:
        st.session_state.default_model = "gemini"
    
    if "normalize_vocab" not in st.session_state:
        st.session_state.normalize_vocab = True
    
    if "default_passes" not in st.session_state:
        st.session_state.default_passes = ["A", "B", "C"]
    
    if "default_export" not in st.session_state:
        st.session_state.default_export = "JSON"
    
    if "include_confidence" not in st.session_state:
        st.session_state.include_confidence = False

def set_api_keys():
    """Set API keys as environment variables."""
    if st.session_state.gemini_api_key:
        # Strip whitespace to avoid API errors
        clean_key = st.session_state.gemini_api_key.strip()
        os.environ["GEMINI_API_KEY"] = clean_key
        os.environ["GOOGLE_API_KEY"] = clean_key
    
    if st.session_state.openai_api_key:
        # Strip whitespace to avoid API errors
        clean_key = st.session_state.openai_api_key.strip()
        os.environ["OPENAI_API_KEY"] = clean_key

def validate_api_key(key_type: str, api_key: str) -> tuple[bool, str]:
    """
    Validate an API key by attempting a minimal API call.
    
    Args:
        key_type: "gemini" or "openai"
        api_key: The API key to validate
    
    Returns:
        (is_valid, error_message)
    """
    if not api_key or not api_key.strip():
        return False, "API key is empty"
    
    api_key = api_key.strip()
    
    if key_type == "gemini":
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            # Try to list models as a lightweight validation
            models = genai.list_models()
            list(models)  # Force evaluation
            return True, "✅ Gemini API key is valid"
        except Exception as e:
            error_msg = str(e)
            if "API_KEY_INVALID" in error_msg or "invalid" in error_msg.lower():
                return False, "❌ Gemini API key is invalid"
            elif "quota" in error_msg.lower():
                return False, "API key valid but quota exceeded"
            else:
                return False, f"Validation failed: {error_msg[:100]}"
    
    elif key_type == "openai":
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            # Try to list models for validation
            client.models.list()
            return True, "✅ OpenAI API key is valid"
        except Exception as e:
            error_msg = str(e)
            if "Incorrect API key" in error_msg or "invalid" in error_msg.lower():
                return False, "❌ OpenAI API key is invalid"
            elif "quota" in error_msg.lower() or "insufficient" in error_msg.lower():
                return False, "API key valid but quota exceeded"
            else:
                return False, f"Validation failed: {error_msg[:100]}"
    
    return False, "Unknown key type"

def has_valid_api_key() -> bool:
    """Check if user has at least one valid API key."""
    return (st.session_state.gemini_key_valid == True) or (st.session_state.openai_key_valid == True)

# Auto-initialize when module is imported
init_session_state()