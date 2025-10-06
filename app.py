import streamlit as st
import os
import sys
from pathlib import Path

# Add src to path
repo_root = Path(__file__).parent.resolve()
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="Fashion Descriptor AI",
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

# Import after page config
from shared_init import init_session_state, set_api_keys, validate_api_key, has_valid_api_key

# Initialize session state
init_session_state()

# ==================== SIDEBAR (SHARED ACROSS ALL PAGES) ====================
with st.sidebar:
    st.markdown("# 👗 Fashion Descriptor")
    st.markdown("*Fashion Intelligence AI*")
    st.markdown("---")
    
    # API Key Configuration
    st.markdown("### 🔑 API Keys")
    
    with st.expander("Configure API Keys", expanded=not has_valid_api_key()):
        st.markdown("**Gemini API Key**")
        st.caption("Get from: [Google AI Studio](https://aistudio.google.com/app/apikey)")
        
        gemini_key = st.text_input(
            "Gemini Key",
            value=st.session_state.gemini_api_key,
            type="password",
            key="gemini_key_input",
            label_visibility="collapsed"
        )
        
        # Validate button for Gemini
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Validate", key="validate_gemini", use_container_width=True):
                if gemini_key.strip():
                    with st.spinner("Validating..."):
                        is_valid, msg = validate_api_key("gemini", gemini_key)
                        st.session_state.gemini_key_valid = is_valid
                        if is_valid:
                            st.session_state.gemini_api_key = gemini_key.strip()
                            st.session_state.engine = None
                            set_api_keys()
                            st.success(msg)
                        else:
                            st.error(msg)
                else:
                    st.error("Please enter an API key first")
        
        with col2:
            if gemini_key != st.session_state.gemini_api_key and gemini_key.strip():
                if st.button("💾 Save", key="save_gemini", use_container_width=True):
                    st.session_state.gemini_api_key = gemini_key.strip()
                    st.session_state.gemini_key_valid = None  # Reset validation
                    st.session_state.engine = None
                    set_api_keys()
                    st.info("Saved! Click 'Validate' to verify.")
        
        # Show validation status
        #if st.session_state.gemini_key_valid == True:
          #  st.success("✅ Gemini API key is valid")
       #elif st.session_state.gemini_key_valid == False:
       #     st.error("❌ Gemini API key is invalid")
       # elif st.session_state.gemini_api_key:
       #     st.warning("⚠️ API key not validated yet")
        
        st.markdown("---")
        
        st.markdown("**OpenAI API Key**")
        st.caption("Get from: [OpenAI Platform](https://platform.openai.com/api-keys)")
        
        openai_key = st.text_input(
            "OpenAI Key",
            value=st.session_state.openai_api_key,
            type="password",
            key="openai_key_input",
            label_visibility="collapsed"
        )
        
        # Validate button for OpenAI
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Validate", key="validate_openai", use_container_width=True):
                if openai_key.strip():
                    with st.spinner("Validating..."):
                        is_valid, msg = validate_api_key("openai", openai_key)
                        st.session_state.openai_key_valid = is_valid
                        if is_valid:
                            st.session_state.openai_api_key = openai_key.strip()
                            st.session_state.engine = None
                            set_api_keys()
                            st.success(msg)
                        else:
                            st.error(msg)
                else:
                    st.error("Please enter an API key first")
        
        with col2:
            if openai_key != st.session_state.openai_api_key and openai_key.strip():
                if st.button("💾 Save", key="save_openai", use_container_width=True):
                    st.session_state.openai_api_key = openai_key.strip()
                    st.session_state.openai_key_valid = None  # Reset validation
                    st.session_state.engine = None
                    set_api_keys()
                    st.info("Saved! Click 'Validate' to verify.")
        
        # Show validation status
        #if st.session_state.openai_key_valid == True:
          #  st.success("✅ OpenAI API key is valid")
        #elif st.session_state.openai_key_valid == False:
        #    st.error("❌ OpenAI API key is invalid")
       # elif st.session_state.openai_api_key:
        #    st.warning("⚠️ API key not validated yet")
    
    # Overall status indicators (outside expander)
    st.markdown("**Status:**")
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.gemini_key_valid == True:
            st.success("✅ Gemini")
        else:
            st.error("❌ Gemini")
    
    with col2:
        if st.session_state.openai_key_valid == True:
            st.success("✅ OpenAI")
        else:
            st.error("❌ OpenAI")
    
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
st.title("🎨 Fashion Descriptor AI")
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

1. **Add API Key**: Click "App >> Configure API Keys" in the sidebar
2. **Validate Key**: Click the validate button to verify your key works
3. **Analyze Images**: Go to the analyze page
4. **View Results**: Check gallery for comparisons
5. **Export Data**: Download JSON, CSV, or prompts

---

💡 **Tip**: Make sure to validate your API key before analyzing images!
""")

# Show API key status
if not has_valid_api_key():
    st.error("""
    ⚠️ **No valid API keys configured!** 
    
    Please add and validate your API key in the sidebar:
    1. Click "App >> Configure API Keys" above
    2. Enter your Gemini or OpenAI API key
    3. Click "Validate" to verify it works
    4. Once validated, you can start analyzing images
    """)
else:
    st.success("✅ **API keys validated!** Ready to analyze fashion images.")