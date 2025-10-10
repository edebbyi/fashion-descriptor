# api/app.py
from __future__ import annotations
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.security import APIKeyHeader
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from pathlib import Path
from typing import Optional, List
import os, uuid, shutil, json, logging, zipfile, tempfile

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
    model: str = Form(VD_MODEL),  # Optional model override
    file: UploadFile | None = File(None),
):
    """
    Analyze fashion images and return structured descriptors.
    
    - **file**: Image file (JPG, PNG, WebP) or ZIP folder containing images
    - **passes**: Comma-separated analysis passes (A=global, B=construction, C=pose/lighting)
    - **model**: AI model to use (openai, gemini, blip2, stub). Defaults to environment setting.
    - **Authorization header**: Bearer token for API authentication
    
    For individual images, returns a single record.
    For ZIP folders, processes all images in the folder and returns multiple records.
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
    filename = file.filename or "upload"
    fp = work_dir / filename
    with open(fp, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Determine if it's a ZIP file or regular image
    is_zip = filename.lower().endswith('.zip')
    
    # Create engine instance for this request with specified model
    try:
        request_engine = Engine(model=model)
        backend_name = type(request_engine.model).__name__
        logging.getLogger("uvicorn").info(f"[vd] Using model: {model} (backend: {backend_name})")
    except Exception as e:
        logging.getLogger("uvicorn").error(f"[vd] Failed to load model '{model}': {e}")
        raise HTTPException(status_code=400, detail=f"Invalid model '{model}'. Supported: openai, gemini, blip2, stub")
    
    try:
        if is_zip:
            # Handle ZIP folder
            records = await _process_zip_folder(fp, work_dir, out_dir, passes.split(","), request_engine)
        else:
            # Handle single image
            records = [await _process_single_image(fp, out_dir, passes.split(","), request_engine)]
            
    except Exception as e:
        logging.getLogger("uvicorn").error(f"[vd] Processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    return JobResponse(
        job_id=job_id,
        status="completed",
        records=records,
        backend=backend_name,
        model=model
    )


async def _process_single_image(image_path: Path, out_dir: Path, passes: List[str], engine: Engine) -> dict:
    """Process a single image and return the analysis record."""
    # Run engine
    rec = engine.describe_image(image_path, passes=passes)
    
    # Persist per-image JSON
    out_json = out_dir / "json" / f"{image_path.stem}.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=2, ensure_ascii=False)
    
    return rec


async def _process_zip_folder(zip_path: Path, work_dir: Path, out_dir: Path, passes: List[str], engine: Engine) -> List[dict]:
    """Extract ZIP file and process all images inside it."""
    extracted_dir = work_dir / "extracted"
    extracted_dir.mkdir(exist_ok=True)
    
    # Extract ZIP file
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extracted_dir)
        # Log extraction details
        extracted_files = zip_ref.namelist()
        logging.getLogger("uvicorn").info(f"[vd] Extracted {len(extracted_files)} files from ZIP")
        logging.getLogger("uvicorn").debug(f"[vd] Extracted files: {extracted_files}")
    
    # Enumerate all extracted files
    all_extracted_files = [f for f in extracted_dir.rglob("*") if f.is_file()]
    logging.getLogger("uvicorn").info(f"[vd] Found {len(all_extracted_files)} total files after extraction")
    
    # Use engine's enumerate_inputs to find all images
    image_paths = engine.enumerate_inputs(extracted_dir)
    
    # Log image discovery results
    if image_paths:
        logging.getLogger("uvicorn").info(f"[vd] Found {len(image_paths)} valid images: {[img.name for img in image_paths]}")
    
    if not image_paths:
        # Provide detailed error information
        file_extensions = [f.suffix.lower() for f in all_extracted_files]
        logging.getLogger("uvicorn").error(f"[vd] No images found. File extensions in ZIP: {set(file_extensions)}")
        logging.getLogger("uvicorn").error(f"[vd] All extracted files: {[f.name for f in all_extracted_files]}")
        raise HTTPException(
            status_code=400,
            detail=f"No valid images found in ZIP file. Found {len(all_extracted_files)} files with extensions: {sorted(set(file_extensions))}. Supported formats: .jpg, .jpeg, .png, .webp"
        )
    
    records = []
    
    # Process each image
    logging.getLogger("uvicorn").info(f"[vd] Starting to process {len(image_paths)} images...")
    for i, image_path in enumerate(image_paths, 1):
        try:
            logging.getLogger("uvicorn").info(f"[vd] Processing image {i}/{len(image_paths)}: {image_path.name}")
            rec = engine.describe_image(image_path, passes=passes)
            
            # Persist per-image JSON
            out_json = out_dir / "json" / f"{image_path.stem}.json"
            with open(out_json, "w", encoding="utf-8") as f:
                json.dump(rec, f, indent=2, ensure_ascii=False)
            
            records.append(rec)
            logging.getLogger("uvicorn").info(f"[vd] Successfully processed {image_path.name}")
            # Log key analysis results
            garment_type = rec.get('garment_type', 'unknown')
            color_primary = rec.get('color_primary', 'unknown')
            confidence_score = rec.get('confidence', {}).get('overall', 'N/A')
            logging.getLogger("uvicorn").info(f"[vd] Analysis: {garment_type}, color: {color_primary}, confidence: {confidence_score}")
            
        except Exception as e:
            logging.getLogger("uvicorn").warning(f"[vd] Failed to process {image_path.name}: {e}")
            # Continue processing other images instead of failing completely
            continue
    
    if not records:
        raise HTTPException(
            status_code=500,
            detail="Failed to process any images from the ZIP file"
        )
    
    logging.getLogger("uvicorn").info(f"[vd] ZIP processing complete. Returning {len(records)} records.")
    return records

