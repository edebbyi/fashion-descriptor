import streamlit as st
from pathlib import Path
import json
from src.visual_descriptor.engine import Engine


st.set_page_config(page_title="Visual Descriptor", layout="wide")


st.title("Visual Descriptor — Mini Reviewer")
left, right = st.columns([1,2])


engine = Engine(model="openai")


with left:
uploaded = st.file_uploader("Upload image(s)", type=["jpg","jpeg","png"], accept_multiple_files=True)
passes = st.multiselect("Passes", ["A","B","C"], default=["A","B","C"])
if st.button("Run Descriptor") and uploaded:
out_records = []
for f in uploaded:
p = Path("/tmp")/f.name
p.write_bytes(f.read())
rec = engine.describe_image(p, passes)
out_records.append(rec)
st.session_state["records"] = out_records


with right:
recs = st.session_state.get("records", [])
for rec in recs:
with st.expander(rec["image_id"], expanded=True):
st.json(rec)
# prompt line
from src.visual_descriptor.export_csv_prompt import prompt_line
st.code(prompt_line(rec))