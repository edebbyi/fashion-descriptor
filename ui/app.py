import streamlit as st
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="Visual Descriptor AI",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== GLOBAL CSS ====================
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
    }
    
    h1, h2, h3 {
        color: #e0e0e0;
        font-weight: 600;
    }
    
    .stButton>button {
        width: 100%;
    }
    
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85em;
        font-weight: 600;
        margin: 2px;
    }
    
    .badge-primary {
        background: rgba(100, 100, 255, 0.2);
        color: #b0b0ff;
        border: 1px solid rgba(100, 100, 255, 0.3);
    }
    
    .badge-secondary {
        background: rgba(200, 100, 200, 0.2);
        color: #ffb0ff;
        border: 1px solid rgba(200, 100, 200, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# ==================== SHARED STATE INITIALIZATION ====================
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

# ==================== SHARED FUNCTIONS ====================
def set_api_keys():
    """Set API keys as environment variables"""
    if st.session_state.gemini_api_key:
        os.environ["GEMINI_API_KEY"] = st.session_state.gemini_api_key
        os.environ["GOOGLE_API_KEY"] = st.session_state.gemini_api_key
    
    if st.session_state.openai_api_key:
        os.environ["OPENAI_API_KEY"] = st.session_state.openai_api_key

# ==================== SIDEBAR (SHARED ACROSS ALL PAGES) ====================
with st.sidebar:
    st.markdown("# 👗 Visual Descriptor")
    st.markdown("*Fashion Intelligence AI*")
    st.markdown("---")
    
    # API Key Configuration
    st.markdown("### 🔑 API Keys")
    
    with st.expander("Configure API Keys", expanded=not (st.session_state.gemini_api_key or st.session_state.openai_api_key)):
        st.markdown("**Gemini API Key**")
        st.caption("Get from: [Google AI Studio](https://aistudio.google.com/app/apikey)")
        gemini_key = st.text_input(
            "Gemini Key",
            value=st.session_state.gemini_api_key,
            type="password",
            key="gemini_key_input",
            label_visibility="collapsed"
        )
        if gemini_key != st.session_state.gemini_api_key:
            st.session_state.gemini_api_key = gemini_key
            st.session_state.engine = None
            set_api_keys()
        
        st.markdown("**OpenAI API Key**")
        st.caption("Get from: [OpenAI Platform](https://platform.openai.com/api-keys)")
        openai_key = st.text_input(
            "OpenAI Key",
            value=st.session_state.openai_api_key,
            type="password",
            key="openai_key_input",
            label_visibility="collapsed"
        )
        if openai_key != st.session_state.openai_api_key:
            st.session_state.openai_api_key = openai_key
            st.session_state.engine = None
            set_api_keys()
        
        # Status indicators
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.gemini_api_key:
                st.success("✅ Gemini")
            else:
                st.warning("⚠️ Gemini")
        
        with col2:
            if st.session_state.openai_api_key:
                st.success("✅ OpenAI")
            else:
                st.warning("⚠️ OpenAI")
    
    st.markdown("---")
    
    # Collection Stats
    st.markdown("### 📊 Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Analyzed", len(st.session_state.analyzed_images))
    with col2:
        st.metric("Saved", len(st.session_state.collection))
    
    st.markdown("---")
    
    # Clear button
    if st.button("🗑️ Clear All Data", use_container_width=True):
        st.session_state.analyzed_images = []
        st.session_state.collection = []
        st.session_state.engine = None
        st.success("Cleared!")
        st.rerun()

# ==================== MAIN CONTENT ====================
st.title("🎨 Visual Descriptor AI")
st.markdown("*AI-powered fashion image analysis for creative directors*")
st.markdown("---")

# Welcome message for home page
st.markdown("""
## Welcome! 👋

Select a page from the sidebar to get started:

- **🏠 home** - Overview and features
- **🔍 analyze** - Upload and analyze fashion images  
- **📊 gallery** - View and compare analyzed images
- **⚙️ settings** - Configure preferences

### Quick Start

1. **Add API Key**: Click "Configure API Keys" in the sidebar
2. **Analyze Images**: Go to the analyze page
3. **View Results**: Check gallery for comparisons
4. **Export Data**: Download JSON, CSV, or prompts

---

💡 **Tip**: Make sure to add your Gemini or OpenAI API key before analyzing images!
""")

# Show API key status
if not st.session_state.gemini_api_key and not st.session_state.openai_api_key:
    st.warning("⚠️ **No API keys configured!** Add your keys in the sidebar to start analyzing images.")
else:
    st.success("✅ **API keys configured!** Ready to analyze fashion images.")