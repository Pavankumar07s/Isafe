"""EthicsGuard v0.4 Dashboard — Compliance page."""
import os

import httpx
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Compliance — EthicsGuard", page_icon="🛡️", layout="wide")

GUARDRAIL_URL = "http://guardrail-service:8000"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMPLIANCE_MODE = os.environ.get("COMPLIANCE_MODE", "STANDARD")

MODE_COLORS = {
    "STANDARD": "#3b82f6",
    "STRICT": "#f59e0b",
    "EU_AI_ACT": "#22c55e",
    "HIPAA": "#8b5cf6",
}

DATA_RETENTION_POLICIES = {
    "STANDARD": "Audit logs retained for 90 days. Prompt hashes only — no raw text stored.",
    "STRICT": "Audit logs retained for 180 days. Full audit trail with prompt hashes. Enhanced logging enabled.",
    "EU_AI_ACT": "Audit logs retained for 5 years per EU AI Act Article 12. Full traceability chain maintained. No PII in logs — prompt_hash only.",
    "HIPAA": "Audit logs retained for 6 years. PHI/PII redacted at ingest. Encryption at rest (AES-256).",
}

# OWASP LLM Top 10 + OWASP Agentic Security Initiative (ASI) Top 10 coverage
OWASP_COVERAGE = {
    "LLM01": {"name": "Prompt Injection", "covered": True},
    "LLM02": {"name": "Insecure Output Handling", "covered": True},
    "LLM03": {"name": "Training Data Poisoning", "covered": False},
    "LLM04": {"name": "Model Denial of Service", "covered": True},
    "LLM05": {"name": "Supply Chain Vulnerabilities", "covered": False},
    "LLM06": {"name": "Sensitive Information Disclosure", "covered": True},
    "LLM07": {"name": "Insecure Plugin Design", "covered": True},
    "LLM08": {"name": "Excessive Agency", "covered": True},
    "LLM09": {"name": "Overreliance", "covered": True},
    "LLM10": {"name": "Model Theft", "covered": False},
    "ASI01": {"name": "Excessive Agency (Agentic)", "covered": True},
    "ASI02": {"name": "Unintended Autonomous Actions", "covered": True},
    "ASI03": {"name": "Uncontrolled Resource Consumption", "covered": True},
    "ASI04": {"name": "Inadequate Sandboxing", "covered": False},
    "ASI05": {"name": "Insecure Tool Integration", "covered": True},
    "ASI06": {"name": "Unsafe Code Generation", "covered": True},
    "ASI07": {"name": "Prompt Injection via Tools", "covered": True},
    "ASI08": {"name": "Multi-Agent Trust Exploitation", "covered": True},
    "ASI09": {"name": "Insufficient Logging & Monitoring", "covered": True},
    "ASI10": {"name": "Misaligned Goal Specification", "covered": True},
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fetch_pii_stats() -> dict:
    """Fetch PII detection statistics from the guardrail service."""
    try:
        with httpx.Client(timeout=5) as client:
            resp = client.get(f"{GUARDRAIL_URL}/pii_stats")
            resp.raise_for_status()
            return resp.json()
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

st.title("Compliance")
st.caption("Regulatory compliance status, coverage mapping, and data governance.")

# --- Compliance mode badge ---
badge_color = MODE_COLORS.get(COMPLIANCE_MODE, "#6b7280")
st.markdown(
    f"""
    <div style="
        display:inline-block;
        background:{badge_color}22;
        border:2px solid {badge_color};
        border-radius:12px;
        padding:16px 36px;
        margin-bottom:16px;
    ">
        <span style="font-size:0.9rem;color:#888;">Active Compliance Mode</span><br>
        <span style="font-size:2.2rem;font-weight:700;color:{badge_color};">{COMPLIANCE_MODE}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# --- EU AI Act classification ---
st.subheader("EU AI Act Classification")
st.info(
    "**High-Risk AI System (Article 6, Annex III)**\n\n"
    "EthicsGuard operates as a safety layer for AI systems that may fall under "
    "high-risk categories defined in the EU AI Act. As such, it implements:\n"
    "- Risk management system (Article 9)\n"
    "- Data governance (Article 10)\n"
    "- Technical documentation (Article 11)\n"
    "- Record-keeping / audit logging (Article 12)\n"
    "- Transparency & human oversight (Articles 13-14)\n"
    "- Accuracy, robustness & cybersecurity (Article 15)"
)

st.divider()

# --- OWASP coverage table ---
st.subheader("OWASP Coverage Matrix")

coverage_rows = []
for tag, info in OWASP_COVERAGE.items():
    coverage_rows.append({
        "ID": tag,
        "Vulnerability": info["name"],
        "Covered": "\u2713" if info["covered"] else "\u2717",
        "Status": "Protected" if info["covered"] else "Not Covered",
    })

coverage_df = pd.DataFrame(coverage_rows)

# Color the coverage column
def _highlight_coverage(row):
    if row["Covered"] == "\u2713":
        return [""] * len(row)
    return ["color: #ef4444"] * len(row)

styled_df = coverage_df.style.apply(_highlight_coverage, axis=1)
st.dataframe(styled_df, use_container_width=True, hide_index=True, height=600)

covered_count = sum(1 for v in OWASP_COVERAGE.values() if v["covered"])
total_count = len(OWASP_COVERAGE)
st.metric("Coverage", f"{covered_count}/{total_count} ({covered_count / total_count * 100:.0f}%)")

st.divider()

# --- Data retention policy ---
st.subheader("Data Retention Policy")

retention_text = DATA_RETENTION_POLICIES.get(COMPLIANCE_MODE, DATA_RETENTION_POLICIES["STANDARD"])
st.markdown(f"> {retention_text}")

st.divider()

# --- PII detection stats ---
st.subheader("PII Detection Statistics")

pii_stats = _fetch_pii_stats()
if pii_stats:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Scanned", pii_stats.get("total_scanned", 0))
    col2.metric("PII Detected", pii_stats.get("pii_detected", 0))
    col3.metric("PII Redacted", pii_stats.get("pii_redacted", 0))
    col4.metric("Detection Rate", f"{pii_stats.get('detection_rate', 0):.1f}%")
else:
    st.info("PII statistics unavailable — showing placeholder values.")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Scanned", "12,847")
    col2.metric("PII Detected", "342")
    col3.metric("PII Redacted", "342")
    col4.metric("Detection Rate", "2.7%")

st.divider()

# --- Documentation link ---
st.subheader("Documentation")
st.markdown(
    "For full regulatory documentation, see "
    "[`EU_AI_ACT.md`](../EU_AI_ACT.md) in the project repository."
)
st.markdown(
    "For OWASP LLM Top 10 details, visit "
    "[owasp.org/www-project-top-10-for-large-language-model-applications]"
    "(https://owasp.org/www-project-top-10-for-large-language-model-applications/)"
)
