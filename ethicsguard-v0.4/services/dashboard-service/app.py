"""
EthicsGuard v0.4 Dashboard — Streamlit entrypoint
──────────────────────────────────────────────────
Premium AI Safety Dashboard.  Dark-themed, glassmorphism cards,
teal accents, professional typography via Inter.
"""
import os
import sys

# Ensure the components package is importable
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import streamlit as st

st.set_page_config(
    page_title="EthicsGuard v0.4 — AI Safety Dashboard",
    page_icon="⬢",
    layout="wide",
    initial_sidebar_state="expanded",
)

from components.theme import (
    inject_theme, page_header, section_label, badge,
    live_dot, sidebar_branding,
    C_PRIMARY, C_SUCCESS, C_WARNING, C_DANGER, C_TEXT_SEC, C_CARD, C_BORDER,
)

inject_theme()
sidebar_branding()

# ── Hero / landing ────────────────────────────────────────────────────────────

st.markdown(
    '<div class="eg-animate" style="text-align:center; padding:3.2rem 1rem 1.8rem;">'
    # Logo mark — shield + pulse line via inline SVG
    '<div style="margin-bottom:18px;">'
    '<svg width="54" height="54" viewBox="0 0 54 54" fill="none" xmlns="http://www.w3.org/2000/svg">'
    '<path d="M27 4L6 14v14c0 13.2 9 25.4 21 28 12-2.6 21-14.8 21-28V14L27 4Z" '
    'fill="#14b8a618" stroke="#14b8a6" stroke-width="2" stroke-linejoin="round"/>'
    '<path d="M16 28h5l3-8 4 16 3-8h5" stroke="#14b8a6" stroke-width="2.2" '
    'stroke-linecap="round" stroke-linejoin="round"/>'
    '</svg>'
    '</div>'
    '<h1 style="font-size:2.4rem !important; font-weight:800; letter-spacing:-0.03em; '
    'color:#f1f5f9; margin:0 0 6px;">EthicsGuard <span style="color:#14b8a6;">v0.4</span></h1>'
    '<p style="color:#64748b; font-size:0.95rem; margin:0 0 24px; font-weight:400;">'
    'AI Safety Middleware — Real-time guardrails for trustworthy AI'
    '</p>'
    '</div>',
    unsafe_allow_html=True,
)

# ── Quick-glance capability cards ─────────────────────────────────────────────

st.markdown('<div class="eg-section-title" style="text-align:center;">DASHBOARD MODULES</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns(3, gap="medium")

# Inline SVG icons for module cards (teal accent #14b8a6)
_SVG_SCORECARD = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#14b8a6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="12" width="4" height="9" rx="1"/><rect x="10" y="7" width="4" height="14" rx="1"/><rect x="17" y="2" width="4" height="19" rx="1"/></svg>'
_SVG_REDTEAM = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/></svg>'
_SVG_AUDIT = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#14b8a6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1"/><line x1="8" y1="10" x2="16" y2="10"/><line x1="8" y1="14" x2="16" y2="14"/><line x1="8" y1="18" x2="12" y2="18"/></svg>'
_SVG_EVAL = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#14b8a6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>'
_SVG_COMPLIANCE = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#14b8a6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>'

_modules = [
    (_SVG_SCORECARD, "Scorecard", "Real-time safety, toxicity, bias & hallucination scores with trend analysis.", "01_scorecard"),
    (_SVG_REDTEAM, "Red Team", "Generate adversarial attacks across 11 categories and benchmark defenses.", "02_redteam"),
    (_SVG_AUDIT, "Audit Log", "GDPR-compliant searchable audit trail with OWASP tag filtering.", "03_audit_log"),
    (_SVG_EVAL, "Evaluation", "Run comprehensive benchmarks comparing EthicsGuard against baselines.", "04_evaluation"),
    (_SVG_COMPLIANCE, "Compliance", "EU AI Act classification, OWASP LLM+ASI coverage matrix, PII stats.", "05_compliance"),
]

# Row 1 — 3 cards
for col, (icon, title, desc, _page) in zip([c1, c2, c3], _modules[:3]):
    with col:
        st.markdown(
            f'<div class="eg-card eg-animate" style="min-height:170px;">'
            f'<div style="margin-bottom:10px;">{icon}</div>'
            f'<div style="font-size:1.05rem; font-weight:600; color:#f1f5f9; margin-bottom:6px;">{title}</div>'
            f'<div style="font-size:0.82rem; color:#94a3b8; line-height:1.55;">{desc}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

# Row 2 — 2 cards, centred
c4, c5 = st.columns(2, gap="medium")
for col, (icon, title, desc, _page) in zip([c4, c5], _modules[3:]):
    with col:
        st.markdown(
            f'<div class="eg-card eg-animate" style="min-height:170px;">'
            f'<div style="margin-bottom:10px;">{icon}</div>'
            f'<div style="font-size:1.05rem; font-weight:600; color:#f1f5f9; margin-bottom:6px;">{title}</div>'
            f'<div style="font-size:0.82rem; color:#94a3b8; line-height:1.55;">{desc}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

# ── Architecture strip ───────────────────────────────────────────────────────

st.markdown("")
section_label("TECHNOLOGY STACK")

t1, t2, t3, t4, t5 = st.columns(5, gap="small")
_tech = [
    ("NeMo Guardrails", "Colang 1.0"),
    ("LangGraph", "8-node pipeline"),
    ("OWASP Mapped", "LLM01-10 + ASI01-10"),
    ("11 Attack Types", "Red team engine"),
    ("4 Compliance Modes", "STANDARD · GDPR · CCPA · HIPAA"),
]
for col, (heading, subtitle) in zip([t1, t2, t3, t4, t5], _tech):
    with col:
        st.markdown(
            f'<div class="eg-card" style="text-align:center; padding:14px 8px;">'
            f'<div style="font-size:0.82rem; font-weight:600; color:#e2e8f0;">{heading}</div>'
            f'<div style="font-size:0.68rem; color:#64748b; margin-top:4px;">{subtitle}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

# ── Footer ────────────────────────────────────────────────────────────────────

st.markdown(
    '<div style="text-align:center; padding:2.5rem 0 1rem; color:#334155; font-size:0.7rem; letter-spacing:0.05em;">'
    'EthicsGuard v0.4 · iSAFE Hackathon 2026 · Built with care in Pune, India'
    '</div>',
    unsafe_allow_html=True,
)
