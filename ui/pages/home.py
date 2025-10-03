import streamlit as st

def show():
    """Home page with overview and features"""
    
    # Hero section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("## Welcome to Visual Descriptor AI")
        st.markdown("""
        Transform fashion images into structured, actionable data using state-of-the-art 
        computer vision. Perfect for:
        
        - **E-commerce**: Auto-generate product descriptions
        - **Design Studios**: Analyze competitor collections  
        - **Fashion Tech**: Build recommendation engines
        - **Research**: Dataset annotation at scale
        """)
        
        if st.button("🚀 Start Analyzing", type="primary", use_container_width=True):
            st.session_state["page"] = "🔍 Analyze"
            st.rerun()
    
    with col2:
        st.image("https://via.placeholder.com/400x300/667eea/ffffff?text=Fashion+AI", 
                 use_container_width=True)
    
    st.markdown("---")
    
    # Features grid
    st.markdown("## 🎯 Key Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>🎨 Fabric Analysis</h3>
            <p>Identify material type, texture, weight, and finish with precision</p>
            <ul>
                <li>Jersey, denim, wool, silk</li>
                <li>Smooth, ribbed, quilted</li>
                <li>Light, medium, heavy</li>
                <li>Matte, semi-gloss, glossy</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>🧵 Construction Details</h3>
            <p>Detect seams, stitching, closures, and finishing techniques</p>
            <ul>
                <li>Princess seams, flat-felled</li>
                <li>Contrast topstitching</li>
                <li>Exposed zippers, buttons</li>
                <li>Hem types and finishes</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>🌈 Color & Patterns</h3>
            <p>Extract color palettes and identify patterns automatically</p>
            <ul>
                <li>Primary & secondary colors</li>
                <li>Polka dots, stripes, plaid</li>
                <li>Pattern foreground/background</li>
                <li>Accent colors (buttons, zippers)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # How it works
    st.markdown("## 🔬 How It Works")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        **1. Upload** 📤  
        Drop your fashion images or upload from your device
        """)
    
    with col2:
        st.markdown("""
        **2. Analyze** 🤖  
        AI processes through multiple analysis passes
        """)
    
    with col3:
        st.markdown("""
        **3. Review** 👀  
        Explore structured data and visualizations
        """)
    
    with col4:
        st.markdown("""
        **4. Export** 💾  
        Download JSON, CSV, or prompt text
        """)
    
    st.markdown("---")
    
    # Stats
    st.markdown("## 📊 Capabilities")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-container">
            <h2>50+</h2>
            <p>Data Fields</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-container">
            <h2>3</h2>
            <p>Analysis Passes</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-container">
            <h2>2-4s</h2>
            <p>Per Image</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-container">
            <h2>100%</h2>
            <p>Accuracy Goal</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # CTA
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Ready to analyze your fashion images?")
        if st.button("🎯 Go to Analyze Page", type="primary", use_container_width=True):
            st.session_state["page"] = "🔍 Analyze"
            st.rerun()