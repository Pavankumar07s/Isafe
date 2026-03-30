"""EthicsGuard v0.4 -- core data models.

Re-exports the three primary Pydantic models so consumers can write::

    from core.models import AuditRecord, ScorecardResult, ProtectResponse
"""

from core.models.audit_record import AuditRecord
from core.models.protect_response import ProtectResponse
from core.models.scorecard_result import ScorecardResult

__all__: list[str] = [
    "AuditRecord",
    "ProtectResponse",
    "ScorecardResult",
]
