import streamlit as st
from pathlib import Path
import json
import pandas as pd
from PIL import Image
import io
from typing import Dict, Any, List
import time
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.visual_descriptor.engine import Engine
from src.visual_descriptor.export_csv_prompt import prompt_line, CSVExporter

# ==================== CONFIG ====================
st.set_page_config(
    page_title="Visual Descriptor — Fashion Intelligence",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "AI-powered fashion image analysis for designers and creative directors"
    }
)

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    /* Main theme */
    .main {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
    }
    
    /* Headers */
    h1 {
        color: #ffffff;
        font-weight: 700;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #ffffff 0%, #a0a0a0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    h2, h3 {
        color: #e0e0e0;
        font-weight: 600;
    }
    
    /* Cards */
    .insight-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        backdrop-filter: blur(10px);
    }
    
    .metric-card {
        background: linear-gradient(135deg, rgba(80, 80, 200, 0.1) 0%, rgba(200, 80, 200, 0.1) 100%);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 8px;
        padding: 15px;
        text-align: center;
    }
    
    /* Prompt text styling */
    .prompt-text {
        background: rgba(100, 100, 255, 0.05);
        border-left: 3px solid #6060ff;
        padding: 15px;
        border-radius: 4px;
        font-family: 'Monaco', monospace;
        font-size: 0.9em;
        line-height: 1.6;
        color: #d0d0d0;
    }
    
    /* Badges */
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

# ==================== STATE MANAGEMENT ====================
if "analyzed_images" not in st.session_state:
    st.session_state.analyzed_images = []

if "collection" not in st.session_state:
    st.session_state.collection = []

if "engine" not in st.session_state:
    st.session_state.engine = None

# ==================== HELPER FUNCTIONS ====================
def init_engine(model: str = "gemini"):
    """Initialize or get existing engine"""
    if st.session_state.engine is None:
        with st.spinner(f"Loading {model.upper()} vision model..."):
            st.session_state.engine = Engine(model=model, normalize=True)
    return st.session_state.engine

def create_badge(text: str, badge_type: str = "primary") -> str:
    """Create a styled badge"""
    return f'<span class="badge badge-{badge_type}">{text}</span>'

def analyze_image(image_file, passes: List[str], engine) -> Dict[str, Any]:
    """Analyze a single image"""
    # Save temporarily
    temp_path = Path("/tmp") / image_file.name
    temp_path.write_bytes(image_file.read())
    
    # Analyze
    with st.spinner(f"Analyzing {image_file.name}..."):
        record = engine.describe_image(temp_path, passes=passes)
        record["_image_file"] = image_file.name
        record["_image_path"] = str(temp_path)
    
    return record

# ==================== MAIN APP ====================
def main():
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        
        # Model selection
        model_choice = st.selectbox(
            "Vision Model",
            ["gemini", "openai", "stub"],
            index=0,
            help="Gemini Flash 2.5 (recommended) or OpenAI GPT-4o"
        )
        
        # Pass selection
        st.markdown("### 🔍 Analysis Passes")
        pass_a = st.checkbox("**Pass A** — Global Analysis", value=True, help="Garment type, fabric, colors, silhouette")
        pass_b = st.checkbox("**Pass B** — Construction", value=True, help="Seams, stitching, closures, hems")
        pass_c = st.checkbox("**Pass C** — Photography", value=True, help="Pose, lighting, camera work")
        
        passes = []
        if pass_a: passes.append("A")
        if pass_b: passes.append("B")
        if pass_c: passes.append("C")
        
        st.markdown("---")
        st.markdown("### 📊 Collection Stats")
        st.metric("Analyzed Images", len(st.session_state.analyzed_images))
        st.metric("Saved to Collection", len(st.session_state.collection))
        
        if st.button("🗑️ Clear All", help="Clear analyzed images and collection"):
            st.session_state.analyzed_images = []
            st.session_state.collection = []
            st.rerun()
    
    # Main content
    st.title("🎨 Visual Descriptor — Fashion Intelligence")
    st.markdown("*AI-powered garment analysis for designers and creative directors*")
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs([
        "📸 Analyze Images",
        "🔬 Detailed View", 
        "📥 Export Hub"
    ])
    
    # ==================== TAB 1: ANALYZE IMAGES ====================
    with tab1:
        st.markdown("## Upload & Analyze")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded_files = st.file_uploader(
                "Upload fashion images",
                type=["jpg", "jpeg", "png", "webp"],
                accept_multiple_files=True,
                help="Upload one or more fashion images for AI analysis"
            )
        
        with col2:
            st.markdown("### Quick Actions")
            analyze_btn = st.button("🚀 Analyze Images", type="primary", use_container_width=True)
            
            if st.session_state.analyzed_images:
                save_all_btn = st.button("💾 Save All to Collection", use_container_width=True)
                if save_all_btn:
                    for record in st.session_state.analyzed_images:
                        if record not in st.session_state.collection:
                            st.session_state.collection.append(record)
                    st.success(f"Saved {len(st.session_state.analyzed_images)} images to collection!")
                    st.rerun()
        
        # Analysis
        if analyze_btn and uploaded_files:
            engine = init_engine(model_choice)
            st.session_state.analyzed_images = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, file in enumerate(uploaded_files):
                status_text.text(f"Analyzing {file.name}...")
                
                record = analyze_image(file, passes, engine)
                st.session_state.analyzed_images.append(record)
                
                progress_bar.progress((idx + 1) / len(uploaded_files))
            
            status_text.text("✅ Analysis complete!")
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()
            st.rerun()
        
        # Display results
        if st.session_state.analyzed_images:
            st.markdown("---")
            st.markdown("## Analysis Results")
            
            # Grid view
            cols = st.columns(3)
            for idx, record in enumerate(st.session_state.analyzed_images):
                with cols[idx % 3]:
                    with st.container():
                        # Image
                        try:
                            img_path = record.get("_image_path") or record.get("image_path")
                            if img_path and Path(img_path).exists():
                                img = Image.open(img_path)
                                st.image(img, use_container_width=True)
                        except Exception:
                            st.info("Image preview unavailable")
                        
                        # Quick info
                        st.markdown(f"**{record.get('image_id', 'Unknown')}**")
                        
                        garment_type = record.get('garment_type', 'Unknown')
                        st.markdown(f"*{garment_type}*")
                        
                        # Primary color badge
                        primary_color = record.get('color_primary') or (record.get('color_palette', [''])[0] if record.get('color_palette') else '')
                        if primary_color:
                            st.markdown(create_badge(primary_color.title(), "primary"), unsafe_allow_html=True)
                        
                        # Fabric badge
                        fabric_type = record.get('fabric', {}).get('type')
                        if fabric_type:
                            st.markdown(create_badge(fabric_type.title(), "secondary"), unsafe_allow_html=True)
    
    # ==================== TAB 2: DETAILED VIEW ====================
    with tab2:
        st.markdown("## Detailed Analysis View")
        
        # Select image to view
        if st.session_state.analyzed_images or st.session_state.collection:
            all_records = st.session_state.analyzed_images + st.session_state.collection
            image_names = [r.get("image_id", f"Image {i}") for i, r in enumerate(all_records)]
            
            selected_idx = st.selectbox(
                "Select image to view",
                range(len(all_records)),
                format_func=lambda i: image_names[i]
            )
            
            record = all_records[selected_idx]
            
            # Layout
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("### 🖼️ Image")
                try:
                    img_path = record.get("_image_path") or record.get("image_path")
                    if img_path and Path(img_path).exists():
                        img = Image.open(img_path)
                        st.image(img, use_container_width=True)
                except Exception:
                    st.info("Image preview unavailable")
                
                # Prompt text
                st.markdown("### 📝 AI Training Prompt")
                prompt = record.get("prompt_text", "")
                if prompt:
                    st.markdown(f'<div class="prompt-text">{prompt}</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown("### 📊 Comprehensive Analysis")
                
                # Garment Info
                with st.expander("👕 **Garment Overview**", expanded=True):
                    garment_type = record.get("garment_type", "Unknown")
                    silhouette = record.get("silhouette", "Unknown")
                    fit = record.get("fit_and_drape", "Unknown")
                    
                    st.markdown(f"**Type:** {garment_type}")
                    st.markdown(f"**Silhouette:** {silhouette}")
                    st.markdown(f"**Fit & Drape:** {fit}")
                
                # Fabric
                with st.expander("🧵 **Fabric Details**", expanded=True):
                    fabric = record.get("fabric", {})
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Type:** {fabric.get('type') or 'Unknown'}")
                        st.markdown(f"**Texture:** {fabric.get('texture') or 'Unknown'}")
                    with col2:
                        st.markdown(f"**Weight:** {fabric.get('weight') or 'Unknown'}")
                        st.markdown(f"**Finish:** {fabric.get('finish') or 'Unknown'}")
                
                # Raw JSON
                with st.expander("🔍 **Raw JSON Data**"):
                    st.json(record)
        
        else:
            st.info("👆 Analyze some images in the 'Analyze Images' tab first!")
    
    # ==================== TAB 3: EXPORT HUB ====================
    with tab3:
        st.markdown("## Export Hub")
        st.markdown("*Download your analysis data in various formats*")
        
        if not (st.session_state.analyzed_images or st.session_state.collection):
            st.info("No data to export. Analyze some images first!")
        else:
            export_source = st.radio(
                "Export from:",
                ["Current Analysis", "Saved Collection", "Both"],
                horizontal=True
            )
            
            # Determine which records to export
            if export_source == "Current Analysis":
                records_to_export = st.session_state.analyzed_images
            elif export_source == "Saved Collection":
                records_to_export = st.session_state.collection
            else:
                records_to_export = st.session_state.analyzed_images + st.session_state.collection
            
            st.markdown(f"**{len(records_to_export)} records** ready for export")
            st.markdown("---")
            
            col1, col2, col3 = st.columns(3)
            
            # JSON Export
            with col1:
                st.markdown("### 📄 JSON Export")
                st.markdown("*Complete structured data*")
                
                if st.button("Generate JSON", use_container_width=True):
                    json_data = json.dumps(records_to_export, indent=2, ensure_ascii=False)
                    st.download_button(
                        label="⬇️ Download JSON",
                        data=json_data,
                        file_name="visual_descriptor_export.json",
                        mime="application/json",
                        use_container_width=True
                    )
            
            # CSV Export
            with col2:
                st.markdown("### 📊 CSV Export")
                st.markdown("*Flat table format*")
                
                if st.button("Generate CSV", use_container_width=True):
                    exporter = CSVExporter()
                    for record in records_to_export:
                        try:
                            exporter.add_flat(record)
                        except Exception as e:
                            st.warning(f"Skipped record: {e}")
                    
                    rows = exporter.export()
                    if rows:
                        df = pd.DataFrame(rows)
                        csv_data = df.to_csv(index=False)
                        st.download_button(
                            label="⬇️ Download CSV",
                            data=csv_data,
                            file_name="visual_descriptor_export.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
            
            # Prompt Text Export
            with col3:
                st.markdown("### 📝 Prompt Export")
                st.markdown("*AI training captions*")
                
                if st.button("Generate Prompts", use_container_width=True):
                    prompts = []
                    for record in records_to_export:
                        image_id = record.get("image_id", "unknown")
                        prompt = record.get("prompt_text", "")
                        if prompt:
                            prompts.append(f"{image_id}: {prompt}")
                    
                    prompt_text = "\n\n".join(prompts)
                    st.download_button(
                        label="⬇️ Download Prompts",
                        data=prompt_text,
                        file_name="visual_descriptor_prompts.txt",
                        mime="text/plain",
                        use_container_width=True
                    )

if __name__ == "__main__":
    main()