"""EthicsGuard v0.4 Dashboard — Audit Log page."""
from datetime import date, datetime, timedelta, timezone
from io import StringIO

import httpx
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Audit Log — EthicsGuard", page_icon="🛡️", layout="wide")

import os

GUARDRAIL_URL = os.environ.get("GUARDRAIL_URL", "http://localhost:8000")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OWASP_TAGS = [
    "LLM01", "LLM02", "LLM03", "LLM04", "LLM05",
    "LLM06", "LLM07", "LLM08", "LLM09", "LLM10",
    "ASI01", "ASI02", "ASI03", "ASI04", "ASI05",
    "ASI06", "ASI07", "ASI08", "ASI09", "ASI10",
]

STATUS_OPTIONS = ["ALL", "ALLOWED", "BLOCKED", "FLAGGED"]

# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

def _fetch_audit_log(
    owasp_filter: list[str] | None = None,
    status_filter: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> pd.DataFrame:
    """Fetch audit log entries from the guardrail service."""
    params: dict = {}
    if owasp_filter:
        params["owasp_tags"] = ",".join(owasp_filter)
    if status_filter and status_filter != "ALL":
        params["status"] = status_filter
    if date_from:
        params["date_from"] = date_from.isoformat()
    if date_to:
        params["date_to"] = date_to.isoformat()

    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(f"{GUARDRAIL_URL}/audit_log", params=params)
            resp.raise_for_status()
            records = resp.json()
            if records:
                return pd.DataFrame(records)
    except httpx.ConnectError:
        st.error("Cannot connect to guardrail-service. Is it running?")
    except httpx.HTTPStatusError as exc:
        st.error(f"guardrail-service returned HTTP {exc.response.status_code}")
    except Exception as exc:
        st.error(f"Error fetching audit log: {exc}")

    return pd.DataFrame()


def _placeholder_audit_log() -> pd.DataFrame:
    """Return placeholder data when the service is unreachable."""
    now = datetime.now(timezone.utc)
    rows = []
    for i in range(25):
        ts = now - timedelta(minutes=i * 3)
        rows.append({
            "timestamp": ts.isoformat(),
            "session_id": f"sess-{1000 + i:04d}",
            "status": "ALLOWED" if i % 3 != 0 else "BLOCKED",
            "policy_triggered": "toxicity_filter" if i % 3 == 0 else "—",
            "owasp_tags": f"LLM{(i % 10) + 1:02d}",
            "latency_ms": round(12.5 + i * 1.3, 1),
            "prompt_hash": f"sha256:{i:064x}",
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------

st.sidebar.header("Filters")

selected_tags = st.sidebar.multiselect("OWASP Tags", OWASP_TAGS)
selected_status = st.sidebar.selectbox("Status", STATUS_OPTIONS)

today = date.today()
default_from = today - timedelta(days=7)
date_from = st.sidebar.date_input("From", value=default_from)
date_to = st.sidebar.date_input("To", value=today)

# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

st.title("Audit Log")
st.caption(
    "Searchable audit trail of all guardrail decisions. "
    "Prompts are NOT displayed — only `prompt_hash` is stored (GDPR compliance)."
)

# Fetch data
df = _fetch_audit_log(
    owasp_filter=selected_tags or None,
    status_filter=selected_status,
    date_from=date_from,
    date_to=date_to,
)

if df.empty:
    st.info("No live data available — showing placeholder entries.")
    df = _placeholder_audit_log()

# Search box
search_query = st.text_input("Search (filters across all columns):")
if search_query:
    mask = df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)
    df = df[mask]

# Display
DISPLAY_COLUMNS = [
    "timestamp",
    "session_id",
    "status",
    "policy_triggered",
    "owasp_tags",
    "latency_ms",
    "prompt_hash",
]
available_cols = [c for c in DISPLAY_COLUMNS if c in df.columns]
st.dataframe(
    df[available_cols] if available_cols else df,
    use_container_width=True,
    hide_index=True,
    height=500,
)

st.caption(f"Showing {len(df)} entries.")

# --- Export CSV ---
st.divider()

csv_buffer = StringIO()
df.to_csv(csv_buffer, index=False)
csv_bytes = csv_buffer.getvalue().encode("utf-8")

st.download_button(
    label="Export CSV",
    data=csv_bytes,
    file_name=f"ethicsguard_audit_log_{today.isoformat()}.csv",
    mime="text/csv",
)
