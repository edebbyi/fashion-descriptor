# api/app.py
from __future__ import annotations
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.security import APIKeyHeader
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from pathlib import Path
from typing import Optional
import os, uuid, shutil, json, logging

from src.visual_descriptor.engine import Engine

# --- Config ---
API_KEY = os.getenv("API_KEY", "charlie305$")
logging.getLogger("uvicorn").info(f"[vd] API_KEY (expected) = {API_KEY!r}")

app = FastAPI(
    title="Visual Descriptor API",
    version="1.0.0",
    swagger_ui_parameters={"persistAuthorization": True},  # keep token in /docs
)

# choose model backend: "openai" | "blip2" | "stub"
engine = Engine(model=os.getenv("VD_MODEL", "openai"))

BASE = Path(os.getenv("BASE_DIR", ".")).resolve()
(BASE / "uploads").mkdir(parents=True, exist_ok=True)
(BASE / "outputs").mkdir(parents=True, exist_ok=True)

# --- Security (API key via Authorization header) ---
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

def _auth_ok(h: Optional[str]) -> bool:
    if not h:
        return False
    s = h.strip()
    return s == API_KEY or s == f"Bearer {API_KEY}"

def get_api_key(authorization: Optional[str] = Depends(api_key_header)) -> str:
    if not _auth_ok(authorization):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return authorization or ""


# --- Models ---
class JobResponse(BaseModel):
    job_id: str
    status: str
    records: list[dict] = []


# --- Routes ---
@app.get("/")
def index():
    # Friendly landing page → /docs
    return RedirectResponse(url="/docs")

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/debug")
def debug():
    # Handy to confirm backend & env while running
    try:
        backend = type(engine.model).__name__
    except Exception:
        backend = "unknown"
    return {
        "backend": backend,
        "vd_model_env": os.getenv("VD_MODEL"),
        "openai_key_present": bool(os.getenv("OPENAI_API_KEY")),
    }

@app.post("/v1/jobs", response_model=JobResponse)
async def create_job(
    api_key: str = Depends(get_api_key),     # ← pulls from Swagger Authorize
    passes: str = Form("A,B,C"),
    file: UploadFile | None = File(None),
):
    if file is None:
        raise HTTPException(status_code=400, detail="Upload a file via multipart/form-data key 'file'")

    job_id = f"j_{uuid.uuid4().hex[:8]}"
    work_dir = BASE / "uploads" / job_id
    out_dir = BASE / "outputs" / job_id
    work_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "json").mkdir(parents=True, exist_ok=True)

    # Save upload
    fp = work_dir / file.filename
    with open(fp, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Run engine
    rec = engine.describe_image(fp, passes=passes.split(","))

    # Persist per-image JSON
    out_json = out_dir / "json" / f"{fp.stem}.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=2, ensure_ascii=False)

    return JobResponse(job_id=job_id, status="completed", records=[rec])