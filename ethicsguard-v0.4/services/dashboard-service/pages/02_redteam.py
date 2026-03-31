"""EthicsGuard v0.4 Dashboard — Red Team page."""
import os
import sys
import httpx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

st.set_page_config(page_title="Red Team — EthicsGuard", page_icon="⬢", layout="wide", initial_sidebar_state="expanded")

from components.theme import (
    inject_theme, page_header, section_label, stat_card,
    badge, status_badge, sidebar_branding, plotly_layout_defaults,
    C_PRIMARY, C_SUCCESS, C_DANGER, C_WARNING, C_TEXT, C_TEXT_SEC, PLOTLY_COLORS,
)

inject_theme()
sidebar_branding()

REDTEAM_URL = os.environ.get("REDTEAM_URL", "http://localhost:8001")

# ── Helpers ───────────────────────────────────────────────────────────────────

DEFAULT_ATTACK_TYPES = [
    "prompt_injection", "jailbreak", "pii_extraction", "deepfake_instruction",
    "agentic_multiturn", "mcp_supply_chain", "cot_exploitation",
    "multimodal_inject", "embedding_inversion", "memory_poisoning", "goal_hijacking",
]
TARGETS = ["ethicsguard", "gpt4o_raw", "openai_mod", "llamaguard"]

TARGET_LABELS = {
    "ethicsguard": "EthicsGuard",
    "gpt4o_raw": "GPT-4o Raw",
    "openai_mod": "OpenAI Mod",
    "llamaguard": "LlamaGuard",
}


def _fetch_attack_catalog() -> list[str]:
    try:
        with httpx.Client(timeout=5) as client:
            resp = client.get(f"{REDTEAM_URL}/attack_catalog")
            resp.raise_for_status()
            data = resp.json()
            attacks_list = data.get("attacks", [])
            if isinstance(attacks_list, list) and all(isinstance(a, dict) for a in attacks_list):
                return [a.get("name", "") for a in attacks_list]
            elif isinstance(attacks_list, list) and all(isinstance(a, str) for a in attacks_list):
                return attacks_list
            return DEFAULT_ATTACK_TYPES
    except Exception:
        return DEFAULT_ATTACK_TYPES


def _generate_attack(attack_type: str, batch_size: int) -> list[dict]:
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{REDTEAM_URL}/generate_attack",
                json={"type": attack_type, "n": batch_size},
            )
            resp.raise_for_status()
            return resp.json().get("attacks", [])
    except httpx.ConnectError:
        st.error("Cannot connect to redteam-service. Is it running?")
        return []
    except httpx.HTTPStatusError as exc:
        st.error(f"redteam-service returned HTTP {exc.response.status_code}")
        return []
    except Exception as exc:
        st.error(f"Error generating attacks: {exc}")
        return []


def _run_batch(prompts: list, target: str) -> list[dict]:
    try:
        attack_list = prompts if all(isinstance(p, str) for p in prompts) else [p.get('prompt', str(p)) for p in prompts]
        with httpx.Client(timeout=60) as client:
            resp = client.post(
                f"{REDTEAM_URL}/run_batch",
                json={"attacks": attack_list, "target": target},
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            for r in results:
                raw = r.get("raw") or {}
                if "owasp_tags" not in r and "owasp_tags" in raw:
                    r["owasp_tags"] = raw["owasp_tags"]
            return results
    except httpx.ConnectError:
        st.error("Cannot connect to redteam-service. Is it running?")
        return []
    except httpx.HTTPStatusError as exc:
        st.error(f"redteam-service returned HTTP {exc.response.status_code}")
        return []
    except Exception as exc:
        st.error(f"Error running batch: {exc}")
        return []


def _compare_all_baselines(prompts: list) -> dict[str, list[dict]]:
    all_results: dict[str, list[dict]] = {}
    for target in TARGETS:
        results = _run_batch(prompts, target)
        all_results[target] = results
    return all_results


# ── Page ──────────────────────────────────────────────────────────────────────

page_header(
    "Red Team",
    "Generate adversarial attacks and test them against safety systems. "
    "Compare EthicsGuard against baseline models."
)

# ── Controls ──────────────────────────────────────────────────────────────────

section_label("ATTACK CONFIGURATION")

col_a, col_b = st.columns([3, 2], gap="large")
with col_a:
    attack_types = _fetch_attack_catalog()
    selected_attack = st.selectbox("Attack type", attack_types)
    batch_size = st.slider("Batch size", min_value=1, max_value=50, value=10)
with col_b:
    target = st.radio("Target system", TARGETS, format_func=lambda t: TARGET_LABELS.get(t, t), horizontal=False)

st.markdown("")
c1, c2, _ = st.columns([1, 1, 3])
generate_clicked = c1.button("Generate & Run", type="primary")
compare_clicked = c2.button("Compare Baselines")

# ── Session state ─────────────────────────────────────────────────────────────

if "redteam_results" not in st.session_state:
    st.session_state.redteam_results = []
if "redteam_prompts" not in st.session_state:
    st.session_state.redteam_prompts = []
if "redteam_comparison" not in st.session_state:
    st.session_state.redteam_comparison = {}

# ── Generate & Run ────────────────────────────────────────────────────────────

if generate_clicked:
    with st.spinner("Generating attack prompts..."):
        prompts = _generate_attack(selected_attack, batch_size)
        st.session_state.redteam_prompts = prompts
    if prompts:
        with st.spinner(f"Running batch against {TARGET_LABELS.get(target, target)}..."):
            results = _run_batch(prompts, target)
            st.session_state.redteam_results = results
            st.session_state.redteam_comparison = {}

if compare_clicked:
    if not st.session_state.redteam_prompts:
        st.warning("Generate attacks first, then compare baselines.")
    else:
        with st.spinner("Running against all baselines..."):
            comparison = _compare_all_baselines(st.session_state.redteam_prompts)
            st.session_state.redteam_comparison = comparison
            st.session_state.redteam_results = []

# ── Results table (single target) ────────────────────────────────────────────

if st.session_state.redteam_results:
    st.markdown("")
    section_label(f"RESULTS — {TARGET_LABELS.get(target, target).upper()}")

    total = len(st.session_state.redteam_results)
    blocked = sum(1 for r in st.session_state.redteam_results if r.get("blocked"))
    asr = ((total - blocked) / total * 100) if total else 0
    block_rate = 100 - asr

    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        stat_card("Block Rate", f"{block_rate:.1f}%", "green" if block_rate >= 80 else "amber" if block_rate >= 50 else "red")
    with c2:
        stat_card("ASR", f"{asr:.1f}%", "green" if asr <= 10 else "amber" if asr <= 30 else "red")
    with c3:
        stat_card("Prompts Tested", str(total), "blue")

    rows = []
    for r in st.session_state.redteam_results:
        prompt_text = r.get("prompt", "")
        is_blocked = r.get("blocked", False)
        owasp = r.get("owasp_tags", [])
        rows.append({
            "Prompt": prompt_text[:90] + ("…" if len(prompt_text) > 90 else ""),
            "Status": "BLOCKED" if is_blocked else "BYPASSED",
            "Latency (ms)": r.get("latency_ms", "—"),
            "OWASP": ", ".join(owasp) if isinstance(owasp, list) else str(owasp or "—"),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ── Comparison chart ─────────────────────────────────────────────────────────

if st.session_state.redteam_comparison:
    st.markdown("")
    section_label("BASELINE COMPARISON — ATTACK SUCCESS RATE")

    asr_data = {}
    for tgt, results in st.session_state.redteam_comparison.items():
        total = len(results)
        blocked = sum(1 for r in results if r.get("blocked"))
        asr_data[tgt] = ((total - blocked) / total * 100) if total else 0

    labels = [TARGET_LABELS.get(t, t) for t in asr_data]
    values = list(asr_data.values())

    bar_colors = []
    for v in values:
        if v <= 10:
            bar_colors.append(C_SUCCESS)
        elif v <= 40:
            bar_colors.append(C_WARNING)
        else:
            bar_colors.append(C_DANGER)

    fig = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=values,
                marker_color=bar_colors,
                text=[f"{v:.1f}%" for v in values],
                textposition="outside",
                textfont=dict(color=C_TEXT, size=13, family="Inter"),
            )
        ]
    )
    layout = plotly_layout_defaults()
    layout.update(
        yaxis_title="ASR (%)",
        yaxis=dict(range=[0, max(values + [10]) * 1.25], gridcolor="#1e293b"),
        xaxis=dict(gridcolor="#1e293b"),
        height=380,
    )
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)

    section_label("DETAIL PER TARGET")
    for tgt, results in st.session_state.redteam_comparison.items():
        with st.expander(f"{TARGET_LABELS.get(tgt, tgt)}  —  {len([r for r in results if r.get('blocked')])} / {len(results)} blocked"):
            rows = []
            for r in results:
                prompt_text = r.get("prompt", "")
                is_blocked = r.get("blocked", False)
                owasp = r.get("owasp_tags", [])
                rows.append({
                    "Prompt": prompt_text[:90] + ("…" if len(prompt_text) > 90 else ""),
                    "Status": "BLOCKED" if is_blocked else "BYPASSED",
                    "Latency": r.get("latency_ms", "—"),
                    "OWASP": ", ".join(owasp) if isinstance(owasp, list) else str(owasp or "—"),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)