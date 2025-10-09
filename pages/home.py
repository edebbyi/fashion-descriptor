# ui/pages/home.py
import streamlit as st
from pathlib import Path
import sys

#root/pages/analyze.py
repo_root = Path(__file__).parent.parent.resolve()
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from shared_init import init_session_state

# Initialize session state
init_session_state()

st.title("🏠 Welcome to Fashion Descriptor AI")
st.markdown("*AI-powered fashion image analysis for creative directors*")
st.markdown("---")

# Hero section
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    ## Transform Fashion Images into Data
    
    Use state-of-the-art computer vision to extract detailed technical specifications 
    from fashion photography. Perfect for:
    
    - **E-commerce Teams**: Auto-generate product descriptions at scale
    - **Design Studios**: Analyze competitor collections and trends  
    - **Fashion Tech**: Build recommendation and discovery engines
    - **Research**: Create annotated datasets for machine learning
    """)
    
    if st.button("🚀 Start Analyzing Now", type="primary", use_container_width=True):
        st.switch_page("pages/analyze.py")

with col2:
    st.info("""
    ### Quick Stats
    
    **50+** Data Fields  
    **3** Analysis Passes  
    **2-4s** Per Image  
    **FREE** with Gemini
    """)

st.markdown("---")

# Features
st.markdown("## 🎯 Key Features")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 🎨 Fabric Analysis
    
    Identify materials with precision:
    
    - **Type**: Jersey, denim, wool, silk, satin
    - **Texture**: Smooth, ribbed, quilted, brushed
    - **Weight**: Light, medium, heavy
    - **Finish**: Matte, semi-gloss, glossy
    """)

with col2:
    st.markdown("""
    ### 🧵 Construction Details
    
    Detect garment construction:
    
    - **Seams**: Princess, flat-felled, panel
    - **Stitching**: Topstitch, contrast, decorative
    - **Closures**: Zippers, buttons, drawstrings
    - **Hems**: Raw edge, rolled, topstitched
    """)

with col3:
    st.markdown("""
    ### 🌈 Colors & Patterns
    
    Extract color intelligence:
    
    - **Primary & secondary** colors
    - **Pattern detection**: Polka dots, stripes, plaid
    - **Foreground/background** separation
    - **Accent colors**: Hardware, stitching, trim
    """)

st.markdown("---")

# How it works
st.markdown("## 🔬 How It Works")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    ### 1. Upload 📤
    
    Drop your fashion images or upload from device
    """)

with col2:
    st.markdown("""
    ### 2. Analyze 🤖
    
    AI processes through 3 analysis passes
    """)

with col3:
    st.markdown("""
    ### 3. Review 👀
    
    Explore structured data and visualizations
    """)

with col4:
    st.markdown("""
    ### 4. Export 💾
    
    Download JSON, CSV, or AI training prompts
    """)

st.markdown("---")

# Analysis passes
st.markdown("## 📋 Three-Pass Analysis System")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### Pass A: Global Analysis
    
    **Comprehensive overview:**
    - Garment type & silhouette
    - Fabric identification
    - Color palette & patterns
    - Overall composition
    - Footwear detection
    """)

with col2:
    st.markdown("""
    ### Pass B: Construction
    
    **Technical details:**
    - Seam types & placement
    - Stitching techniques & colors
    - Closures & hardware
    - Hem finishes
    - Top/bottom separation
    """)

with col3:
    st.markdown("""
    ### Pass C: Presentation
    
    **Photography analysis:**
    - Model pose & framing
    - Camera angle & view
    - Lighting setup & mood
    - Background & environment
    - Photo style classification
    """)

st.markdown("---")

# API Keys section
st.markdown("## 🔑 Getting Started")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### Gemini Flash 2.5 (Recommended)
    
    **Best for fashion analysis:**
    - ⭐⭐⭐⭐⭐ Quality
    - **FREE** with rate limits
    - 2-4 seconds per image
    - Superior color/construction detection
    
    **Get your key:**  
    [Google AI Studio →](https://aistudio.google.com/app/apikey)
    """)
    
    if not st.session_state.gemini_api_key:
        st.warning("⚠️ No Gemini API key set")
    else:
        st.success("✅ Gemini API key configured")

with col2:
    st.markdown("""
    ### OpenAI GPT-4o (Alternative)
    
    **High quality general purpose:**
    - ⭐⭐⭐⭐ Quality
    - ~$0.03 per image
    - 3-5 seconds per image
    - Good overall performance
    
    **Get your key:**  
    [OpenAI Platform →](https://platform.openai.com/api-keys)
    """)
    
    if not st.session_state.openai_api_key:
        st.warning("⚠️ No OpenAI API key set")
    else:
        st.success("✅ OpenAI API key configured")

if not st.session_state.gemini_api_key and not st.session_state.openai_api_key:
    st.info("💡 **Tip**: Add your API key in the sidebar to start analyzing images!")

st.markdown("---")

# CTA
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("### Ready to analyze your fashion images?")
    if st.button("🎯 Go to Analyze Page", type="primary", use_container_width=True):
        st.switch_page("pages/analyze.py")

st.markdown("---")

# Footer
st.caption("""
**Fashion Descriptor AI** - Powered by Gemini Flash 2.5 & GPT-4o  
Built for fashion tech innovators 👗✨
""")