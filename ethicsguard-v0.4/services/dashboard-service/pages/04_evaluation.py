"""EthicsGuard v0.4 Dashboard — Evaluation page."""
import time

import httpx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Evaluation — EthicsGuard", page_icon="🛡️", layout="wide")

EVAL_URL = "http://evaluation-service:8002"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ATTACK_CATEGORIES = [
    "prompt_injection",
    "jailbreak",
    "encoding",
    "multilingual",
    "semantic_smuggling",
    "context_overflow",
    "few_shot_poisoning",
    "tool_abuse",
    "crescendo",
]

SYSTEMS = ["EthicsGuard", "GPT-4o Raw", "OpenAI Mod", "LlamaGuard"]

# Pre-loaded placeholder results
PLACEHOLDER_SUMMARY = pd.DataFrame({
    "System": SYSTEMS,
    "ASR (%)": [4.2, 38.7, 22.1, 15.6],
    "FPR (%)": [2.1, 0.0, 5.3, 3.8],
    "FNR (%)": [4.2, 38.7, 22.1, 15.6],
    "Latency p95 (ms)": [45, 12, 85, 120],
})

PLACEHOLDER_ASR_BY_CATEGORY = {
    cat: {
        "EthicsGuard": round(2 + i * 0.5, 1),
        "GPT-4o Raw": round(25 + i * 3, 1),
        "OpenAI Mod": round(15 + i * 1.8, 1),
        "LlamaGuard": round(10 + i * 1.5, 1),
    }
    for i, cat in enumerate(ATTACK_CATEGORIES)
}


def _start_eval() -> str | None:
    """Start a full evaluation run; return the eval_id or None on failure."""
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.post(f"{EVAL_URL}/run_eval")
            resp.raise_for_status()
            return resp.json().get("eval_id")
    except httpx.ConnectError:
        st.error("Cannot connect to evaluation-service. Is it running?")
    except httpx.HTTPStatusError as exc:
        st.error(f"evaluation-service returned HTTP {exc.response.status_code}")
    except Exception as exc:
        st.error(f"Error starting evaluation: {exc}")
    return None


def _poll_status(eval_id: str) -> dict:
    """Poll evaluation status; return the latest status dict."""
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(f"{EVAL_URL}/eval_status/{eval_id}")
            resp.raise_for_status()
            return resp.json()
    except Exception:
        return {"status": "error"}


def _fetch_results(eval_id: str) -> dict | None:
    """Fetch completed evaluation results."""
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(f"{EVAL_URL}/eval_status/{eval_id}")
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        st.error(f"Error fetching results: {exc}")
        return None


def _download_report(eval_id: str) -> bytes | None:
    """Download the PDF report for a completed evaluation."""
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(f"{EVAL_URL}/report/{eval_id}")
            resp.raise_for_status()
            return resp.content
    except httpx.ConnectError:
        st.error("Cannot connect to evaluation-service.")
    except httpx.HTTPStatusError as exc:
        st.error(f"evaluation-service returned HTTP {exc.response.status_code}")
    except Exception as exc:
        st.error(f"Error downloading report: {exc}")
    return None


def _render_asr_chart(asr_by_category: dict[str, dict[str, float]]):
    """Render a side-by-side bar chart of ASR per attack category."""
    categories = list(asr_by_category.keys())
    fig = go.Figure()
    colors = ["#3b82f6", "#f59e0b", "#ef4444", "#22c55e"]
    for idx, system in enumerate(SYSTEMS):
        values = [asr_by_category[cat].get(system, 0) for cat in categories]
        fig.add_trace(go.Bar(name=system, x=categories, y=values, marker_color=colors[idx]))
    fig.update_layout(
        barmode="group",
        yaxis_title="ASR (%)",
        yaxis=dict(range=[0, 100]),
        height=450,
        margin=dict(t=20, b=60),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_summary_table(summary_df: pd.DataFrame):
    """Render the summary comparison table."""
    st.dataframe(
        summary_df.style.format({
            "ASR (%)": "{:.1f}",
            "FPR (%)": "{:.1f}",
            "FNR (%)": "{:.1f}",
            "Latency p95 (ms)": "{:.0f}",
        }),
        use_container_width=True,
        hide_index=True,
    )


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

st.title("Evaluation")
st.caption("Run comprehensive benchmark evaluations and compare systems.")

# Session state
if "eval_id" not in st.session_state:
    st.session_state.eval_id = None
if "eval_results" not in st.session_state:
    st.session_state.eval_results = None

# --- Run evaluation ---
if st.button("Run Full Evaluation", type="primary"):
    eval_id = _start_eval()
    if eval_id:
        st.session_state.eval_id = eval_id
        st.session_state.eval_results = None

        progress_bar = st.progress(0, text="Evaluation starting...")
        status_text = st.empty()

        completed = False
        while not completed:
            time.sleep(3)
            status = _poll_status(eval_id)
            state = status.get("status", "unknown")
            progress = status.get("progress", 0)

            progress_bar.progress(
                min(progress / 100.0, 1.0) if isinstance(progress, (int, float)) else 0,
                text=f"Status: {state} ({progress}%)",
            )
            status_text.text(f"Eval ID: {eval_id} | State: {state}")

            if state in ("completed", "done", "finished"):
                progress_bar.progress(1.0, text="Evaluation complete!")
                completed = True
                results = _fetch_results(eval_id)
                st.session_state.eval_results = results
            elif state in ("error", "failed"):
                st.error(f"Evaluation failed: {status.get('error', 'Unknown error')}")
                break

        st.rerun()

# --- Results section ---
st.divider()

results = st.session_state.eval_results
eval_id = st.session_state.eval_id

if results and results.get("status") in ("completed", "done", "finished"):
    st.subheader("Evaluation Results")

    # Parse results
    asr_data = results.get("asr_by_category", PLACEHOLDER_ASR_BY_CATEGORY)
    summary_data = results.get("summary")
    if summary_data and isinstance(summary_data, list):
        summary_df = pd.DataFrame(summary_data)
    else:
        summary_df = PLACEHOLDER_SUMMARY

    # ASR chart
    st.markdown("#### ASR per Attack Category")
    _render_asr_chart(asr_data)

    # Summary table
    st.markdown("#### System Comparison Summary")
    _render_summary_table(summary_df)

    # Download PDF report
    st.divider()
    if st.button("Download PDF Report"):
        if eval_id:
            with st.spinner("Generating report..."):
                pdf_bytes = _download_report(eval_id)
            if pdf_bytes:
                st.download_button(
                    label="Save PDF",
                    data=pdf_bytes,
                    file_name=f"ethicsguard_eval_{eval_id}.pdf",
                    mime="application/pdf",
                )
        else:
            st.warning("No eval_id available.")
else:
    # Show placeholder results
    st.subheader("Evaluation Results (Placeholder)")
    st.info("Run a full evaluation to see live results. Showing pre-loaded placeholder data.")

    st.markdown("#### ASR per Attack Category")
    _render_asr_chart(PLACEHOLDER_ASR_BY_CATEGORY)

    st.markdown("#### System Comparison Summary")
    _render_summary_table(PLACEHOLDER_SUMMARY)
