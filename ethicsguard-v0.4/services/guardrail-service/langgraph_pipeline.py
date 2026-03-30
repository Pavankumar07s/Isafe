"""SafetySupervisorAgent wrapper — provides the high-level pipeline interface.

Wraps ``core.langgraph_agents.safety_supervisor.run_safety_pipeline`` and
converts the raw pipeline state into a ``ProtectResponse``.
"""

from __future__ import annotations

import logging
import os
import sys
import time
from typing import Any

# Ensure project root is on the path
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from core.langgraph_agents.safety_supervisor import SafetyState, run_safety_pipeline
from core.models.audit_record import AuditRecord
from core.models.protect_response import ProtectResponse
from core.models.scorecard_result import ScorecardResult
from shared.audit_logger import AuditLogger

logger = logging.getLogger(__name__)


class SafetySupervisorAgent:
    """High-level agent wrapping the safety pipeline.

    Converts raw pipeline state to structured ProtectResponse and handles
    audit logging.
    """

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit_logger = audit_logger
        self._model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    async def protect(
        self,
        prompt: str,
        context: str = "",
        session_id: str | None = None,
        compliance_mode: str = "STANDARD",
    ) -> ProtectResponse:
        """Run the full safety pipeline and return a ProtectResponse.

        Args:
            prompt: The user prompt to evaluate.
            context: Optional grounding context.
            session_id: Optional session ID for multi-turn tracking.
            compliance_mode: Regulatory mode override.

        Returns:
            A fully populated ProtectResponse.
        """
        start = time.time()

        # Run the pipeline
        state: SafetyState = await run_safety_pipeline(
            prompt=prompt,
            session_id=session_id,
            compliance_mode=compliance_mode,
        )

        latency_ms = round((time.time() - start) * 1000, 2)

        # Build scorecard
        scorecard = ScorecardResult(
            overall=round(
                0.30 * state.get("safety_score", 50.0)
                + 0.25 * state.get("toxicity_score", 50.0)
                + 0.20 * state.get("bias_score", 50.0)
                + 0.25 * state.get("hallucination_score", 50.0),
                2,
            ),
            safety=round(state.get("safety_score", 50.0), 2),
            toxicity=round(state.get("toxicity_score", 50.0), 2),
            bias=round(state.get("bias_score", 50.0), 2),
            hallucination=round(state.get("hallucination_score", 50.0), 2),
        )

        # Build audit record
        audit_record = AuditRecord(
            prompt_hash=AuditRecord.hash_prompt(prompt),
            status=state.get("final_status", "ALLOWED"),
            owasp_tags=state.get("owasp_tags", []),
            scores={
                "safety": scorecard.safety,
                "toxicity": scorecard.toxicity,
                "bias": scorecard.bias,
                "hallucination": scorecard.hallucination,
            },
            latency_ms=latency_ms,
            model=self._model,
            session_id=session_id,
        )

        # Persist audit log
        if self._audit_logger:
            try:
                await self._audit_logger.log(audit_record)
            except Exception as exc:
                logger.error("Failed to persist audit log: %s", exc)

        # Build trace
        trace = {
            "steps": state.get("trace_steps", []),
            "total_nodes": len(state.get("trace_steps", [])),
        }

        return ProtectResponse(
            status=state.get("final_status", "ALLOWED"),
            scorecard=scorecard,
            owasp_tags=state.get("owasp_tags", []),
            compliance_flags=state.get("compliance_flags", []),
            policy_triggered=state.get("policy_triggered"),
            audit_log=audit_record,
            trace=trace,
            latency_ms=latency_ms,
        )
