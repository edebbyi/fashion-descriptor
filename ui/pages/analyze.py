import streamlit as st
from pathlib import Path
import json
import time
from PIL import Image
import io

def show():
    """Main analysis page with rich visualizations"""
    
    st.markdown("## 🔍 Image Analysis")
    st.markdown("Upload fashion images for detailed AI-powered analysis")
    
    # Initialize session state
    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = []
    
    # Upload section
    st.markdown("---")
    uploaded_files = st.file_uploader(
        "📤 Upload Images",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        help="Upload one or more fashion images for analysis"
    )
    
    # Analysis options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        passes = st.multiselect(
            "Analysis Passes",
            ["A", "B", "C"],
            default=["A", "B", "C"],
            help="A=Global, B=Construction, C=Pose/Lighting"
        )
    
    with col2:
        model = st.selectbox(
            "AI Model",
            ["gemini", "openai", "stub"],
            index=0,
            help="Gemini Flash 2.5 (recommended)"
        )
    
    with col3:
        st.markdown("###")
        analyze_button = st.button(
            "🚀 Analyze Images",
            type="primary",
            use_container_width=True,
            disabled=not uploaded_files
        )
    
    # Analysis execution
    if analyze_button and uploaded_files:
        from src.visual_descriptor.engine import Engine
        
        engine = Engine(model=model, normalize=True)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        
        for idx, uploaded_file in enumerate(uploaded_files):
            # Update progress
            progress = (idx + 1) / len(uploaded_files)
            progress_bar.progress(progress)
            status_text.text(f"Analyzing {uploaded_file.name}... ({idx + 1}/{len(uploaded_files)})")
            
            # Save temp file
            temp_path = Path("/tmp") / uploaded_file.name
            temp_path.write_bytes(uploaded_file.read())
            
            # Analyze
            try:
                start_time = time.time()
                record = engine.describe_image(temp_path, passes=passes)
                elapsed = time.time() - start_time
                
                # Store image for display
                img = Image.open(temp_path)
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG")
                record["_image_bytes"] = buffered.getvalue()
                record["_processing_time"] = elapsed
                
                results.append(record)
            except Exception as e:
                st.error(f"Error analyzing {uploaded_file.name}: {str(e)}")
        
        progress_bar.empty()
        status_text.empty()
        
        if results:
            st.session_state.analysis_results = results
            st.success(f"✅ Successfully analyzed {len(results)} image(s)!")
            st.balloons()
    
    # Display results
    if st.session_state.analysis_results:
        st.markdown("---")
        st.markdown("## 📊 Analysis Results")
        
        # Results tabs
        tabs = st.tabs([f"Image {i+1}" for i in range(len(st.session_state.analysis_results))])
        
        for idx, (tab, result) in enumerate(zip(tabs, st.session_state.analysis_results)):
            with tab:
                display_analysis_result(result, idx)
        
        # Bulk export
        st.markdown("---")
        st.markdown("### 💾 Export Results")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📄 Export JSON", use_container_width=True):
                export_json(st.session_state.analysis_results)
        
        with col2:
            if st.button("📊 Export CSV", use_container_width=True):
                export_csv(st.session_state.analysis_results)
        
        with col3:
            if st.button("📝 Export Prompts", use_container_width=True):
                export_prompts(st.session_state.analysis_results)
        
        with col4:
            if st.button("🗑️ Clear Results", use_container_width=True):
                st.session_state.analysis_results = []
                st.rerun()


def display_analysis_result(result: dict, idx: int):
    """Display a single analysis result with rich visualizations"""
    
    # Top metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Processing Time", f"{result.get('_processing_time', 0):.2f}s")
    
    with col2:
        backend = result.get("backend", "Unknown")
        st.metric("AI Backend", backend)
    
    with col3:
        fields_count = count_filled_fields(result)
        st.metric("Fields Extracted", fields_count)
    
    st.markdown("---")
    
    # Main content: Image + Analysis
    col_img, col_data = st.columns([1, 1])
    
    with col_img:
        st.markdown("### 📸 Image")
        if "_image_bytes" in result:
            st.image(result["_image_bytes"], use_container_width=True)
        
        # Prompt text
        if result.get("prompt_text"):
            st.markdown("### 📝 AI-Generated Description")
            st.info(result["prompt_text"])
    
    with col_data:
        st.markdown("### 🎯 Key Details")
        
        # Garment overview
        with st.expander("👗 Garment Overview", expanded=True):
            st.markdown(f"**Type:** {result.get('garment_type') or 'N/A'}")
            st.markdown(f"**Silhouette:** {result.get('silhouette') or 'N/A'}")
            st.markdown(f"**Fit & Drape:** {result.get('fit_and_drape') or 'N/A'}")
        
        # Fabric details
        with st.expander("🧵 Fabric Analysis", expanded=True):
            fabric = result.get("fabric", {})
            if isinstance(fabric, dict):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Type:** {fabric.get('type') or 'N/A'}")
                    st.markdown(f"**Texture:** {fabric.get('texture') or 'N/A'}")
                with col2:
                    st.markdown(f"**Weight:** {fabric.get('weight') or 'N/A'}")
                    st.markdown(f"**Finish:** {fabric.get('finish') or 'N/A'}")
        
        # Colors
        with st.expander("🌈 Colors & Patterns", expanded=True):
            display_colors(result)
        
        # Construction
        with st.expander("🔧 Construction Details", expanded=True):
            display_construction(result)
        
        # Photography
        with st.expander("📷 Photography Analysis", expanded=False):
            display_photography(result)
    
    # Full JSON (collapsible)
    st.markdown("---")
    with st.expander("🔍 View Full JSON Data"):
        # Remove image bytes for display
        display_result = {k: v for k, v in result.items() if not k.startswith("_")}
        st.json(display_result)


def display_colors(result: dict):
    """Display color analysis with visual swatches"""
    
    color_primary = result.get("color_primary")
    color_secondary = result.get("color_secondary")
    color_palette = result.get("color_palette", [])
    
    if color_primary:
        st.markdown(f"**Primary:** {color_primary}")
    
    if color_secondary:
        st.markdown(f"**Secondary:** {color_secondary}")
    
    if color_palette:
        st.markdown(f"**Palette:** {', '.join(color_palette)}")
    
    # Pattern detection
    colors_obj = result.get("colors", {})
    if isinstance(colors_obj, dict):
        pattern = colors_obj.get("pattern")
        if isinstance(pattern, dict) and pattern.get("type"):
            ptype = pattern.get("type", "").replace("_", " ").title()
            fg = pattern.get("foreground", "")
            bg = pattern.get("background", "")
            st.markdown(f"**Pattern:** {ptype}")
            if fg:
                st.markdown(f"  - Foreground: {fg}")
            if bg:
                st.markdown(f"  - Background: {bg}")


def display_construction(result: dict):
    """Display construction details"""
    
    construction = result.get("construction", {})
    if not isinstance(construction, dict):
        st.markdown("*No construction data*")
        return
    
    # Global construction
    if construction.get("seams"):
        st.markdown(f"**Seams:** {construction['seams']}")
    
    if construction.get("stitching"):
        stitch = construction['stitching']
        color = construction.get("stitching_color", "")
        if color:
            st.markdown(f"**Stitching:** {color} {stitch}")
        else:
            st.markdown(f"**Stitching:** {stitch}")
    
    if construction.get("closure"):
        st.markdown(f"**Closure:** {construction['closure']}")
    
    # Top construction
    top = construction.get("top")
    if isinstance(top, dict):
        st.markdown("**Top:**")
        if top.get("seams"):
            st.markdown(f"  - Seams: {top['seams']}")
        if top.get("stitching"):
            st.markdown(f"  - Stitching: {top.get('stitching_color', '')} {top['stitching']}")
        if top.get("closure"):
            st.markdown(f"  - Closure: {top['closure']}")
    
    # Bottom construction
    bottom = construction.get("bottom")
    if isinstance(bottom, dict):
        st.markdown("**Bottom:**")
        if bottom.get("seams"):
            st.markdown(f"  - Seams: {bottom['seams']}")
        if bottom.get("stitching"):
            st.markdown(f"  - Stitching: {bottom.get('stitching_color', '')} {bottom['stitching']}")


def display_photography(result: dict):
    """Display photography analysis"""
    
    st.markdown(f"**Pose:** {result.get('pose') or 'N/A'}")
    st.markdown(f"**Photo Style:** {result.get('photo_style') or 'N/A'}")
    
    model = result.get("model", {})
    if isinstance(model, dict):
        st.markdown("**Model:**")
        if model.get("framing"):
            st.markdown(f"  - Framing: {model['framing']}")
        if model.get("expression"):
            st.markdown(f"  - Expression: {model['expression']}")
        if model.get("gaze"):
            st.markdown(f"  - Gaze: {model['gaze']}")
    
    camera = result.get("camera", {})
    if isinstance(camera, dict):
        st.markdown("**Camera:**")
        if camera.get("view"):
            st.markdown(f"  - View: {camera['view']}")
        if camera.get("angle"):
            st.markdown(f"  - Angle: {camera['angle']}")
        if camera.get("multiview") == "yes":
            st.markdown(f"  - Multi-view: {camera.get('views', 'Yes')}")
    
    lighting = result.get("environment_lighting", {})
    if isinstance(lighting, dict):
        st.markdown("**Lighting:**")
        if lighting.get("setup"):
            st.markdown(f"  - Setup: {lighting['setup']}")
        if lighting.get("mood"):
            st.markdown(f"  - Mood: {lighting['mood']}")
        if lighting.get("background"):
            st.markdown(f"  - Background: {lighting['background']}")


def count_filled_fields(result: dict) -> int:
    """Count non-null fields in result"""
    count = 0
    
    def count_recursive(obj):
        nonlocal count
        if isinstance(obj, dict):
            for k, v in obj.items():
                if not k.startswith("_"):
                    if v is not None and v != "" and v != []:
                        if isinstance(v, (dict, list)):
                            count_recursive(v)
                        else:
                            count += 1
        elif isinstance(obj, list):
            for item in obj:
                count_recursive(item)
    
    count_recursive(result)
    return count


def export_json(results: list):
    """Export results as JSON"""
    # Remove image bytes
    clean_results = []
    for r in results:
        clean = {k: v for k, v in r.items() if not k.startswith("_")}
        clean_results.append(clean)
    
    json_str = json.dumps(clean_results, indent=2, ensure_ascii=False)
    st.download_button(
        label="📥 Download JSON",
        data=json_str,
        file_name="analysis_results.json",
        mime="application/json"
    )


def export_csv(results: list):
    """Export results as CSV"""
    from src.visual_descriptor.export_csv_prompt import CSVExporter
    
    exporter = CSVExporter()
    for r in results:
        clean = {k: v for k, v in r.items() if not k.startswith("_")}
        exporter.add_flat(clean)
    
    rows = exporter.export()
    if not rows:
        st.error("No data to export")
        return
    
    # Convert to CSV string
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    
    st.download_button(
        label="📥 Download CSV",
        data=output.getvalue(),
        file_name="analysis_results.csv",
        mime="text/csv"
    )


def export_prompts(results: list):
    """Export prompt text"""
    lines = []
    for r in results:
        image_id = r.get("image_id", "unknown")
        prompt = r.get("prompt_text", "")
        lines.append(f"{image_id}: {prompt}")
    
    prompt_text = "\n\n".join(lines)
    
    st.download_button(
        label="📥 Download Prompts",
        data=prompt_text,
        file_name="prompt_text.txt",
        mime="text/plain"
    )