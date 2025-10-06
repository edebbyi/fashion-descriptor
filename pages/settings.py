# pages/settings.py
import streamlit as st
import os
from pathlib import Path
import sys

# Path setup
repo_root = Path(__file__).parent.parent.resolve()
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from shared_init import init_session_state, validate_api_key, set_api_keys

# Initialize session state
init_session_state()

st.title("⚙️ Settings")
st.markdown("*Configure your Fashion Descriptor AI preferences*")
st.markdown("---")

# API Configuration
st.markdown("## 🔑 API Key Management")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Gemini API")
    
    # Status display
    if st.session_state.gemini_key_valid == True:
        st.success("✅ **Valid and Verified**")
    elif st.session_state.gemini_key_valid == False:
        st.error("❌ **Invalid or Failed Validation**")
    elif st.session_state.gemini_api_key:
        st.warning("⚠️ **Not Validated**")
    else:
        st.info("ℹ️ **Not Configured**")
    
    st.markdown("""
    **Gemini Flash 2.5**
    - Best for fashion analysis
    - FREE with rate limits
    - Superior color/construction detection
    
    [Get your key →](https://aistudio.google.com/app/apikey)
    """)
    
    if st.session_state.gemini_api_key:
        key_preview = st.session_state.gemini_api_key[:8] + "..." + st.session_state.gemini_api_key[-4:]
        st.code(key_preview)
        
        # Test button
        if st.button("🔍 Test Gemini Key", use_container_width=True):
            with st.spinner("Testing API key..."):
                is_valid, msg = validate_api_key("gemini", st.session_state.gemini_api_key)
                st.session_state.gemini_key_valid = is_valid
                if is_valid:
                    st.success(f"✅ {msg}")
                    set_api_keys()
                else:
                    st.error(f"❌ {msg}")
        
        if st.button("🗑️ Clear Gemini Key", use_container_width=True):
            st.session_state.gemini_api_key = ""
            st.session_state.gemini_key_valid = None
            st.session_state.engine = None
            if "GEMINI_API_KEY" in os.environ:
                del os.environ["GEMINI_API_KEY"]
            if "GOOGLE_API_KEY" in os.environ:
                del os.environ["GOOGLE_API_KEY"]
            st.success("Gemini key cleared!")
            st.rerun()
    else:
        st.info("💡 Add your Gemini API key in the sidebar to get started")

with col2:
    st.markdown("### OpenAI API")
    
    # Status display
    if st.session_state.openai_key_valid == True:
        st.success("✅ **Valid and Verified**")
    elif st.session_state.openai_key_valid == False:
        st.error("❌ **Invalid or Failed Validation**")
    elif st.session_state.openai_api_key:
        st.warning("⚠️ **Not Validated**")
    else:
        st.info("ℹ️ **Not Configured**")
    
    st.markdown("""
    **GPT-4o Vision**
    - High quality analysis
    - ~$0.03 per image
    - Good general purpose
    
    [Get your key →](https://platform.openai.com/api-keys)
    """)
    
    if st.session_state.openai_api_key:
        key_preview = st.session_state.openai_api_key[:8] + "..." + st.session_state.openai_api_key[-4:]
        st.code(key_preview)
        
        # Test button
        if st.button("🔍 Test OpenAI Key", use_container_width=True):
            with st.spinner("Testing API key..."):
                is_valid, msg = validate_api_key("openai", st.session_state.openai_api_key)
                st.session_state.openai_key_valid = is_valid
                if is_valid:
                    st.success(f"✅ {msg}")
                    set_api_keys()
                else:
                    st.error(f"❌ {msg}")
        
        if st.button("🗑️ Clear OpenAI Key", use_container_width=True):
            st.session_state.openai_api_key = ""
            st.session_state.openai_key_valid = None
            st.session_state.engine = None
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]
            st.success("OpenAI key cleared!")
            st.rerun()
    else:
        st.info("💡 Add your OpenAI API key in the sidebar to get started")

st.markdown("---")

# Validation Help
with st.expander("🆘 API Key Validation Help"):
    st.markdown("""
    ### Common Validation Issues
    
    **"Invalid API key"**
    - Double-check you copied the entire key
    - Make sure there are no extra spaces
    - Verify the key hasn't been revoked
    - For Gemini: Get a new key from [Google AI Studio](https://aistudio.google.com/app/apikey)
    - For OpenAI: Get a new key from [OpenAI Platform](https://platform.openai.com/api-keys)
    
    **"Quota exceeded"**
    - Your API key is valid but you've hit rate limits
    - For Gemini: Wait a few minutes (free tier: 15 requests/min)
    - For OpenAI: Add billing info or wait for quota reset
    
    **"Validation failed"**
    - Check your internet connection
    - Verify the API service is accessible
    - Try again in a few moments
    
    ### How Validation Works
    
    When you click "Validate", we:
    1. Strip whitespace from your API key
    2. Make a minimal API call to list available models
    3. Confirm the key works and has access
    4. Store the validation result
    
    **Note:** Validation does NOT make any charges to your account.
    """)

st.markdown("---")

# Analysis Configuration
st.markdown("## 🔬 Analysis Settings")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Default Model")
    default_model = st.selectbox(
        "Select default AI model",
        ["gemini", "openai", "stub"],
        index=0,
        help="This will be the default model for analysis"
    )
    
    if default_model != st.session_state.default_model:
        st.session_state.default_model = default_model
    
    st.markdown("### Vocabulary Normalization")
    normalize = st.checkbox(
        "Normalize fabric types, colors, and terms",
        value=st.session_state.normalize_vocab,
        help="Standardize terminology for consistency"
    )
    
    if normalize != st.session_state.normalize_vocab:
        st.session_state.normalize_vocab = normalize

with col2:
    st.markdown("### Default Analysis Passes")
    
    current_passes = st.session_state.default_passes
    default_pass_a = st.checkbox("Pass A - Global Analysis", value="A" in current_passes)
    default_pass_b = st.checkbox("Pass B - Construction", value="B" in current_passes)
    default_pass_c = st.checkbox("Pass C - Photography", value="C" in current_passes)
    
    passes = []
    if default_pass_a: passes.append("A")
    if default_pass_b: passes.append("B")
    if default_pass_c: passes.append("C")
    
    if passes != st.session_state.default_passes:
        st.session_state.default_passes = passes
    
    st.info(f"**{len(passes)} passes** will run by default")

st.markdown("---")

# Export Settings
st.markdown("## 💾 Export Settings")

col1, col2 = st.columns(2)

with col1:
    export_format = st.radio(
        "Default Export Format",
        ["JSON", "CSV", "Prompt Text"],
        horizontal=True,
        index=["JSON", "CSV", "Prompt Text"].index(st.session_state.default_export)
    )
    
    if export_format != st.session_state.default_export:
        st.session_state.default_export = export_format

with col2:
    include_confidence = st.checkbox(
        "Include Confidence Scores",
        value=st.session_state.include_confidence,
        help="Add confidence scores to exports (if available)"
    )
    
    if include_confidence != st.session_state.include_confidence:
        st.session_state.include_confidence = include_confidence

st.markdown("---")

# Data Management
st.markdown("## 🗄️ Data Management")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Analyzed Images", len(st.session_state.analyzed_images))
    
    if st.session_state.analyzed_images:
        if st.button("🗑️ Clear Analyzed", use_container_width=True):
            st.session_state.analyzed_images = []
            st.success("Cleared analyzed images!")
            st.rerun()

with col2:
    st.metric("Saved Collection", len(st.session_state.collection))
    
    if st.session_state.collection:
        if st.button("🗑️ Clear Collection", use_container_width=True):
            st.session_state.collection = []
            st.success("Cleared collection!")
            st.rerun()

with col3:
    total = len(st.session_state.analyzed_images) + len(st.session_state.collection)
    st.metric("Total Records", total)
    
    if total > 0:
        if st.button("🗑️ Clear All Data", use_container_width=True, type="secondary"):
            st.session_state.analyzed_images = []
            st.session_state.collection = []
            st.session_state.engine = None
            st.success("Cleared all data!")
            st.rerun()

st.markdown("---")

# System Information
st.markdown("## 🔧 System Information")

with st.expander("Backend Status"):
    try:
        from src.visual_descriptor.engine import Engine
        
        # Try to show which backend is loaded
        if st.session_state.engine:
            backend = type(st.session_state.engine.model).__name__
            st.success(f"**Active Backend:** {backend}")
        else:
            st.info("**Status:** No engine loaded yet")
        
        st.markdown("**Available Backends:**")
        st.markdown("- ✅ Gemini Flash 2.5")
        st.markdown("- ✅ OpenAI GPT-4o")
        st.markdown("- ✅ Stub (testing)")
        
    except Exception as e:
        st.error(f"Backend Error: {str(e)}")

with st.expander("Environment Info"):
    st.markdown("**Python Environment:**")
    st.code(f"""
Python: 3.11+
Streamlit: {st.__version__}
Model: {st.session_state.default_model}
Normalize: {st.session_state.normalize_vocab}
    """)
    
    st.markdown("**Environment Variables:**")
    st.code(f"""
GEMINI_API_KEY: {'Set' if os.getenv('GEMINI_API_KEY') else 'Not set'}
OPENAI_API_KEY: {'Set' if os.getenv('OPENAI_API_KEY') else 'Not set'}
    """)
    
    st.markdown("**Validation Status:**")
    st.code(f"""
Gemini Key Valid: {st.session_state.gemini_key_valid}
OpenAI Key Valid: {st.session_state.openai_key_valid}
    """)

st.markdown("---")

# About
st.markdown("## ℹ️ About")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Fashion Descriptor AI**  
    Version 2.0.0
    
    AI-powered fashion image analysis using state-of-the-art 
    computer vision models.
    
    **Key Features:**
    - 50+ structured data fields
    - Multi-pass analysis system
    - Color & pattern detection
    - Construction analysis
    - Multiple export formats
    - API key validation
    """)

with col2:
    st.markdown("""
    **Powered By:**
    - Gemini Flash 2.5
    - OpenAI GPT-4o
    
    **Resources:**
    - [Documentation](#)
    - [GitHub Repository](#)
    - [Report Issues](#)
                
    **License:** MIT

    **Developer:** Deborah Imafidon                        
    """)

st.markdown("---")

# Reset button
if st.button("🔄 Reset All Settings to Defaults", type="secondary", use_container_width=True):
    # Reset to defaults
    st.session_state.default_model = "gemini"
    st.session_state.normalize_vocab = True
    st.session_state.default_passes = ["A", "B", "C"]
    st.session_state.default_export = "JSON"
    st.session_state.include_confidence = False
    
    st.success("✅ Settings reset to defaults!")
    st.rerun()

st.caption("Made with ❤️ by Deborah Imafidon")