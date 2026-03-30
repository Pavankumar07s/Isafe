"""EthicsGuard Guardrail Service — FastAPI application.

Exposes POST /protect as the main safety endpoint.
Includes rate limiting, health checks, and graceful shutdown.
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
from contextlib import asynccontextmanager
from typing import AsyncIterator

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

load_dotenv()

# Ensure project root is on the path
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

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
    from services.guardrail_service.ethics_layer import EthicsLayer

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
        examples=[""],
    )
    session_id: str | None = Field(
        default=None,
        description="Optional session ID for multi-turn tracking",
        examples=["session-abc-123"],
    )
    compliance_mode: str | None = Field(
        default=None,
        description="Override compliance mode: STANDARD | GDPR_EU | CCPA_CA | HIPAA_US",
        examples=["STANDARD"],
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health", tags=["system"])
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "version": "0.4.0"}


@app.post("/protect", response_model=ProtectResponse, tags=["safety"])
@limiter.limit(f"{_RATE_LIMIT}/minute")
async def protect(request: Request, body: ProtectRequest) -> ProtectResponse | JSONResponse:
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


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "services.guardrail_service.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
