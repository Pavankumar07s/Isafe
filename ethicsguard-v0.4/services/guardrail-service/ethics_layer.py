"""EthicsLayer — the main entry point for the guardrail service.

Wraps SafetySupervisorAgent and manages shared resources (audit logger, etc.).
"""

from __future__ import annotations

import logging
import os
import sys

_SERVICE_DIR = os.path.abspath(os.path.dirname(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SERVICE_DIR, "..", ".."))
for _p in (_PROJECT_ROOT, _SERVICE_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from core.models.protect_response import ProtectResponse
from langgraph_pipeline import SafetySupervisorAgent
from shared.audit_logger import AuditLogger

logger = logging.getLogger(__name__)


class EthicsLayer:
    """High-level ethics layer wrapping the safety pipeline.

    Manages the audit logger lifecycle and provides the ``protect()`` method.
    """

    def __init__(self) -> None:
        db_path = os.getenv("AUDIT_DB_PATH", "/data/ethicsguard_audit.db")
        enable_prometheus = os.getenv("ENABLE_PROMETHEUS", "true").lower() == "true"
        enable_otel = bool(os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"))

        self._audit_logger = AuditLogger(
            db_path=db_path,
            enable_prometheus=enable_prometheus,
            enable_otel=enable_otel,
        )
        self._agent = SafetySupervisorAgent(audit_logger=self._audit_logger)

    async def protect(
        self,
        prompt: str,
        context: str = "",
        session_id: str | None = None,
        compliance_mode: str | None = None,
    ) -> ProtectResponse:
        """Evaluate a prompt through the full safety pipeline.

        Args:
            prompt: The user prompt to evaluate.
            context: Optional grounding context.
            session_id: Optional session ID for multi-turn tracking.
            compliance_mode: Regulatory mode override. Defaults to env var.

        Returns:
            A ProtectResponse with all safety assessments.
        """
        mode = compliance_mode or os.getenv("COMPLIANCE_MODE", "STANDARD")
        return await self._agent.protect(
            prompt=prompt,
            context=context,
            session_id=session_id,
            compliance_mode=mode,
        )

    async def close(self) -> None:
        """Clean up resources."""
        await self._audit_logger.close()
