# shared_init.py
"""
Shared initialization for all Streamlit pages.
Import this at the top of every page file.
"""
import streamlit as st
import os
import sys
from pathlib import Path

# This file is now at repo root (moved from ui/)
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
        os.environ["GEMINI_API_KEY"] = st.session_state.gemini_api_key
        os.environ["GOOGLE_API_KEY"] = st.session_state.gemini_api_key
    
    if st.session_state.openai_api_key:
        os.environ["OPENAI_API_KEY"] = st.session_state.openai_api_key

# Auto-initialize when module is imported
init_session_state()
