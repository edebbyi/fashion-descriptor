import streamlit as st
import os

def show():
    """Settings page for configuration"""
    
    st.markdown("## ⚙️ Settings")
    st.markdown("Configure your Visual Descriptor AI preferences")
    
    st.markdown("---")
    
    # Model settings
    st.markdown("### 🤖 AI Model Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        model_choice = st.selectbox(
            "Vision Model Backend",
            ["gemini", "openai", "stub"],
            index=0,
            help="Select which AI model to use for analysis"
        )
        
        st.session_state["vd_model"] = model_choice
        
        # Model info
        if model_choice == "gemini":
            st.info("""
            **Gemini Flash 2.5**
            - Best for fashion analysis
            - FREE with rate limits
            - 2-4 seconds per image
            - Superior color/construction detection
            """)
        elif model_choice == "openai":
            st.info("""
            **GPT-4o Vision**
            - High quality analysis
            - ~$0.03 per image
            - 3-5 seconds per image
            - Good general purpose
            """)
        else:
            st.warning("""
            **Stub (Testing Only)**
            - Basic heuristic analysis
            - Free, instant
            - Limited accuracy
            - For development/testing
            """)
    
    with col2:
        normalize = st.checkbox(
            "Normalize Vocabulary",
            value=True,
            help="Standardize fabric types, colors, and other terms"
        )
        
        st.session_state["normalize_vocab"] = normalize
    
    st.markdown("---")
    
    # API Keys
    st.markdown("### 🔑 API Keys")
    
    st.markdown("""
    Configure your API keys for the vision models. These are stored in environment 
    variables and **not** persisted in the app.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        gemini_key_set = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
        if gemini_key_set:
            st.success("✅ Gemini API Key is set")
        else:
            st.warning("⚠️ Gemini API Key not set")
            st.markdown("Get your key: [Google AI Studio](https://aistudio.google.com/app/apikey)")
    
    with col2:
        openai_key_set = bool(os.getenv("OPENAI_API_KEY"))
        if openai_key_set:
            st.success("✅ OpenAI API Key is set")
        else:
            st.warning("⚠️ OpenAI API Key not set")
            st.markdown("Get your key: [OpenAI Platform](https://platform.openai.com/api-keys)")
    
    st.markdown("---")
    
    # Analysis passes
    st.markdown("### 🔬 Analysis Passes")
    
    st.markdown("""
    The visual descriptor uses a multi-pass analysis system for comprehensive results:
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **Pass A: Global**
        - Garment type & silhouette
        - Fabric identification
        - Colors & patterns
        - Overall composition
        """)
    
    with col2:
        st.markdown("""
        **Pass B: Construction**
        - Seam types & placement
        - Stitching details
        - Closures & hardware
        - Finishing techniques
        """)
    
    with col3:
        st.markdown("""
        **Pass C: Presentation**
        - Model pose & framing
        - Camera angle & view
        - Lighting setup
        - Background & mood
        """)
    
    st.markdown("---")
    
    # Export settings
    st.markdown("### 💾 Export Settings")
    
    export_format = st.radio(
        "Default Export Format",
        ["JSON", "CSV", "Prompt Text"],
        horizontal=True
    )
    
    st.session_state["default_export"] = export_format
    
    include_confidence = st.checkbox(
        "Include Confidence Scores",
        value=False,
        help="Add confidence scores to exports (if available)"
    )
    
    st.session_state["include_confidence"] = include_confidence
    
    st.markdown("---")
    
    # UI preferences
    st.markdown("### 🎨 Interface Preferences")
    
    col1, col2 = st.columns(2)
    
    with col1:
        auto_expand = st.checkbox(
            "Auto-expand Result Sections",
            value=True,
            help="Automatically expand details in analysis results"
        )
        st.session_state["auto_expand"] = auto_expand
    
    with col2:
        show_processing_time = st.checkbox(
            "Show Processing Time",
            value=True,
            help="Display analysis processing time"
        )
        st.session_state["show_processing_time"] = show_processing_time
    
    st.markdown("---")
    
    # About
    st.markdown("### ℹ️ About Visual Descriptor AI")
    
    st.markdown("""
    **Version:** 2.0.0  
    **Backend:** Gemini Flash 2.5 / GPT-4o  
    **License:** MIT
    
    This tool uses advanced computer vision to analyze fashion images and extract 
    detailed technical specifications. Perfect for e-commerce, design studios, and 
    fashion tech applications.
    
    **Key Features:**
    - 50+ structured data fields
    - Multi-pass analysis system
    - Color & pattern detection
    - Construction analysis
    - Export to multiple formats
    
    **Documentation:** [GitHub Repository](#)  
    **Support:** [Report Issues](#)
    """)
    
    st.markdown("---")
    
    # System info
    with st.expander("🔧 System Information"):
        st.markdown("#### Backend Status")
        
        try:
            from src.visual_descriptor.engine import Engine
            engine = Engine(model=st.session_state.get("vd_model", "gemini"))
            backend = type(engine.model).__name__
            st.success(f"Active Backend: {backend}")
        except Exception as e:
            st.error(f"Backend Error: {str(e)}")
        
        st.markdown("#### Environment")
        st.code(f"""
Python: 3.11+
Streamlit: {st.__version__}
Model: {st.session_state.get('vd_model', 'gemini')}
Normalize: {st.session_state.get('normalize_vocab', True)}
        """)
    
    # Reset button
    st.markdown("---")
    if st.button("🔄 Reset to Defaults", type="secondary"):
        # Clear session state
        keys_to_clear = ["vd_model", "normalize_vocab", "default_export", 
                        "include_confidence", "auto_expand", "show_processing_time"]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.success("✅ Settings reset to defaults")
        st.rerun()