"""EthicsGuard v0.4 Dashboard — Red Team page."""
import httpx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Red Team — EthicsGuard", page_icon="🛡️", layout="wide")

REDTEAM_URL = "http://redteam-service:8001"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DEFAULT_ATTACK_TYPES = [
    "prompt_injection",
    "jailbreak_dan",
    "jailbreak_roleplay",
    "encoding_base64",
    "encoding_rot13",
    "multilingual",
    "semantic_smuggling",
    "context_overflow",
    "few_shot_poisoning",
    "tool_abuse",
    "crescendo",
]

TARGETS = ["ethicsguard", "gpt4o_raw", "openai_mod", "llamaguard"]


def _fetch_attack_catalog() -> list[str]:
    """Fetch available attack types from the red-team service."""
    try:
        with httpx.Client(timeout=5) as client:
            resp = client.get(f"{REDTEAM_URL}/attack_catalog")
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                return data
            return data.get("attack_types", DEFAULT_ATTACK_TYPES)
    except Exception:
        return DEFAULT_ATTACK_TYPES


def _generate_attack(attack_type: str, batch_size: int) -> list[dict]:
    """Call the red-team service to generate attack prompts."""
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{REDTEAM_URL}/generate_attack",
                json={"attack_type": attack_type, "count": batch_size},
            )
            resp.raise_for_status()
            return resp.json().get("prompts", [])
    except httpx.ConnectError:
        st.error("Cannot connect to redteam-service. Is it running?")
        return []
    except httpx.HTTPStatusError as exc:
        st.error(f"redteam-service returned HTTP {exc.response.status_code}")
        return []
    except Exception as exc:
        st.error(f"Error generating attacks: {exc}")
        return []


def _run_batch(prompts: list[dict], target: str) -> list[dict]:
    """Run a batch of attack prompts against a target."""
    try:
        with httpx.Client(timeout=60) as client:
            resp = client.post(
                f"{REDTEAM_URL}/run_batch",
                json={"prompts": prompts, "target": target},
            )
            resp.raise_for_status()
            return resp.json().get("results", [])
    except httpx.ConnectError:
        st.error("Cannot connect to redteam-service. Is it running?")
        return []
    except httpx.HTTPStatusError as exc:
        st.error(f"redteam-service returned HTTP {exc.response.status_code}")
        return []
    except Exception as exc:
        st.error(f"Error running batch: {exc}")
        return []


def _compare_all_baselines(prompts: list[dict]) -> dict[str, list[dict]]:
    """Run the same prompts against every target and return results keyed by target."""
    all_results: dict[str, list[dict]] = {}
    for target in TARGETS:
        results = _run_batch(prompts, target)
        all_results[target] = results
    return all_results


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

st.title("Red Team")
st.caption("Generate adversarial attacks and test them against safety systems.")

# --- Controls ---
attack_types = _fetch_attack_catalog()

col_a, col_b = st.columns(2)
with col_a:
    selected_attack = st.selectbox("Attack type", attack_types)
    batch_size = st.slider("Batch size", min_value=1, max_value=50, value=10)
with col_b:
    target = st.radio("Target system", TARGETS, horizontal=True)

st.divider()

col_gen, col_compare = st.columns(2)
generate_clicked = col_gen.button("Generate & Run", type="primary")
compare_clicked = col_compare.button("Compare all baselines")

# --- Session state ---
if "redteam_results" not in st.session_state:
    st.session_state.redteam_results = []
if "redteam_prompts" not in st.session_state:
    st.session_state.redteam_prompts = []
if "redteam_comparison" not in st.session_state:
    st.session_state.redteam_comparison = {}

# --- Generate & Run ---
if generate_clicked:
    with st.spinner("Generating attack prompts..."):
        prompts = _generate_attack(selected_attack, batch_size)
        st.session_state.redteam_prompts = prompts

    if prompts:
        with st.spinner(f"Running batch against {target}..."):
            results = _run_batch(prompts, target)
            st.session_state.redteam_results = results
            st.session_state.redteam_comparison = {}

# --- Compare all baselines ---
if compare_clicked:
    if not st.session_state.redteam_prompts:
        st.warning("Generate attacks first, then compare baselines.")
    else:
        with st.spinner("Running against all baselines..."):
            comparison = _compare_all_baselines(st.session_state.redteam_prompts)
            st.session_state.redteam_comparison = comparison
            st.session_state.redteam_results = []

# --- Results table (single target) ---
if st.session_state.redteam_results:
    st.subheader(f"Results — {target}")
    rows = []
    for r in st.session_state.redteam_results:
        prompt_text = r.get("prompt", "")
        rows.append({
            "Prompt (first 80 chars)": prompt_text[:80] + ("..." if len(prompt_text) > 80 else ""),
            "Blocked?": "Yes" if r.get("blocked") else "No",
            "Latency (ms)": r.get("latency_ms", "—"),
            "OWASP Tags": ", ".join(r.get("owasp_tags", [])) if isinstance(r.get("owasp_tags"), list) else r.get("owasp_tags", "—"),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # ASR summary
    total = len(st.session_state.redteam_results)
    blocked = sum(1 for r in st.session_state.redteam_results if r.get("blocked"))
    asr = ((total - blocked) / total * 100) if total else 0
    st.metric("Attack Success Rate (ASR)", f"{asr:.1f}%")

# --- Comparison chart ---
if st.session_state.redteam_comparison:
    st.subheader("Baseline Comparison — ASR per Target")

    asr_data = {}
    for tgt, results in st.session_state.redteam_comparison.items():
        total = len(results)
        blocked = sum(1 for r in results if r.get("blocked"))
        asr_data[tgt] = ((total - blocked) / total * 100) if total else 0

    fig = go.Figure(
        data=[
            go.Bar(
                x=list(asr_data.keys()),
                y=list(asr_data.values()),
                marker_color=["#3b82f6", "#f59e0b", "#ef4444", "#22c55e"],
                text=[f"{v:.1f}%" for v in asr_data.values()],
                textposition="outside",
            )
        ]
    )
    fig.update_layout(
        yaxis_title="ASR (%)",
        yaxis=dict(range=[0, 105]),
        height=400,
        margin=dict(t=20, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Detail tables per target
    for tgt, results in st.session_state.redteam_comparison.items():
        with st.expander(f"Details — {tgt}"):
            rows = []
            for r in results:
                prompt_text = r.get("prompt", "")
                rows.append({
                    "Prompt (first 80 chars)": prompt_text[:80] + ("..." if len(prompt_text) > 80 else ""),
                    "Blocked?": "Yes" if r.get("blocked") else "No",
                    "Latency (ms)": r.get("latency_ms", "—"),
                    "OWASP Tags": ", ".join(r.get("owasp_tags", [])) if isinstance(r.get("owasp_tags"), list) else r.get("owasp_tags", "—"),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
