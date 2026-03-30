"""
EthicsGuard v0.4 - Evaluation Service
FastAPI application for running guardrail evaluations and generating reports.
"""

import asyncio
import os
import signal
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Project-root sys.path setup
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

# Local imports — directory uses hyphens so standard dotted imports won't work.
# sys.path already includes PROJECT_ROOT; add this service directory too.
_SERVICE_DIR = Path(__file__).resolve().parent
if str(_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVICE_DIR))

from eval_runner import EvalRunner
from report_generator import ReportGenerator

# ---------------------------------------------------------------------------
# Dataset path resolution
# ---------------------------------------------------------------------------
EVAL_DIR = PROJECT_ROOT / "evaluation"
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

DATASET_MAP = {
    "2026_full": EVAL_DIR / "2026_attack_dataset.csv",
    "harmbench": EVAL_DIR / "harmbench_subset.csv",
}

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="EthicsGuard Evaluation Service",
    version="0.4.0",
    description="Runs adversarial evaluations against guardrail targets and generates PDF reports.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory job store
# ---------------------------------------------------------------------------
eval_jobs: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------
class RunEvalRequest(BaseModel):
    dataset: str = Field(
        default="2026_full",
        description="Dataset identifier: 2026_full, harmbench, or an absolute path for custom.",
    )
    baselines: list[str] = Field(
        default_factory=lambda: ["openai_mod", "gpt4o_raw", "llamaguard"],
        description="List of baseline targets to compare against.",
    )


class RunEvalResponse(BaseModel):
    eval_id: str
    status: str
    estimated_minutes: int


class EvalStatusResponse(BaseModel):
    eval_id: str
    status: str  # running | complete | failed
    progress: float  # 0.0 - 1.0
    results: Optional[dict] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Background evaluation task
# ---------------------------------------------------------------------------
async def _run_evaluation_task(eval_id: str, dataset_path: str, baselines: list[str]):
    """Execute the evaluation in the background and update the job store."""
    job = eval_jobs[eval_id]

    async def _progress_cb(progress: float):
        job["progress"] = round(progress, 4)

    runner = EvalRunner()
    try:
        results = await runner.run_evaluation(
            dataset_path=dataset_path,
            target="ethicsguard",
            baselines=baselines,
            progress_callback=_progress_cb,
        )

        # Convert EvalResult objects to dicts
        results_dict = {name: res.to_dict() for name, res in results.items()}

        # Generate PDF report
        report_gen = ReportGenerator()
        report_path = str(REPORTS_DIR / f"eval_report_{eval_id}.pdf")
        report_gen.generate_report(results_dict, report_path)

        job["status"] = "complete"
        job["progress"] = 1.0
        job["results"] = results_dict
        job["report_path"] = report_path
        job["completed_at"] = datetime.now(timezone.utc).isoformat()

    except Exception as exc:
        job["status"] = "failed"
        job["error"] = str(exc)
        job["completed_at"] = datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.post("/run_eval", response_model=RunEvalResponse)
async def run_eval(request: RunEvalRequest):
    """Start a new evaluation job."""
    # Resolve dataset path
    if request.dataset in DATASET_MAP:
        dataset_path = str(DATASET_MAP[request.dataset])
    elif os.path.isabs(request.dataset) and os.path.isfile(request.dataset):
        dataset_path = request.dataset
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown dataset '{request.dataset}'. "
            f"Valid options: {list(DATASET_MAP.keys())} or an absolute file path.",
        )

    eval_id = str(uuid.uuid4())
    num_baselines = len(request.baselines)
    estimated_minutes = max(1, 5 + num_baselines * 3)  # rough estimate

    eval_jobs[eval_id] = {
        "eval_id": eval_id,
        "status": "running",
        "progress": 0.0,
        "results": None,
        "report_path": None,
        "error": None,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "dataset": request.dataset,
        "baselines": request.baselines,
    }

    # Fire background task
    asyncio.create_task(
        _run_evaluation_task(eval_id, dataset_path, request.baselines)
    )

    return RunEvalResponse(
        eval_id=eval_id,
        status="running",
        estimated_minutes=estimated_minutes,
    )


@app.get("/eval_status/{eval_id}", response_model=EvalStatusResponse)
async def eval_status(eval_id: str):
    """Check the status of an evaluation job."""
    if eval_id not in eval_jobs:
        raise HTTPException(status_code=404, detail="Evaluation job not found.")
    job = eval_jobs[eval_id]
    return EvalStatusResponse(
        eval_id=job["eval_id"],
        status=job["status"],
        progress=job["progress"],
        results=job["results"],
        error=job.get("error"),
    )


@app.get("/report/{eval_id}")
async def get_report(eval_id: str):
    """Download the PDF evaluation report."""
    if eval_id not in eval_jobs:
        raise HTTPException(status_code=404, detail="Evaluation job not found.")
    job = eval_jobs[eval_id]
    if job["status"] != "complete":
        raise HTTPException(
            status_code=409,
            detail=f"Report not ready. Job status: {job['status']}",
        )
    report_path = job.get("report_path")
    if not report_path or not os.path.isfile(report_path):
        raise HTTPException(status_code=500, detail="Report file missing.")
    return FileResponse(
        report_path,
        media_type="application/pdf",
        filename=f"ethicsguard_eval_{eval_id}.pdf",
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.4.0"}


# ---------------------------------------------------------------------------
# Graceful shutdown
# ---------------------------------------------------------------------------
def _handle_sigterm(*_):
    """Handle SIGTERM for graceful container shutdown."""
    raise SystemExit(0)


signal.signal(signal.SIGTERM, _handle_sigterm)

# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
    )
