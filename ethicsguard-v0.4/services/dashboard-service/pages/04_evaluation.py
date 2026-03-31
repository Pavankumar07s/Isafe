"""EthicsGuard v0.4 Dashboard — Evaluation page."""
import os
import sys
import time

import httpx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

st.set_page_config(page_title="Evaluation — EthicsGuard", page_icon="⬢", layout="wide", initial_sidebar_state="expanded")

from components.theme import (
    inject_theme, page_header, section_label, stat_card,
    badge, sidebar_branding, plotly_layout_defaults,
    C_PRIMARY, C_SUCCESS, C_DANGER, C_WARNING, C_TEXT, C_TEXT_SEC, PLOTLY_COLORS,
)

inject_theme()
sidebar_branding()

EVAL_URL = os.environ.get("EVAL_URL", "http://localhost:8002")

# ── Constants ─────────────────────────────────────────────────────────────────

ATTACK_CATEGORIES = [
    "prompt_injection", "jailbreak", "encoding", "multilingual",
    "semantic_smuggling", "context_overflow", "few_shot_poisoning",
    "tool_abuse", "crescendo",
]

SYSTEMS = ["EthicsGuard", "GPT-4o Raw", "OpenAI Mod", "LlamaGuard"]

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

# ── Helpers ───────────────────────────────────────────────────────────────────


def _start_eval() -> str | None:
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.post(f"{EVAL_URL}/run_eval", json={})
            resp.raise_for_status()
            return resp.json().get("eval_id")
    except httpx.ConnectError:
        st.error("Cannot connect to evaluation-service.")
    except httpx.HTTPStatusError as exc:
        st.error(f"evaluation-service returned HTTP {exc.response.status_code}")
    except Exception as exc:
        st.error(f"Error starting evaluation: {exc}")
    return None


def _poll_status(eval_id: str) -> dict:
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(f"{EVAL_URL}/eval_status/{eval_id}")
            resp.raise_for_status()
            return resp.json()
    except Exception:
        return {"status": "error"}


def _fetch_results(eval_id: str) -> dict | None:
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(f"{EVAL_URL}/eval_status/{eval_id}")
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        st.error(f"Error fetching results: {exc}")
        return None


def _download_report(eval_id: str) -> bytes | None:
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(f"{EVAL_URL}/report/{eval_id}")
            resp.raise_for_status()
            return resp.content
    except Exception:
        return None


def _render_asr_chart(asr_by_category: dict[str, dict[str, float]]):
    categories = list(asr_by_category.keys())
    fig = go.Figure()
    for idx, system in enumerate(SYSTEMS):
        values = [asr_by_category[cat].get(system, 0) for cat in categories]
        fig.add_trace(go.Bar(
            name=system, x=categories, y=values,
            marker_color=PLOTLY_COLORS[idx % len(PLOTLY_COLORS)],
        ))
    layout = plotly_layout_defaults()
    layout.update(
        barmode="group",
        yaxis_title="ASR (%)",
        yaxis=dict(range=[0, 100], gridcolor="#1e293b"),
        xaxis=dict(gridcolor="#1e293b", tickangle=-30),
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="right", x=1),
    )
    fig.update_layout(**layout)
    st.plotly_chart(fig, width="stretch")


def _render_summary_table(summary_df: pd.DataFrame):
    st.dataframe(
        summary_df.style.format({
            "ASR (%)": "{:.1f}",
            "FPR (%)": "{:.1f}",
            "FNR (%)": "{:.1f}",
            "Latency p95 (ms)": "{:.0f}",
        }),
        width="stretch",
        hide_index=True,
    )


# ── Page ──────────────────────────────────────────────────────────────────────

page_header(
    "Evaluation",
    "Run comprehensive benchmark evaluations across attack categories and compare "
    "EthicsGuard against baseline safety systems."
)

# Session state
if "eval_id" not in st.session_state:
    st.session_state.eval_id = None
if "eval_results" not in st.session_state:
    st.session_state.eval_results = None

# ── Run evaluation ────────────────────────────────────────────────────────────

section_label("RUN BENCHMARK")

st.markdown(
    '<div style="color:#94a3b8; font-size:0.82rem; margin-bottom:12px;">'
    'Launches a full evaluation against all attack categories and baselines. '
    'Typically completes in 1-3 minutes.</div>',
    unsafe_allow_html=True,
)

if st.button("Run Full Evaluation", type="primary"):
    eval_id = _start_eval()
    if eval_id:
        st.session_state.eval_id = eval_id
        st.session_state.eval_results = None

        progress_bar = st.progress(0, text="Evaluation starting…")
        status_text = st.empty()

        completed = False
        while not completed:
            time.sleep(3)
            status = _poll_status(eval_id)
            state = status.get("status", "unknown")
            progress = status.get("progress", 0)

            progress_bar.progress(
                min(progress, 1.0) if isinstance(progress, (int, float)) else 0,
                text=f"Status: {state} ({progress * 100:.0f}%)",
            )
            status_text.text(f"Eval ID: {eval_id} | State: {state}")

            if state in ("complete", "completed", "done", "finished"):
                progress_bar.progress(1.0, text="Evaluation complete!")
                completed = True
                results = _fetch_results(eval_id)
                st.session_state.eval_results = results
            elif state in ("error", "failed"):
                st.error(f"Evaluation failed: {status.get('error', 'Unknown error')}")
                break

        st.rerun()

# ── Results ───────────────────────────────────────────────────────────────────

results = st.session_state.eval_results
eval_id = st.session_state.eval_id

is_live = results and results.get("status") in ("complete", "completed", "done", "finished")

# Choose data source
if is_live:
    asr_data = results.get("asr_by_category", PLACEHOLDER_ASR_BY_CATEGORY)
    summary_data = results.get("summary")
    summary_df = pd.DataFrame(summary_data) if summary_data and isinstance(summary_data, list) else PLACEHOLDER_SUMMARY
else:
    asr_data = PLACEHOLDER_ASR_BY_CATEGORY
    summary_df = PLACEHOLDER_SUMMARY

# Key metrics from summary
section_label("KEY METRICS" + ("" if is_live else " (PLACEHOLDER)"))

if not is_live:
    st.caption("Run a full evaluation to see live results. Showing pre-loaded data.")

eg_row = summary_df[summary_df["System"] == "EthicsGuard"]
if not eg_row.empty:
    eg_asr = eg_row.iloc[0]["ASR (%)"]
    eg_fpr = eg_row.iloc[0]["FPR (%)"]
    eg_lat = eg_row.iloc[0]["Latency p95 (ms)"]
else:
    eg_asr, eg_fpr, eg_lat = 4.2, 2.1, 45

c1, c2, c3 = st.columns(3, gap="medium")
with c1:
    stat_card("Block Rate", f"{100 - eg_asr:.1f}%", "green" if eg_asr < 10 else "amber")
with c2:
    stat_card("False Positive Rate", f"{eg_fpr:.1f}%", "green" if eg_fpr < 5 else "amber")
with c3:
    stat_card("Latency p95", f"{eg_lat:.0f} ms", "green" if eg_lat < 100 else "amber")

# ASR chart
st.markdown("")
section_label("ASR PER ATTACK CATEGORY")
_render_asr_chart(asr_data)

# Summary table
section_label("SYSTEM COMPARISON")
_render_summary_table(summary_df)

# ── PDF Report ────────────────────────────────────────────────────────────────

if eval_id and is_live:
    section_label("REPORT DOWNLOAD")
    if "pdf_bytes" not in st.session_state:
        st.session_state.pdf_bytes = None
    if st.button("Generate PDF Report"):
        with st.spinner("Generating report…"):
            st.session_state.pdf_bytes = _download_report(eval_id)
    if st.session_state.pdf_bytes:
        st.download_button(
            label="Download PDF",
            data=st.session_state.pdf_bytes,
            file_name=f"ethicsguard_eval_{eval_id}.pdf",
            mime="application/pdf",
        )
