import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
from starlette.concurrency import run_in_threadpool
from app.services.ai_engine import ai_engine
from app.api.v1.endpoints.auth import get_current_user, require_role
from app.core.database import utc_now, format_iso_z

router = APIRouter()

# In-memory background training jobs tracker
training_jobs: Dict[str, Dict[str, Any]] = {}

class PredictRequest(BaseModel):
    text: str

def _run_training_job_sync(job_id: str):
    """Synchronous worker function executed in the background."""
    job = training_jobs.get(job_id)
    if not job:
        return
    job["status"] = "running"
    job["started_at"] = format_iso_z(utc_now())
    try:
        updated_metrics = ai_engine.trigger_retraining()
        job["status"] = "completed"
        job["completed_at"] = format_iso_z(utc_now())
        job["result"] = updated_metrics
    except Exception as e:
        job["status"] = "failed"
        job["completed_at"] = format_iso_z(utc_now())
        job["error"] = str(e)

@router.get("/dataset-info")
async def get_dataset_info(current_user: dict = Depends(get_current_user)):
    """Returns dataset overview, sample counts, and class distributions."""
    data = await run_in_threadpool(ai_engine.get_dataset_overview)
    return data

@router.get("/metrics")
async def get_model_metrics(current_user: dict = Depends(get_current_user)):
    """Returns the latest evaluation report, operational model statuses, and performance metrics."""
    metrics = await run_in_threadpool(ai_engine.get_model_metrics)
    return metrics

@router.post("/predict")
async def run_live_prediction(payload: PredictRequest, current_user: dict = Depends(get_current_user)):
    """Runs live NLP prediction using the trained Apple smartphone model via threadpool."""
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text input cannot be empty.")
    
    result = await run_in_threadpool(ai_engine.predict_full_nlp, payload.text)
    return result

@router.post("/train")
async def trigger_model_retraining(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_role("admin"))
):
    """
    Initiates model retraining on the Apple smartphone Kaggle dataset as an asynchronous background job.
    Returns a job_id for status tracking.
    """
    job_id = f"job_train_{uuid.uuid4().hex[:8]}"
    training_jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "created_at": format_iso_z(utc_now()),
        "started_at": None,
        "completed_at": None,
        "result": None,
        "error": None
    }
    background_tasks.add_task(_run_training_job_sync, job_id)
    return {
        "status": "queued",
        "job_id": job_id,
        "message": "Model retraining initiated in the background."
    }

@router.get("/train/{job_id}")
async def get_training_job_status(job_id: str, current_user: dict = Depends(get_current_user)):
    """Returns the progress, status, and metrics of a model retraining job."""
    if job_id not in training_jobs:
        raise HTTPException(status_code=404, detail="Training job not found")
    return training_jobs[job_id]
