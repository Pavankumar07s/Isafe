"""EthicsGuard v0.4 Dashboard — Compliance page."""
import os
import sys

import httpx
import pandas as pd
import streamlit as st

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

st.set_page_config(page_title="Compliance — EthicsGuard", page_icon="⬢", layout="wide", initial_sidebar_state="expanded")

from components.theme import (
    inject_theme, page_header, section_label, stat_card,
    badge, sidebar_branding, card_open, card_close,
    C_PRIMARY, C_SUCCESS, C_DANGER, C_WARNING, C_TEXT, C_TEXT_SEC,
)

inject_theme()
sidebar_branding()

GUARDRAIL_URL = os.environ.get("GUARDRAIL_URL", "http://localhost:8000")

# ── Constants ─────────────────────────────────────────────────────────────────

COMPLIANCE_MODE = os.environ.get("COMPLIANCE_MODE", "STANDARD")

# SVG icons for compliance modes
_SVG_STD = '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/></svg>'
_SVG_EU = '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10A15.3 15.3 0 0 1 12 2z"/></svg>'
_SVG_US = '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>'
_SVG_HIPAA = '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>'

MODE_META = {
    "STANDARD":  {"color": "#3b82f6", "icon": _SVG_STD,   "label": "Standard"},
    "GDPR_EU":   {"color": "#22c55e", "icon": _SVG_EU,    "label": "GDPR (EU)"},
    "CCPA_CA":   {"color": "#f59e0b", "icon": _SVG_US,    "label": "CCPA (CA)"},
    "HIPAA_US":  {"color": "#8b5cf6", "icon": _SVG_HIPAA, "label": "HIPAA (US)"},
}

DATA_RETENTION_POLICIES = {
    "STANDARD": "Audit logs retained for 365 days. Prompt hashes only — no raw text stored.",
    "GDPR_EU":  "Audit logs retained for 30 days per GDPR minimization. Full traceability chain maintained. No PII in logs. PII redacted before LLM processing.",
    "CCPA_CA":  "Audit logs retained for 90 days. Right-to-deletion support enabled. Opt-out of data sale flag propagated.",
    "HIPAA_US": "Audit logs retained for 90 days. PHI/PII redacted at ingest. Encryption at rest (Fernet/AES-256). No PHI in LLM context without de-identification.",
}

OWASP_COVERAGE = {
    "LLM01": {"name": "Prompt Injection",                "covered": True},
    "LLM02": {"name": "Sensitive Information Disclosure", "covered": True},
    "LLM03": {"name": "Supply Chain Risks",              "covered": True},
    "LLM04": {"name": "Data and Model Poisoning",        "covered": True},
    "LLM05": {"name": "Improper Output Handling",        "covered": True},
    "LLM06": {"name": "Excessive Agency",                "covered": True},
    "LLM07": {"name": "System Prompt Leakage",           "covered": True},
    "LLM08": {"name": "Vector and Embedding Weaknesses", "covered": True},
    "LLM09": {"name": "Misinformation",                  "covered": True},
    "LLM10": {"name": "Unbounded Consumption",           "covered": False},
    "ASI01": {"name": "Memory Poisoning",                "covered": True},
    "ASI02": {"name": "Tool / Plugin Abuse",             "covered": True},
    "ASI03": {"name": "Cascading Hallucinations",        "covered": True},
    "ASI04": {"name": "Goal Hijacking",                  "covered": True},
    "ASI05": {"name": "Scope Creep",                     "covered": True},
    "ASI06": {"name": "Identity Spoofing",               "covered": True},
    "ASI07": {"name": "Excessive Persistence",           "covered": False},
    "ASI08": {"name": "Insecure MCP Tool Execution",     "covered": True},
    "ASI09": {"name": "Audit Trail Evasion",             "covered": True},
    "ASI10": {"name": "Over-Permissioned Execution",     "covered": True},
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _fetch_pii_stats() -> dict:
    try:
        with httpx.Client(timeout=5) as client:
            resp = client.get(f"{GUARDRAIL_URL}/pii_stats")
            resp.raise_for_status()
            return resp.json()
    except Exception:
        return {}


# ── Page ──────────────────────────────────────────────────────────────────────

page_header(
    "Compliance",
    "Regulatory compliance status, OWASP coverage mapping, and data governance."
)

# ── Compliance mode hero ─────────────────────────────────────────────────────

meta = MODE_META.get(COMPLIANCE_MODE, MODE_META["STANDARD"])
m_color = meta["color"]

st.markdown(
    f'<div class="eg-card eg-card-accent eg-animate" '
    f'style="text-align:center; padding:28px 20px 24px; margin-bottom:6px;">'
    f'<div style="font-size:0.72rem; font-weight:600; text-transform:uppercase; '
    f'letter-spacing:0.08em; color:#64748b; margin-bottom:6px;">'
    f'Active Compliance Mode</div>'
    f'<div style="font-size:2.6rem; font-weight:800; letter-spacing:-0.02em; '
    f'color:{m_color};">{meta["icon"]}  {COMPLIANCE_MODE}</div>'
    f'<div style="font-size:0.78rem; color:#64748b; margin-top:4px;">'
    f'{DATA_RETENTION_POLICIES.get(COMPLIANCE_MODE, "")}</div>'
    f'</div>',
    unsafe_allow_html=True,
)

# ── EU AI Act ─────────────────────────────────────────────────────────────────

section_label("EU AI ACT CLASSIFICATION")

eu_articles = [
    ("Article 9",  "Risk management system"),
    ("Article 10", "Data governance"),
    ("Article 11", "Technical documentation"),
    ("Article 12", "Record-keeping / audit logging"),
    ("Articles 13-14", "Transparency & human oversight"),
    ("Article 15", "Accuracy, robustness & cybersecurity"),
]

st.markdown(
    '<div class="eg-card eg-animate">'
    '<div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">'
    + badge("High-Risk AI System", "amber")
    + '<span style="color:#94a3b8; font-size:0.82rem;">Article 6, Annex III</span>'
    '</div>'
    '<div style="color:#94a3b8; font-size:0.84rem; line-height:1.7;">'
    'EthicsGuard operates as a safety layer for AI systems under high-risk '
    'categories defined in the EU AI Act. Implemented requirements:</div>'
    '<div style="margin-top:10px; display:grid; grid-template-columns:repeat(auto-fill,minmax(250px,1fr)); gap:8px;">',
    unsafe_allow_html=True,
)
for article, desc in eu_articles:
    st.markdown(
        f'<div style="display:flex; align-items:center; gap:8px; '
        f'padding:6px 12px; border-radius:6px; background:#0f172a;">'
        f'<span style="color:#14b8a6; font-weight:600; font-size:0.8rem; white-space:nowrap;">{article}</span>'
        f'<span style="color:#94a3b8; font-size:0.8rem;">{desc}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
st.markdown('</div></div>', unsafe_allow_html=True)

# ── OWASP coverage ───────────────────────────────────────────────────────────

section_label("OWASP COVERAGE MATRIX")

covered_count = sum(1 for v in OWASP_COVERAGE.values() if v["covered"])
total_count = len(OWASP_COVERAGE)
pct = covered_count / total_count * 100

c1, c2, c3 = st.columns(3, gap="medium")
with c1:
    stat_card("Covered", f"{covered_count}/{total_count}", "green")
with c2:
    stat_card("Coverage", f"{pct:.0f}%", "green" if pct >= 80 else "amber")
with c3:
    stat_card("Gaps", str(total_count - covered_count), "red" if total_count - covered_count > 3 else "amber")

# Build coverage HTML grid
rows_html = ""
for tag, info in OWASP_COVERAGE.items():
    is_covered = info["covered"]
    dot_color = C_SUCCESS if is_covered else C_DANGER
    label = "Protected" if is_covered else "Gap"
    bg = "#12261e" if is_covered else "#261216"
    rows_html += (
        f'<div style="display:flex; align-items:center; justify-content:space-between; '
        f'padding:8px 14px; border-radius:6px; background:{bg}; margin-bottom:4px;">'
        f'<div style="display:flex; align-items:center; gap:10px;">'
        f'<span style="color:{dot_color}; font-weight:700; font-size:0.8rem; '
        f'min-width:48px;">{tag}</span>'
        f'<span style="color:#cbd5e1; font-size:0.82rem;">{info["name"]}</span>'
        f'</div>'
        f'<span style="font-size:0.72rem; font-weight:600; color:{dot_color};">{label}</span>'
        f'</div>'
    )

st.markdown(
    f'<div class="eg-card eg-animate" style="padding:14px 16px;">{rows_html}</div>',
    unsafe_allow_html=True,
)

# ── PII stats ─────────────────────────────────────────────────────────────────

section_label("PII DETECTION STATISTICS")

pii_stats = _fetch_pii_stats()
if pii_stats:
    ts = pii_stats.get("total_scanned", 0)
    pd_ = pii_stats.get("pii_detected", 0)
    pr = pii_stats.get("pii_redacted", 0)
    dr = pii_stats.get("detection_rate", 0)
else:
    ts, pd_, pr, dr = 12847, 342, 342, 2.7

c1, c2, c3, c4 = st.columns(4, gap="medium")
with c1:
    stat_card("Scanned", f"{ts:,}", "blue")
with c2:
    stat_card("Detected", str(pd_), "amber")
with c3:
    stat_card("Redacted", str(pr), "green")
with c4:
    stat_card("Detection Rate", f"{dr:.1f}%", "green" if dr < 5 else "amber")

if not pii_stats:
    st.caption("PII statistics unavailable — showing placeholder values.")

# ── Documentation ─────────────────────────────────────────────────────────────

section_label("DOCUMENTATION")

st.markdown(
    '<div class="eg-card eg-animate" style="padding:16px 20px;">'
    '<div style="display:flex; gap:20px; flex-wrap:wrap;">'
    '<a href="https://owasp.org/www-project-top-10-for-large-language-model-applications/" '
    'target="_blank" style="color:#14b8a6; text-decoration:none; font-size:0.85rem; '
    'font-weight:500;">OWASP LLM Top 10 ↗</a>'
    '<span style="color:#334155;">|</span>'
    '<span style="color:#94a3b8; font-size:0.85rem;">EU_AI_ACT.md — in project repository</span>'
    '<span style="color:#334155;">|</span>'
    '<span style="color:#94a3b8; font-size:0.85rem;">ETHICS.md — ethical framework</span>'
    '</div></div>',
    unsafe_allow_html=True,
)
