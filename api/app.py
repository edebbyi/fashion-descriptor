from __future__ import annotations
from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pathlib import Path
import os, uuid, shutil, json
from typing import List, Optional
from src.visual_descriptor.engine import Engine


API_KEY = os.getenv("API_KEY", "charlie305$")
app = FastAPI(title="Visual Descriptor API", version="1.0.0")
engine = Engine(model=os.getenv("VD_MODEL", "stub"))
BASE = Path(os.getenv("BASE_DIR", ".")).resolve()
( BASE / "uploads" ).mkdir(parents=True, exist_ok=True)
( BASE / "outputs" ).mkdir(parents=True, exist_ok=True)


class JobResponse(BaseModel):
job_id: str
status: str
records: list[dict] = []


@app.get("/healthz")
async def healthz():
return {"status": "ok"}


@app.post("/v1/jobs", response_model=JobResponse)
async def create_job(
authorization: Optional[str] = Header(None),
passes: str = Form("A,B,C"),
file: UploadFile | None = File(None),
):
if authorization is None or not authorization.endswith(API_KEY):
raise HTTPException(status_code=401, detail="Unauthorized")


job_id = f"j_{uuid.uuid4().hex[:8]}"
work_dir = BASE / "uploads" / job_id
out_dir = BASE / "outputs" / job_id
work_dir.mkdir(parents=True, exist_ok=True)
(out_dir / "json").mkdir(parents=True, exist_ok=True)


if file is None:
raise HTTPException(status_code=400, detail="Upload a file via multipart/form-data key 'file'")


fp = work_dir / file.filename
with open(fp, "wb") as f:
shutil.copyfileobj(file.file, f)


rec = engine.describe_image(fp, passes=passes.split(','))
with open(out_dir / "json" / f"{fp.stem}.json", "w") as f:
json.dump(rec, f, indent=2, ensure_ascii=False)


return JobResponse(job_id=job_id, status="completed", records=[rec])