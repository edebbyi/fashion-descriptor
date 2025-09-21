# Visual Descriptor Tool (MVP)


Photo → structured fashion descriptors (fabric, silhouette, stitching, pose, lighting). Runs locally, exposes CLI + FastAPI, optional Streamlit review.


## 1) Install
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt


## 2) Run on a single image or folder
# Single file
python -m src.cli --in data/images/look1.jpg --out outputs
# Folder
python -m src.cli --in data/images --out outputs --passes A,B,C --normalize yes


## 3) Start API (single-file upload endpoint)
export API_KEY=dev_example_key_123
make api # or: uvicorn api.app:app --reload
# Then POST with multipart form-data 'file' and header Authorization: Bearer dev_example_key_123


## 4) Streamlit reviewer (optional)
make ui


## 5) Swap models later
- Default uses a zero-cost **StubCaptioner** (fast for wiring/tests).
- Enable BLIP‑2 by installing transformers/torch and setting `--model blip2` (or `VD_MODEL=blip2`).
- You can add any VLM as `captioners/<name>.py` exposing `.run(image_path, pass_id)`.


## 6) Outputs
- `outputs/json/<image_id>.json` (one per image)
- `outputs/descriptors.csv` (batch)
- `outputs/prompt_text.txt` (one prompt-ready line per image)


## 7) Acceptance checks
- Pydantic schema validation ensures JSON validity.
- Add more tests in `tests/` for coverage % if desired.


## 8) Deploy cheap & fast
- **Local**: good for batches and no infra cost.
- **API on a $5 VM** (Fly.io/Render/EC2 t4g.micro) using the stub or a small CPU model.
- For heavy VLM runs, burst on a **spot GPU** (RunPod/Lambda) only when needed; keep API on a tiny CPU VM.


## 9) License
MIT