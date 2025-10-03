import streamlit as st
import pandas as pd

def show():
    """Gallery page for viewing and comparing multiple analyses"""
    
    st.markdown("## 📊 Analysis Gallery")
    st.markdown("Compare and filter your analyzed images")
    
    # Check if we have results
    if "analysis_results" not in st.session_state or not st.session_state.analysis_results:
        st.info("👋 No analyses yet! Go to the **Analyze** page to process some images.")
        if st.button("🔍 Go to Analyze"):
            st.session_state["page"] = "🔍 Analyze"
            st.rerun()
        return
    
    results = st.session_state.analysis_results
    
    # Summary metrics
    st.markdown("### 📈 Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Images", len(results))
    
    with col2:
        avg_time = sum(r.get("_processing_time", 0) for r in results) / len(results)
        st.metric("Avg Processing Time", f"{avg_time:.2f}s")
    
    with col3:
        garment_types = set(r.get("garment_type") for r in results if r.get("garment_type"))
        st.metric("Unique Garment Types", len(garment_types))
    
    with col4:
        fabrics = set(r.get("fabric", {}).get("type") for r in results if r.get("fabric", {}).get("type"))
        st.metric("Unique Fabrics", len(fabrics))
    
    st.markdown("---")
    
    # Filters
    st.markdown("### 🔍 Filters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        garment_filter = st.multiselect(
            "Garment Type",
            options=sorted(set(r.get("garment_type") for r in results if r.get("garment_type"))),
            default=[]
        )
    
    with col2:
        fabric_filter = st.multiselect(
            "Fabric Type",
            options=sorted(set(r.get("fabric", {}).get("type") for r in results if r.get("fabric", {}).get("type"))),
            default=[]
        )
    
    with col3:
        color_filter = st.multiselect(
            "Primary Color",
            options=sorted(set(r.get("color_primary") for r in results if r.get("color_primary"))),
            default=[]
        )
    
    # Apply filters
    filtered_results = results
    if garment_filter:
        filtered_results = [r for r in filtered_results if r.get("garment_type") in garment_filter]
    if fabric_filter:
        filtered_results = [r for r in filtered_results if r.get("fabric", {}).get("type") in fabric_filter]
    if color_filter:
        filtered_results = [r for r in filtered_results if r.get("color_primary") in color_filter]
    
    st.info(f"Showing {len(filtered_results)} of {len(results)} images")
    
    # View mode selection
    view_mode = st.radio(
        "View Mode",
        ["📇 Grid View", "📊 Table View", "🔀 Comparison"],
        horizontal=True
    )
    
    st.markdown("---")
    
    if view_mode == "📇 Grid View":
        show_grid_view(filtered_results)
    elif view_mode == "📊 Table View":
        show_table_view(filtered_results)
    else:
        show_comparison_view(filtered_results)


def show_grid_view(results: list):
    """Display results in a grid layout"""
    
    st.markdown("### Gallery")
    
    # Grid layout (3 columns)
    cols_per_row = 3
    
    for i in range(0, len(results), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(results):
                with col:
                    display_card(results[idx], idx)


def display_card(result: dict, idx: int):
    """Display a single result card"""
    
    with st.container():
        # Image
        if "_image_bytes" in result:
            st.image(result["_image_bytes"], use_container_width=True)
        
        # Details
        st.markdown(f"**{result.get('image_id', f'Image {idx+1}')}**")
        
        garment = result.get("garment_type", "N/A")
        fabric = result.get("fabric", {}).get("type", "N/A")
        color = result.get("color_primary", "N/A")
        
        st.caption(f"🎯 {garment}")
        st.caption(f"🧵 {fabric}")
        st.caption(f"🎨 {color}")
        
        # View details button
        if st.button(f"View Details", key=f"view_{idx}"):
            st.session_state[f"selected_result_{idx}"] = result
            with st.expander("Details", expanded=True):
                st.json({k: v for k, v in result.items() if not k.startswith("_")})


def show_table_view(results: list):
    """Display results in a table"""
    
    st.markdown("### Data Table")
    
    # Build table data
    table_data = []
    for r in results:
        row = {
            "Image ID": r.get("image_id", "N/A"),
            "Garment Type": r.get("garment_type", "N/A"),
            "Silhouette": r.get("silhouette", "N/A"),
            "Fabric Type": r.get("fabric", {}).get("type", "N/A"),
            "Fabric Texture": r.get("fabric", {}).get("texture", "N/A"),
            "Fabric Weight": r.get("fabric", {}).get("weight", "N/A"),
            "Primary Color": r.get("color_primary", "N/A"),
            "Secondary Color": r.get("color_secondary", "N/A"),
            "Closure": r.get("construction", {}).get("closure", "N/A"),
            "Photo Style": r.get("photo_style", "N/A"),
        }
        table_data.append(row)
    
    df = pd.DataFrame(table_data)
    
    # Display with sorting and filtering
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=600
    )
    
    # Export table
    if st.button("📥 Export Table as CSV"):
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="gallery_table.csv",
            mime="text/csv"
        )


def show_comparison_view(results: list):
    """Compare multiple results side-by-side"""
    
    st.markdown("### Side-by-Side Comparison")
    
    if len(results) < 2:
        st.info("Need at least 2 images for comparison")
        return
    
    # Select images to compare
    image_ids = [r.get("image_id", f"Image {i+1}") for i, r in enumerate(results)]
    
    col1, col2 = st.columns(2)
    
    with col1:
        left_idx = st.selectbox("Left Image", range(len(results)), format_func=lambda i: image_ids[i])
    
    with col2:
        right_idx = st.selectbox("Right Image", range(len(results)), index=min(1, len(results)-1), format_func=lambda i: image_ids[i])
    
    st.markdown("---")
    
    # Display comparison
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown(f"### {image_ids[left_idx]}")
        display_comparison_card(results[left_idx])
    
    with col_right:
        st.markdown(f"### {image_ids[right_idx]}")
        display_comparison_card(results[right_idx])
    
    # Highlight differences
    st.markdown("---")
    st.markdown("### 🔍 Key Differences")
    
    left = results[left_idx]
    right = results[right_idx]
    
    differences = []
    
    # Compare garment type
    if left.get("garment_type") != right.get("garment_type"):
        differences.append(f"**Garment Type:** {left.get('garment_type')} vs {right.get('garment_type')}")
    
    # Compare fabric
    left_fabric = left.get("fabric", {}).get("type")
    right_fabric = right.get("fabric", {}).get("type")
    if left_fabric != right_fabric:
        differences.append(f"**Fabric:** {left_fabric} vs {right_fabric}")
    
    # Compare colors
    if left.get("color_primary") != right.get("color_primary"):
        differences.append(f"**Primary Color:** {left.get('color_primary')} vs {right.get('color_primary')}")
    
    # Compare silhouette
    if left.get("silhouette") != right.get("silhouette"):
        differences.append(f"**Silhouette:** {left.get('silhouette')} vs {right.get('silhouette')}")
    
    if differences:
        for diff in differences:
            st.markdown(f"- {diff}")
    else:
        st.success("These images have very similar attributes!")


def display_comparison_card(result: dict):
    """Display a comparison card"""
    
    # Image
    if "_image_bytes" in result:
        st.image(result["_image_bytes"], use_container_width=True)
    
    # Key details
    st.markdown("#### Key Details")
    
    st.markdown(f"**Garment:** {result.get('garment_type', 'N/A')}")
    st.markdown(f"**Silhouette:** {result.get('silhouette', 'N/A')}")
    
    fabric = result.get("fabric", {})
    if isinstance(fabric, dict):
        st.markdown(f"**Fabric:** {fabric.get('type', 'N/A')} ({fabric.get('texture', 'N/A')})")
    
    st.markdown(f"**Primary Color:** {result.get('color_primary', 'N/A')}")
    
    construction = result.get("construction", {})
    if isinstance(construction, dict):
        st.markdown(f"**Closure:** {construction.get('closure', 'N/A')}")
        st.markdown(f"**Stitching:** {construction.get('stitching', 'N/A')}")
    
    # Prompt text
    if result.get("prompt_text"):
        with st.expander("📝 Full Description"):
            st.caption(result["prompt_text"])