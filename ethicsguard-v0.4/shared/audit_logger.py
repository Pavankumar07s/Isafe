"""Structured audit logging with SQLite persistence, Prometheus metrics, and OpenTelemetry.

Every /protect call produces an AuditRecord that is:
1. Inserted into an async SQLite database
2. Counted via Prometheus metrics (if enabled)
3. Traced via OpenTelemetry spans (if enabled)
"""

from __future__ import annotations

import csv
import io
import json
import logging
import os
from typing import Any

import aiosqlite
import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Optional imports — gracefully degrade if not installed
# ---------------------------------------------------------------------------

_prometheus_available = False
try:
    from prometheus_client import Counter, Histogram
    _prometheus_available = True
except ImportError:
    pass

_otel_available = False
try:
    from opentelemetry import trace as otel_trace
    _otel_available = True
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Prometheus metrics (module-level singletons)
# ---------------------------------------------------------------------------

if _prometheus_available:
    REQUESTS_TOTAL = Counter(
        "ethicsguard_requests_total",
        "Total requests processed by EthicsGuard",
        ["status"],
    )
    LATENCY_HISTOGRAM = Histogram(
        "ethicsguard_latency_seconds",
        "Request latency in seconds",
        buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
    )
    OWASP_TAGS_TOTAL = Counter(
        "ethicsguard_owasp_tags_total",
        "OWASP tags triggered",
        ["tag"],
    )


# ---------------------------------------------------------------------------
# SQL schema
# ---------------------------------------------------------------------------

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    prompt_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    owasp_tags TEXT NOT NULL,
    scores TEXT NOT NULL,
    latency_ms REAL NOT NULL,
    model TEXT NOT NULL,
    session_id TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
"""

_INSERT_SQL = """
INSERT INTO audit_log (id, timestamp, prompt_hash, status, owasp_tags, scores, latency_ms, model, session_id)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


# ---------------------------------------------------------------------------
# AuditLogger
# ---------------------------------------------------------------------------


class AuditLogger:
    """Async audit logger backed by SQLite with optional Prometheus and OTEL.

    Args:
        db_path: Path to the SQLite database file.
        enable_prometheus: Whether to emit Prometheus counters/histograms.
        enable_otel: Whether to create OpenTelemetry spans.
    """

    def __init__(
        self,
        db_path: str = "/data/ethicsguard_audit.db",
        enable_prometheus: bool = True,
        enable_otel: bool = False,
    ) -> None:
        self.db_path = db_path
        self.enable_prometheus = enable_prometheus and _prometheus_available
        self.enable_otel = enable_otel and _otel_available
        self._db: aiosqlite.Connection | None = None

    async def _ensure_db(self) -> aiosqlite.Connection:
        """Lazy-open the database connection and create the table."""
        if self._db is None:
            os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
            self._db = await aiosqlite.connect(self.db_path)
            await self._db.execute(_CREATE_TABLE_SQL)
            await self._db.commit()
        return self._db

    async def log(self, record: Any) -> None:
        """Persist an AuditRecord to SQLite and emit metrics.

        Args:
            record: An ``AuditRecord`` instance (or any object with the same
                attributes: id, timestamp, prompt_hash, status, owasp_tags,
                scores, latency_ms, model, session_id).
        """
        db = await self._ensure_db()

        # SQLite insert
        await db.execute(
            _INSERT_SQL,
            (
                record.id,
                record.timestamp,
                record.prompt_hash,
                record.status,
                json.dumps(record.owasp_tags),
                json.dumps(record.scores),
                record.latency_ms,
                record.model,
                record.session_id,
            ),
        )
        await db.commit()

        # Prometheus
        if self.enable_prometheus and _prometheus_available:
            REQUESTS_TOTAL.labels(status=record.status).inc()
            LATENCY_HISTOGRAM.observe(record.latency_ms / 1000.0)
            for tag in record.owasp_tags:
                OWASP_TAGS_TOTAL.labels(tag=tag).inc()

        # OpenTelemetry
        if self.enable_otel and _otel_available:
            tracer = otel_trace.get_tracer("ethicsguard.audit")
            with tracer.start_as_current_span("audit_log") as span:
                span.set_attribute("audit.id", record.id)
                span.set_attribute("audit.status", record.status)
                span.set_attribute("audit.latency_ms", record.latency_ms)
                span.set_attribute("audit.owasp_tags", json.dumps(record.owasp_tags))

        logger.info(
            "audit_logged",
            audit_id=record.id,
            status=record.status,
            latency_ms=record.latency_ms,
            owasp_tags=record.owasp_tags,
        )

    async def query(
        self, filters: dict[str, Any] | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Query audit records with optional filters.

        Args:
            filters: Optional dict with keys: ``status``, ``owasp_tag``,
                ``session_id``, ``date_from``, ``date_to``.
            limit: Max rows to return.

        Returns:
            List of dicts matching the query.
        """
        db = await self._ensure_db()
        conditions: list[str] = []
        params: list[Any] = []
        filters = filters or {}

        if "status" in filters:
            conditions.append("status = ?")
            params.append(filters["status"])

        if "owasp_tag" in filters:
            conditions.append("owasp_tags LIKE ?")
            params.append(f"%{filters['owasp_tag']}%")

        if "session_id" in filters:
            conditions.append("session_id = ?")
            params.append(filters["session_id"])

        if "date_from" in filters:
            conditions.append("timestamp >= ?")
            params.append(filters["date_from"])

        if "date_to" in filters:
            conditions.append("timestamp <= ?")
            params.append(filters["date_to"])

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        sql = f"SELECT * FROM audit_log WHERE {where_clause} ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        async with db.execute(sql, params) as cursor:
            columns = [desc[0] for desc in cursor.description]
            rows = await cursor.fetchall()

        results: list[dict[str, Any]] = []
        for row in rows:
            record = dict(zip(columns, row))
            record["owasp_tags"] = json.loads(record["owasp_tags"])
            record["scores"] = json.loads(record["scores"])
            results.append(record)

        return results

    async def export_csv(self, filters: dict[str, Any] | None = None) -> str:
        """Export filtered audit records as a CSV string.

        Args:
            filters: Same filters as :meth:`query`.

        Returns:
            CSV-formatted string.
        """
        records = await self.query(filters=filters, limit=10000)
        if not records:
            return ""

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=records[0].keys())
        writer.writeheader()
        for record in records:
            # Flatten complex fields for CSV
            row = dict(record)
            row["owasp_tags"] = json.dumps(row["owasp_tags"])
            row["scores"] = json.dumps(row["scores"])
            writer.writerow(row)

        return output.getvalue()

    async def close(self) -> None:
        """Close the database connection."""
        if self._db is not None:
            await self._db.close()
            self._db = None


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import asyncio
    import sys
    import tempfile

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from core.models.audit_record import AuditRecord

    async def _test() -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_audit.db")
            audit_logger = AuditLogger(db_path=db_path, enable_prometheus=False, enable_otel=False)

            # Log a record
            record = AuditRecord(
                prompt_hash=AuditRecord.hash_prompt("test prompt"),
                status="BLOCKED",
                owasp_tags=["LLM01", "ASI04"],
                scores={"safety": 15.0, "toxicity": 88.0, "bias": 92.0, "hallucination": 85.0},
                latency_ms=42.5,
                model="gpt-4o-mini",
            )
            await audit_logger.log(record)
            print("[PASS] Record logged")

            # Query
            results = await audit_logger.query()
            assert len(results) == 1, f"Expected 1 record, got {len(results)}"
            assert results[0]["status"] == "BLOCKED"
            print("[PASS] Query returned 1 record")

            # Export CSV
            csv_str = await audit_logger.export_csv()
            assert "BLOCKED" in csv_str
            print("[PASS] CSV export contains record")

            await audit_logger.close()
            print("\nAll tests passed.")

    print("=== AuditLogger self-test ===\n")
    asyncio.run(_test())
