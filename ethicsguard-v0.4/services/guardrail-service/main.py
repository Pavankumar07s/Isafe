"""EthicsGuard Guardrail Service — FastAPI application.

Exposes POST /protect as the main safety endpoint.
Includes rate limiting, health checks, and graceful shutdown.
"""

import asyncio
import logging
import os
import signal
import sys
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from dotenv import load_dotenv
from fastapi import Body, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

load_dotenv()

# Ensure project root and service dir are on the path
_SERVICE_DIR = os.path.abspath(os.path.dirname(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SERVICE_DIR, "..", ".."))
for _p in (_PROJECT_ROOT, _SERVICE_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from core.models.protect_response import ProtectResponse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------

_RATE_LIMIT = os.getenv("RATE_LIMIT_PER_MINUTE", "60")
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{_RATE_LIMIT}/minute"])

# ---------------------------------------------------------------------------
# Global ethics layer (initialized in lifespan)
# ---------------------------------------------------------------------------

_ethics_layer = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: init and teardown."""
    global _ethics_layer
    from ethics_layer import EthicsLayer

    _ethics_layer = EthicsLayer()
    logger.info("EthicsLayer initialized")

    yield

    # Graceful shutdown
    if _ethics_layer:
        await _ethics_layer.close()
        logger.info("EthicsLayer shut down")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="EthicsGuard Guardrail Service",
    description="AI safety middleware — evaluates prompts for safety, toxicity, bias, and hallucination risk.",
    version="0.4.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# SIGTERM handler for graceful shutdown
# ---------------------------------------------------------------------------


def _handle_sigterm(signum: int, frame: object) -> None:
    logger.info("Received SIGTERM, initiating graceful shutdown")
    raise SystemExit(0)


signal.signal(signal.SIGTERM, _handle_sigterm)

# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class ProtectRequest(BaseModel):
    """Request body for POST /protect."""

    prompt: str = Field(
        ...,
        description="The user prompt to evaluate",
        examples=["How do I hack a website?"],
    )
    context: str = Field(
        default="",
        description="Optional grounding context (e.g. RAG documents)",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session ID for multi-turn tracking",
    )
    compliance_mode: Optional[str] = Field(
        default=None,
        description="Override compliance mode: STANDARD | GDPR_EU | CCPA_CA | HIPAA_US",
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health", tags=["system"])
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "version": "0.4.0"}


@app.post("/protect", tags=["safety"])
@limiter.limit(f"{_RATE_LIMIT}/minute")
async def protect(request: Request, body: ProtectRequest):
    """Evaluate a prompt through the full EthicsGuard safety pipeline.

    Returns a ProtectResponse with status (ALLOWED/BLOCKED/FLAGGED),
    scorecard, OWASP tags, compliance flags, and full audit record.
    """
    try:
        if _ethics_layer is None:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "ERROR",
                    "error": "Service not initialized",
                    "latency_ms": 0.0,
                },
            )

        response = await _ethics_layer.protect(
            prompt=body.prompt,
            context=body.context,
            session_id=body.session_id,
            compliance_mode=body.compliance_mode,
        )
        return response

    except Exception as exc:
        logger.error("Protect endpoint error: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=200,
            content={
                "status": "ERROR",
                "error": str(exc),
                "latency_ms": 0.0,
            },
        )


@app.get("/recent_requests", tags=["dashboard"])
async def recent_requests(limit: int = 50) -> list:
    """Return last N audit log entries for the dashboard scorecard."""
    if _ethics_layer is None:
        return []
    try:
        records = await _ethics_layer._audit_logger.query(limit=limit)
        results = []
        for r in records:
            scores = r.get("scores", {})
            if isinstance(scores, str):
                import json
                scores = json.loads(scores)
            results.append({
                "timestamp": r.get("timestamp", ""),
                "status": r.get("status", "ALLOWED"),
                "owasp_tags": r.get("owasp_tags", []),
                "overall_score": round(
                    0.30 * scores.get("safety", 50)
                    + 0.25 * scores.get("toxicity", 50)
                    + 0.20 * scores.get("bias", 50)
                    + 0.25 * scores.get("hallucination", 50), 2
                ),
                "safety": scores.get("safety", 50),
                "toxicity": scores.get("toxicity", 50),
                "bias": scores.get("bias", 50),
                "hallucination": scores.get("hallucination", 50),
                "session_id": r.get("session_id"),
                "latency_ms": r.get("latency_ms", 0),
                "policy_triggered": r.get("policy_triggered"),
                "prompt_hash": r.get("prompt_hash", ""),
            })
        return results
    except Exception as exc:
        logger.warning("Failed to fetch recent requests: %s", exc)
        return []


@app.get("/scores/latest", tags=["dashboard"])
async def scores_latest() -> dict:
    """Return the latest aggregate scores for the dashboard."""
    if _ethics_layer is None:
        return {"safety": 85, "toxicity": 92, "bias": 78, "hallucination": 70}
    try:
        records = await _ethics_layer._audit_logger.query(limit=10)
        if not records:
            return {"safety": 85, "toxicity": 92, "bias": 78, "hallucination": 70}
        import json
        totals = {"safety": 0, "toxicity": 0, "bias": 0, "hallucination": 0}
        count = 0
        for r in records:
            scores = r.get("scores", {})
            if isinstance(scores, str):
                scores = json.loads(scores)
            for k in totals:
                totals[k] += scores.get(k, 50)
            count += 1
        if count > 0:
            return {k: round(v / count, 1) for k, v in totals.items()}
        return {"safety": 85, "toxicity": 92, "bias": 78, "hallucination": 70}
    except Exception as exc:
        logger.warning("Failed to compute latest scores: %s", exc)
        return {"safety": 85, "toxicity": 92, "bias": 78, "hallucination": 70}


@app.get("/audit_log", tags=["dashboard"])
async def audit_log(
    status: str | None = None,
    owasp_tags: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list:
    """Return filtered audit log entries for the dashboard."""
    if _ethics_layer is None:
        return []
    try:
        filters = {}
        if status and status != "ALL":
            filters["status"] = status
        if owasp_tags:
            filters["owasp_tag"] = owasp_tags.split(",")[0]
        if date_from:
            filters["date_from"] = date_from
        if date_to:
            filters["date_to"] = date_to
        records = await _ethics_layer._audit_logger.query(filters=filters, limit=200)
        return records
    except Exception as exc:
        logger.warning("Failed to fetch audit log: %s", exc)
        return []


@app.get("/pii_stats", tags=["dashboard"])
async def pii_stats() -> dict:
    """Return PII detection statistics."""
    if _ethics_layer is None:
        return {"total_scanned": 0, "pii_detected": 0, "pii_redacted": 0, "detection_rate": 0.0}
    try:
        records = await _ethics_layer._audit_logger.query(limit=10000)
        import json
        total = len(records)
        pii_count = 0
        for r in records:
            flags = r.get("compliance_flags", [])
            if isinstance(flags, str):
                try:
                    flags = json.loads(flags)
                except Exception:
                    flags = []
            if any("PII" in str(f) for f in flags):
                pii_count += 1
        rate = (pii_count / total * 100) if total > 0 else 0.0
        return {
            "total_scanned": total,
            "pii_detected": pii_count,
            "pii_redacted": pii_count,
            "detection_rate": round(rate, 1),
        }
    except Exception as exc:
        logger.warning("Failed to compute PII stats: %s", exc)
        return {"total_scanned": 0, "pii_detected": 0, "pii_redacted": 0, "detection_rate": 0.0}


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
