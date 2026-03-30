"""AuditRecord Pydantic model for EthicsGuard v0.4.

Stores an immutable audit trail entry for every /protect invocation.
The raw prompt is NEVER stored -- only a SHA-256 hash.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class AuditRecord(BaseModel):
    """Immutable record written to the audit log for each request."""

    model_config = {
        "frozen": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "b4f7c2a1-8e3d-4f5a-9b6c-1d2e3f4a5b6c",
                    "timestamp": "2026-03-30T12:00:00Z",
                    "prompt_hash": "a3f1c5b2d4e6f7890123456789abcdef0123456789abcdef0123456789abcdef",
                    "status": "ALLOWED",
                    "owasp_tags": ["LLM01"],
                    "scores": {
                        "safety": 95.0,
                        "toxicity": 2.1,
                        "bias": 5.3,
                        "hallucination": 8.0,
                    },
                    "latency_ms": 42.7,
                    "model": "gpt-4o",
                    "session_id": "sess-abc-123",
                }
            ]
        },
    }

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this audit record (UUID v4).",
        examples=["b4f7c2a1-8e3d-4f5a-9b6c-1d2e3f4a5b6c"],
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 timestamp of when the request was processed.",
        examples=["2026-03-30T12:00:00Z"],
    )
    prompt_hash: str = Field(
        ...,
        min_length=64,
        max_length=64,
        description="SHA-256 hex digest of the original prompt. Raw prompts are NEVER stored.",
        examples=["a3f1c5b2d4e6f7890123456789abcdef0123456789abcdef0123456789abcdef"],
    )
    status: Literal["ALLOWED", "BLOCKED", "FLAGGED"] = Field(
        ...,
        description="Final disposition of the request.",
        examples=["ALLOWED"],
    )
    owasp_tags: list[str] = Field(
        default_factory=list,
        description="OWASP LLM / ASI tags triggered by this request.",
        examples=[["LLM01", "LLM02"]],
    )
    scores: dict[str, float] = Field(
        ...,
        description="Numeric scores keyed by dimension (safety, toxicity, bias, hallucination).",
        examples=[{"safety": 95.0, "toxicity": 2.1, "bias": 5.3, "hallucination": 8.0}],
    )
    latency_ms: float = Field(
        ...,
        ge=0.0,
        description="End-to-end processing latency in milliseconds.",
        examples=[42.7],
    )
    model: str = Field(
        ...,
        description="Identifier of the LLM model that was guarded.",
        examples=["gpt-4o"],
    )
    session_id: str | None = Field(
        default=None,
        description="Optional session identifier for multi-turn conversations.",
        examples=["sess-abc-123"],
    )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def hash_prompt(raw_prompt: str) -> str:
        """Return the SHA-256 hex digest of *raw_prompt*."""
        return hashlib.sha256(raw_prompt.encode("utf-8")).hexdigest()

    @model_validator(mode="after")
    def _validate_score_keys(self) -> "AuditRecord":
        """Ensure all four required score dimensions are present."""
        required_keys = {"safety", "toxicity", "bias", "hallucination"}
        missing = required_keys - set(self.scores.keys())
        if missing:
            raise ValueError(f"scores dict is missing required keys: {missing}")
        return self


# ------------------------------------------------------------------
# Quick smoke-test
# ------------------------------------------------------------------
if __name__ == "__main__":
    sample_hash = AuditRecord.hash_prompt("Tell me how to hack a server")
    record = AuditRecord(
        prompt_hash=sample_hash,
        status="BLOCKED",
        owasp_tags=["LLM01", "ASI04"],
        scores={
            "safety": 12.0,
            "toxicity": 88.5,
            "bias": 4.2,
            "hallucination": 1.0,
        },
        latency_ms=37.2,
        model="gpt-4o",
        session_id="sess-demo-001",
    )
    print("=== AuditRecord sample ===")
    print(record.model_dump_json(indent=2))
