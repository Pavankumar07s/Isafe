"""ProtectResponse Pydantic model for EthicsGuard v0.4.

This is the top-level response schema returned by the ``/protect`` endpoint.
It composes :class:`ScorecardResult` and :class:`AuditRecord`.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from core.models.audit_record import AuditRecord
from core.models.scorecard_result import ScorecardResult


class ProtectResponse(BaseModel):
    """Response payload for the ``POST /protect`` endpoint."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "BLOCKED",
                    "scorecard": {
                        "overall": 22.0,
                        "safety": 15.0,
                        "toxicity": 85.0,
                        "bias": 12.0,
                        "hallucination": 5.0,
                    },
                    "owasp_tags": ["LLM01", "ASI04"],
                    "compliance_flags": ["GDPR_PII_DETECTED"],
                    "policy_triggered": "prompt_injection_block",
                    "audit_log": {
                        "id": "b4f7c2a1-8e3d-4f5a-9b6c-1d2e3f4a5b6c",
                        "timestamp": "2026-03-30T12:00:00Z",
                        "prompt_hash": "a3f1c5b2d4e6f7890123456789abcdef0123456789abcdef0123456789abcdef",
                        "status": "BLOCKED",
                        "owasp_tags": ["LLM01", "ASI04"],
                        "scores": {
                            "safety": 15.0,
                            "toxicity": 85.0,
                            "bias": 12.0,
                            "hallucination": 5.0,
                        },
                        "latency_ms": 42.7,
                        "model": "gpt-4o",
                        "session_id": None,
                    },
                    "trace": {
                        "steps": [
                            "input_validation",
                            "toxicity_check",
                            "bias_check",
                            "hallucination_check",
                            "policy_engine",
                        ],
                        "total_nodes": 5,
                    },
                    "latency_ms": 42.7,
                }
            ]
        },
    }

    status: Literal["ALLOWED", "BLOCKED", "FLAGGED"] = Field(
        ...,
        description="Final disposition of the guarded request.",
        examples=["BLOCKED"],
    )
    scorecard: ScorecardResult = Field(
        ...,
        description="Detailed numeric scores from the scoring pipeline.",
    )
    owasp_tags: list[str] = Field(
        default_factory=list,
        description="OWASP LLM Top-10 / ASI tags triggered (e.g. LLM01, ASI04).",
        examples=[["LLM01", "ASI04"]],
    )
    compliance_flags: list[str] = Field(
        default_factory=list,
        description="Compliance/regulatory flags raised (e.g. GDPR_PII_DETECTED).",
        examples=[["GDPR_PII_DETECTED"]],
    )
    policy_triggered: str | None = Field(
        default=None,
        description="Identifier of the policy rule that caused a BLOCK/FLAG, if any.",
        examples=["prompt_injection_block"],
    )
    audit_log: AuditRecord = Field(
        ...,
        description="The full audit record persisted for this request.",
    )
    trace: dict[str, Any] = Field(
        default_factory=lambda: {"steps": [], "total_nodes": 0},
        description="Execution trace with a 'steps' list and 'total_nodes' count.",
        examples=[
            {
                "steps": [
                    "input_validation",
                    "toxicity_check",
                    "bias_check",
                    "hallucination_check",
                    "policy_engine",
                ],
                "total_nodes": 5,
            }
        ],
    )
    latency_ms: float = Field(
        ...,
        ge=0.0,
        description="Total end-to-end latency for the /protect call in milliseconds.",
        examples=[42.7],
    )


# ------------------------------------------------------------------
# Quick smoke-test
# ------------------------------------------------------------------
if __name__ == "__main__":
    prompt_hash = AuditRecord.hash_prompt("Tell me how to hack a server")

    scorecard = ScorecardResult(
        overall=22.0,
        safety=15.0,
        toxicity=85.0,
        bias=12.0,
        hallucination=5.0,
    )

    audit = AuditRecord(
        prompt_hash=prompt_hash,
        status="BLOCKED",
        owasp_tags=["LLM01", "ASI04"],
        scores={
            "safety": 15.0,
            "toxicity": 85.0,
            "bias": 12.0,
            "hallucination": 5.0,
        },
        latency_ms=42.7,
        model="gpt-4o",
    )

    response = ProtectResponse(
        status="BLOCKED",
        scorecard=scorecard,
        owasp_tags=["LLM01", "ASI04"],
        compliance_flags=["GDPR_PII_DETECTED"],
        policy_triggered="prompt_injection_block",
        audit_log=audit,
        trace={
            "steps": [
                "input_validation",
                "toxicity_check",
                "bias_check",
                "hallucination_check",
                "policy_engine",
            ],
            "total_nodes": 5,
        },
        latency_ms=42.7,
    )

    print("=== ProtectResponse sample ===")
    print(response.model_dump_json(indent=2))
