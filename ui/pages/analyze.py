import streamlit as st
from pathlib import Path
import time
from PIL import Image
import io
import base64
import sys
import os

import sys
print("DEBUG: sys.path =", sys.path)
print("DEBUG: Current file =", __file__)

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
print("DEBUG: Added to path =", str(Path(__file__).parent.parent.parent))
# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.visual_descriptor.engine import Engine

# ==================== HELPER FUNCTIONS ====================
def set_api_keys():
    """Set API keys as environment variables"""
    if st.session_state.gemini_api_key:
        os.environ["GEMINI_API_KEY"] = st.session_state.gemini_api_key
        os.environ["GOOGLE_API_KEY"] = st.session_state.gemini_api_key
    
    if st.session_state.openai_api_key:
        os.environ["OPENAI_API_KEY"] = st.session_state.openai_api_key

def init_engine(model: str = "gemini"):
    """Initialize or get existing engine"""
    set_api_keys()
    with st.spinner(f"Loading {model.upper()} vision model..."):
        try:
            st.session_state.engine = Engine(model=model, normalize=True)
            return st.session_state.engine
        except Exception as e:
            st.error(f"Failed to initialize engine: {str(e)}")
            return None

def image_to_base64(image: Image.Image) -> str:
    """Convert PIL Image to base64 string"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def analyze_image(image_file, passes: list, engine) -> dict:
    """Analyze a single image"""
    # Save temporarily
    temp_path = Path("/tmp") / image_file.name
    image_bytes = image_file.read()
    temp_path.write_bytes(image_bytes)
    
    # Load image and convert to base64
    img = Image.open(io.BytesIO(image_bytes))
    img_base64 = image_to_base64(img)
    
    # Analyze
    record = engine.describe_image(temp_path, passes=passes)
    record["_image_file"] = image_file.name
    record["_image_base64"] = img_base64
    
    return record

def create_badge(text: str, badge_type: str = "primary") -> str:
    """Create a styled badge"""
    return f'<span class="badge badge-{badge_type}">{text}</span>'

# ==================== MAIN PAGE ====================
st.title("🔍 Analyze Images")
st.markdown("*Upload fashion images for AI-powered analysis*")
st.markdown("---")

# Settings section
col1, col2, col3 = st.columns(3)

with col1:
    model_choice = st.selectbox(
        "AI Model",
        ["gemini", "openai", "stub"],
        index=0,
        help="Gemini Flash 2.5 (recommended) or OpenAI GPT-4o"
    )
    
    # Check if API key is available
    if model_choice == "gemini" and not st.session_state.gemini_api_key:
        st.error("⚠️ Gemini API key required!")
    elif model_choice == "openai" and not st.session_state.openai_api_key:
        st.error("⚠️ OpenAI API key required!")

with col2:
    pass_a = st.checkbox("Pass A - Global", value=True, help="Garment type, fabric, colors")
    pass_b = st.checkbox("Pass B - Construction", value=True, help="Seams, stitching, closures")
    pass_c = st.checkbox("Pass C - Photography", value=True, help="Pose, lighting, camera")

with col3:
    passes = []
    if pass_a: passes.append("A")
    if pass_b: passes.append("B")
    if pass_c: passes.append("C")
    
    st.info(f"**{len(passes)} passes selected**")

st.markdown("---")

# Upload section
uploaded_files = st.file_uploader(
    "📤 Upload Fashion Images",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True,
    help="Upload one or more fashion images for analysis"
)

# Analyze button
can_analyze = uploaded_files and (
    (model_choice == "gemini" and st.session_state.gemini_api_key) or
    (model_choice == "openai" and st.session_state.openai_api_key) or
    (model_choice == "stub")
)

col1, col2 = st.columns([3, 1])

with col1:
    analyze_btn = st.button(
        "🚀 Analyze Images",
        type="primary",
        disabled=not can_analyze,
        use_container_width=True
    )

with col2:
    if st.session_state.analyzed_images:
        if st.button("💾 Save to Gallery", use_container_width=True):
            # Get existing image IDs in gallery
            existing_ids = {r.get("image_id") or r.get("_image_file") 
                          for r in st.session_state.collection}
            
            # Add only new images
            added = 0
            skipped = 0
            for record in st.session_state.analyzed_images:
                record_id = record.get("image_id") or record.get("_image_file")
                if record_id not in existing_ids:
                    st.session_state.collection.append(record)
                    existing_ids.add(record_id)
                    added += 1
                else:
                    skipped += 1
            
            # Clear analyzed images after saving
            st.session_state.analyzed_images = []
            
            # Show appropriate message
            if added > 0 and skipped > 0:
                st.success(f"✅ Saved {added} new image(s), skipped {skipped} duplicate(s)")
            elif added > 0:
                st.success(f"✅ Saved {added} image(s) to gallery!")
            else:
                st.info(f"ℹ️ All {skipped} image(s) already in gallery")
            
            st.rerun()

if not can_analyze and uploaded_files:
    st.warning("⚠️ Please add an API key in the sidebar before analyzing.")

# Analysis execution
if analyze_btn and uploaded_files:
    engine = init_engine(model_choice)
    
    if engine is None:
        st.error("Failed to initialize engine. Check your API keys.")
    else:
        # Clear previous results
        st.session_state.analyzed_images = []
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Analyze each image
        for idx, file in enumerate(uploaded_files):
            status_text.text(f"Analyzing {file.name}... ({idx + 1}/{len(uploaded_files)})")
            
            try:
                record = analyze_image(file, passes, engine)
                st.session_state.analyzed_images.append(record)
            except Exception as e:
                st.error(f"Error analyzing {file.name}: {str(e)}")
            
            progress_bar.progress((idx + 1) / len(uploaded_files))
        
        # Cleanup progress indicators
        status_text.empty()
        progress_bar.empty()
        
        st.success(f"✅ Successfully analyzed {len(st.session_state.analyzed_images)} image(s)!")
        st.balloons()

# Display results
if st.session_state.analyzed_images:
    st.markdown("---")
    st.markdown("## 📊 Analysis Results")
    st.info(f"👇 **{len(st.session_state.analyzed_images)} image(s) analyzed** - Click 'Save to Gallery' above to keep them permanently")
    
    # Grid view
    cols = st.columns(3)
    
    for idx, record in enumerate(st.session_state.analyzed_images):
        with cols[idx % 3]:
            # Image
            if record.get("_image_base64"):
                st.markdown(
                    f'<img src="{record["_image_base64"]}" style="width:100%; border-radius:8px; margin-bottom:10px;">',
                    unsafe_allow_html=True
                )
            else:
                st.info("Image preview unavailable")
            
            # Info
            st.markdown(f"**{record.get('image_id', 'Unknown')}**")
            
            garment_type = record.get('garment_type', 'Unknown')
            st.caption(f"*{garment_type}*")
            
            # Badges
            primary_color = record.get('color_primary') or (
                record.get('color_palette', [''])[0] if record.get('color_palette') else ''
            )
            if primary_color:
                st.markdown(create_badge(primary_color.title(), "primary"), unsafe_allow_html=True)
            
            fabric_type = record.get('fabric', {}).get('type')
            if fabric_type:
                st.markdown(create_badge(fabric_type.title(), "secondary"), unsafe_allow_html=True)
            
            # Details expander
            with st.expander("View Details"):
                st.markdown(f"**Silhouette:** {record.get('silhouette', 'N/A')}")
                st.markdown(f"**Fit:** {record.get('fit_and_drape', 'N/A')}")
                
                fabric = record.get('fabric', {})
                if isinstance(fabric, dict):
                    st.markdown(f"**Fabric:** {fabric.get('type', 'N/A')} ({fabric.get('texture', 'N/A')})")
                
                if record.get('prompt_text'):
                    st.markdown("**AI Description:**")
                    st.caption(record['prompt_text'])
else:
    st.info("👆 Upload images above and click 'Analyze Images' to get started!")
