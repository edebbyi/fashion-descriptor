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
VD_MODEL = os.getenv("VD_MODEL", "gemini")
logging.getLogger("uvicorn").info(f"[vd] API_KEY (expected) = {API_KEY!r}")
logging.getLogger("uvicorn").info(f"[vd] VD_MODEL = {VD_MODEL}")

app = FastAPI(
    title="Fashion Descriptor API",
    version="2.0.0",
    description=f"Fashion image analysis powered by {VD_MODEL.upper()}",
    swagger_ui_parameters={"persistAuthorization": True},
)

# Initialize engine with configured model
try:
    engine = Engine(model=VD_MODEL)
    backend_name = type(engine.model).__name__
    logging.getLogger("uvicorn").info(f"[vd] Loaded backend: {backend_name}")
except Exception as e:
    logging.getLogger("uvicorn").error(f"[vd] Failed to load backend: {e}")
    raise

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
    backend: str
    model: str


# --- Routes ---
@app.get("/")
def index():
    """Redirect to API docs"""
    return RedirectResponse(url="/docs")

@app.get("/healthz")
async def healthz():
    """Health check endpoint"""
    return {
        "status": "ok",
        "model": VD_MODEL,
        "backend": type(engine.model).__name__
    }

@app.get("/debug")
def debug():
    """Debug endpoint to verify configuration"""
    try:
        backend = type(engine.model).__name__
    except Exception:
        backend = "unknown"
    
    return {
        "backend": backend,
        "vd_model_env": VD_MODEL,
        "gemini_key_present": bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
        "openai_key_present": bool(os.getenv("OPENAI_API_KEY")),
        "api_key_set": bool(API_KEY),
    }

@app.post("/v1/jobs", response_model=JobResponse)
async def create_job(
    api_key: str = Depends(get_api_key),
    passes: str = Form("A,B,C"),
    file: UploadFile | None = File(None),
):
    """
    Analyze a fashion image and return structured descriptors.
    
    - **file**: Image file (JPG, PNG, WebP)
    - **passes**: Comma-separated analysis passes (A=global, B=construction, C=pose/lighting)
    - **Authorization header**: Bearer token for API authentication
    """
    if file is None:
        raise HTTPException(
            status_code=400,
            detail="Upload a file via multipart/form-data key 'file'"
        )

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
    try:
        rec = engine.describe_image(fp, passes=passes.split(","))
    except Exception as e:
        logging.getLogger("uvicorn").error(f"[vd] Engine error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    # Persist per-image JSON
    out_json = out_dir / "json" / f"{fp.stem}.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=2, ensure_ascii=False)

    return JobResponse(
        job_id=job_id,
        status="completed",
        records=[rec],
        backend=type(engine.model).__name__,
        model=VD_MODEL
    )

