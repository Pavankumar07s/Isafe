"""EthicsGuard v0.4 Dashboard — Scorecard page."""
import time
from datetime import datetime, timezone

import httpx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Scorecard — EthicsGuard", page_icon="🛡️", layout="wide")

GUARDRAIL_URL = "http://guardrail-service:8000"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _score_color(value: int) -> str:
    """Return CSS color string based on score thresholds."""
    if value >= 80:
        return "#22c55e"  # green
    if value >= 60:
        return "#f59e0b"  # amber
    return "#ef4444"      # red


def _colored_metric(label: str, value: int):
    """Render a single large metric card with color coding."""
    color = _score_color(value)
    st.markdown(
        f"""
        <div style="
            background:{color}22;
            border-left:6px solid {color};
            border-radius:8px;
            padding:18px 24px;
            text-align:center;
        ">
            <div style="font-size:0.95rem;color:#888;">{label}</div>
            <div style="font-size:2.6rem;font-weight:700;color:{color};">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _fetch_recent_requests(n: int = 50) -> list[dict]:
    """Fetch the last *n* scored requests from the guardrail service."""
    try:
        with httpx.Client(timeout=5) as client:
            resp = client.get(f"{GUARDRAIL_URL}/recent_requests", params={"limit": n})
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPError as exc:
        st.error(f"Could not reach guardrail-service: {exc}")
        return []
    except Exception as exc:
        st.error(f"Unexpected error fetching recent requests: {exc}")
        return []


def _fetch_latest_scores() -> dict:
    """Return the latest aggregated scores dict."""
    try:
        with httpx.Client(timeout=5) as client:
            resp = client.get(f"{GUARDRAIL_URL}/scores/latest")
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPError:
        return {}
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

st.title("Scorecard")
st.caption("Real-time trustworthiness scores across safety dimensions.")

# Auto-refresh toggle
auto_refresh = st.sidebar.toggle("Auto-refresh (5 s)", value=False)

# --- Scores ---
scores = _fetch_latest_scores()
safety    = scores.get("safety", 85)
toxicity  = scores.get("toxicity", 92)
bias      = scores.get("bias", 78)
halluc    = scores.get("hallucination", 70)

col1, col2, col3, col4 = st.columns(4)
with col1:
    _colored_metric("Safety", safety)
with col2:
    _colored_metric("Toxicity", toxicity)
with col3:
    _colored_metric("Bias", bias)
with col4:
    _colored_metric("Hallucination", halluc)

st.divider()

# --- Trend chart (last 50 requests) ---
st.subheader("Score Trend — Last 50 Requests")

recent = _fetch_recent_requests(50)
if recent:
    df = pd.DataFrame(recent)
    fig = go.Figure()
    for dim in ["safety", "toxicity", "bias", "hallucination"]:
        if dim in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df[dim], mode="lines+markers", name=dim.capitalize()))
    fig.update_layout(
        xaxis_title="Request #",
        yaxis_title="Score (0-100)",
        yaxis=dict(range=[0, 105]),
        height=350,
        margin=dict(t=20, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    # Placeholder data when service is unavailable
    import random
    placeholder_data = {
        "request": list(range(1, 51)),
        "safety": [random.randint(70, 100) for _ in range(50)],
        "toxicity": [random.randint(75, 100) for _ in range(50)],
        "bias": [random.randint(60, 95) for _ in range(50)],
        "hallucination": [random.randint(55, 90) for _ in range(50)],
    }
    df_placeholder = pd.DataFrame(placeholder_data)
    fig = go.Figure()
    for dim in ["safety", "toxicity", "bias", "hallucination"]:
        fig.add_trace(go.Scatter(x=df_placeholder["request"], y=df_placeholder[dim], mode="lines+markers", name=dim.capitalize()))
    fig.update_layout(
        xaxis_title="Request #",
        yaxis_title="Score (0-100)",
        yaxis=dict(range=[0, 105]),
        height=350,
        margin=dict(t=20, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.info("Showing placeholder data — guardrail-service is not reachable.")

st.divider()

# --- Recent requests table ---
st.subheader("Recent Requests")

if recent:
    table_rows = []
    for r in recent[:20]:
        table_rows.append({
            "Timestamp": r.get("timestamp", "—"),
            "Status": r.get("status", "—"),
            "Top OWASP Tag": (r.get("owasp_tags") or ["—"])[0] if isinstance(r.get("owasp_tags"), list) else r.get("owasp_tags", "—"),
            "Overall Score": r.get("overall_score", "—"),
        })
    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
else:
    placeholder_table = pd.DataFrame({
        "Timestamp": [datetime.now(timezone.utc).isoformat() for _ in range(5)],
        "Status": ["PASS", "BLOCKED", "PASS", "PASS", "BLOCKED"],
        "Top OWASP Tag": ["LLM01", "LLM02", "—", "LLM06", "LLM09"],
        "Overall Score": [92, 34, 88, 76, 28],
    })
    st.dataframe(placeholder_table, use_container_width=True, hide_index=True)

st.divider()

# --- Test a prompt ---
st.subheader("Test a Prompt")
test_prompt = st.text_area("Enter a prompt to test against EthicsGuard:", height=100)
if st.button("Submit", type="primary"):
    if not test_prompt.strip():
        st.warning("Please enter a prompt.")
    else:
        with st.spinner("Calling guardrail-service..."):
            try:
                with httpx.Client(timeout=15) as client:
                    resp = client.post(
                        f"{GUARDRAIL_URL}/protect",
                        json={"prompt": test_prompt},
                    )
                    resp.raise_for_status()
                    result = resp.json()

                status = result.get("status", "UNKNOWN")
                if status == "PASS":
                    st.success(f"**PASS** — Overall score: {result.get('overall_score', 'N/A')}")
                else:
                    st.error(f"**{status}** — Overall score: {result.get('overall_score', 'N/A')}")

                with st.expander("Full response"):
                    st.json(result)

            except httpx.ConnectError:
                st.error("Cannot connect to guardrail-service. Is it running?")
            except httpx.HTTPStatusError as exc:
                st.error(f"guardrail-service returned HTTP {exc.response.status_code}: {exc.response.text[:300]}")
            except Exception as exc:
                st.error(f"Unexpected error: {exc}")

# --- Auto-refresh ---
if auto_refresh:
    time.sleep(5)
    st.rerun()
