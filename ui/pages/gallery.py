import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Fix path setup
current_file = Path(__file__).resolve()
repo_root = current_file.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "ui"))

from shared_init import init_session_state

# Initialize session state
init_session_state()

st.title("📊 Gallery")
st.markdown("*View and compare your analyzed images*")
st.markdown("---")

# Check what we have
has_analyzed = len(st.session_state.analyzed_images) > 0
has_collection = len(st.session_state.collection) > 0

# Show workflow hint if they have analyzed but not saved
if has_analyzed and not has_collection:
    st.info("💡 **Tip**: You have not saved your analyzed images yet. Go to the **analyze** page and click '💾 Save to Gallery' to keep them permanently!")

# View selector
view_option = st.radio(
    "📁 Show:",
    ["🎯 Gallery (Saved)", "🔬 Recent Analysis", "🌐 All Images"],
    horizontal=True,
    help="Gallery = permanently saved | Recent Analysis = temporary | All = both combined"
)

# Determine which records to show
if view_option == "🎯 Gallery (Saved)":
    all_records = st.session_state.collection
    if not all_records:
        st.warning("📭 Your gallery is empty!")
        st.markdown("Go to the **analyze** page to process images, then save them to your gallery.")
elif view_option == "🔬 Recent Analysis":
    all_records = st.session_state.analyzed_images
    if not all_records:
        st.info("🔍 No recent analysis!")
        st.markdown("Go to the **analyze** page to process new fashion images.")
else:  # All Images
    all_records = st.session_state.collection + st.session_state.analyzed_images
    if not all_records:
        st.info("👋 No images yet!")
        st.markdown("Go to the **analyze** page to get started.")

if not all_records:
    if st.button("🔍 Go to Analyze Page", use_container_width=True):
        st.switch_page("pages/analyze.py")
else:
    # Summary metrics
    st.markdown("### 📈 Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Images", len(all_records))
    
    with col2:
        garment_types = set(r.get("garment_type") for r in all_records if r.get("garment_type"))
        st.metric("Garment Types", len(garment_types))
    
    with col3:
        fabrics = set(r.get("fabric", {}).get("type") for r in all_records if r.get("fabric", {}).get("type"))
        st.metric("Fabric Types", len(fabrics))
    
    with col4:
        colors = set(r.get("color_primary") for r in all_records if r.get("color_primary"))
        st.metric("Colors", len(colors))
    
    st.markdown("---")
    
    # Filters
    st.markdown("### 🔍 Filters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        garment_filter = st.multiselect(
            "Garment Type",
            options=sorted(set(r.get("garment_type") for r in all_records if r.get("garment_type"))),
            default=[]
        )
    
    with col2:
        fabric_filter = st.multiselect(
            "Fabric Type",
            options=sorted(set(r.get("fabric", {}).get("type") for r in all_records if r.get("fabric", {}).get("type"))),
            default=[]
        )
    
    with col3:
        color_filter = st.multiselect(
            "Primary Color",
            options=sorted(set(r.get("color_primary") for r in all_records if r.get("color_primary"))),
            default=[]
        )
    
    # Apply filters
    filtered_records = all_records
    if garment_filter:
        filtered_records = [r for r in filtered_records if r.get("garment_type") in garment_filter]
    if fabric_filter:
        filtered_records = [r for r in filtered_records if r.get("fabric", {}).get("type") in fabric_filter]
    if color_filter:
        filtered_records = [r for r in filtered_records if r.get("color_primary") in color_filter]
    
    st.info(f"Showing {len(filtered_records)} of {len(all_records)} images")
    
    # View mode
    view_mode = st.radio(
        "View Mode",
        ["📇 Grid View", "📊 Table View"],
        horizontal=True
    )
    
    st.markdown("---")
    
    # Grid View
    if view_mode == "📇 Grid View":
        st.markdown("### Gallery")
        
        if not filtered_records:
            st.warning("No images match the selected filters.")
        else:
            # 3 columns grid
            cols_per_row = 3
            
            for i in range(0, len(filtered_records), cols_per_row):
                cols = st.columns(cols_per_row)
                
                for j, col in enumerate(cols):
                    idx = i + j
                    if idx < len(filtered_records):
                        record = filtered_records[idx]
                        
                        with col:
                            # Image
                            if record.get("_image_base64"):
                                st.markdown(
                                    f'<img src="{record["_image_base64"]}" style="width:100%; border-radius:8px;">',
                                    unsafe_allow_html=True
                                )
                            else:
                                st.info("Preview unavailable")
                            
                            # Details
                            st.markdown(f"**{record.get('image_id', f'Image {idx+1}')}**")
                            
                            garment = record.get('garment_type', 'N/A')
                            fabric = record.get('fabric', {}).get('type', 'N/A')
                            color = record.get('color_primary', 'N/A')
                            
                            st.caption(f"🎯 {garment}")
                            st.caption(f"🧵 {fabric}")
                            st.caption(f"🎨 {color}")
    
    # Table View
    else:
        st.markdown("### Data Table")
        
        if not filtered_records:
            st.warning("No images match the selected filters.")
        else:
            # Build table data
            table_data = []
            for r in filtered_records:
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
            
            # Display with sorting
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                height=500
            )
            
            # Export table
            if st.button("📥 Export Table as CSV", use_container_width=True):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="⬇️ Download CSV",
                    data=csv,
                    file_name="gallery_table.csv",
                    mime="text/csv",
                    use_container_width=True
                )