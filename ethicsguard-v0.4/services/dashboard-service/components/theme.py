"""
EthicsGuard v0.4 — Premium Design System
─────────────────────────────────────────
Shared CSS, components, and visual helpers used across all dashboard pages.

Design principles:
  • Dark theme with deep navy tones — professional, calm, trustworthy
  • Teal (#14b8a6) primary accent — signals safety and reliability
  • Generous whitespace and clear typography hierarchy
  • Glassmorphism cards with subtle depth — modern without being gimmicky
  • Intentional micro-animations — alive but never distracting
  • WCAG 2.2 AA contrast throughout

Color palette:
  Background:    #0b1120 (deep navy)      Surface:       #111827
  Card:          #1e293b (slate-800)       Card hover:    #243247
  Border:        #334155 (slate-700)       Border accent: #14b8a622
  Primary:       #14b8a6 (teal)           Primary hover: #0d9488
  Success:       #22c55e                   Warning:       #f59e0b
  Danger:        #ef4444                   Info:          #3b82f6
  Text primary:  #f1f5f9                   Text secondary:#94a3b8
  Muted:         #64748b
"""
import streamlit as st


# ── Palette constants (importable by pages that need them for Plotly) ─────────

C_BG = "#0b1120"
C_SURFACE = "#111827"
C_CARD = "#1e293b"
C_CARD_HOVER = "#243247"
C_BORDER = "#334155"
C_PRIMARY = "#14b8a6"
C_PRIMARY_DIM = "#14b8a622"
C_SUCCESS = "#22c55e"
C_WARNING = "#f59e0b"
C_DANGER = "#ef4444"
C_INFO = "#3b82f6"
C_TEXT = "#f1f5f9"
C_TEXT_SEC = "#94a3b8"
C_MUTED = "#64748b"

PLOTLY_COLORS = [C_PRIMARY, C_WARNING, C_DANGER, C_SUCCESS, C_INFO, "#a78bfa"]


def plotly_layout_defaults() -> dict:
    """Return a dict of Plotly layout overrides matching the dashboard theme."""
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", color=C_TEXT_SEC, size=12),
        xaxis=dict(gridcolor="#1e293b", zerolinecolor="#334155"),
        yaxis=dict(gridcolor="#1e293b", zerolinecolor="#334155"),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=C_TEXT_SEC, size=11),
        ),
        margin=dict(l=0, r=0, t=28, b=40),
        hoverlabel=dict(
            bgcolor=C_CARD,
            bordercolor=C_BORDER,
            font=dict(color=C_TEXT, family="Inter, system-ui, sans-serif"),
        ),
    )


# ── Master CSS ───────────────────────────────────────────────────────────────

_MASTER_CSS = """
<style>
/* ─── Typography ───────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="st-"] {
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* ─── Page background ──────────────────────────────────────────────── */
.stApp {
    background: linear-gradient(168deg, #0b1120 0%, #0f172a 40%, #111827 100%);
}
[data-testid="stAppViewContainer"] {
    background: transparent;
}

/* ─── Sidebar (locked open) ────────────────────────────────────────── */
[data-testid="collapsedControl"] { display: none !important; }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #111827 100%) !important;
    border-right: 1px solid #1e293b !important;
    min-width: 280px !important;
    max-width: 320px !important;
    transform: none !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdown"] p {
    color: #94a3b8;
}
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label {
    color: #cbd5e1 !important;
    font-weight: 500;
}

/* ─── Headers ─────────────────────────────────────────────────────── */
h1 {
    font-weight: 700 !important;
    letter-spacing: -0.025em !important;
    color: #f1f5f9 !important;
    font-size: 1.85rem !important;
    padding-bottom: 0.1rem !important;
}
h2, .stSubheader {
    font-weight: 600 !important;
    color: #e2e8f0 !important;
    letter-spacing: -0.015em !important;
    font-size: 1.25rem !important;
}
h3 {
    font-weight: 600 !important;
    color: #cbd5e1 !important;
    font-size: 1.05rem !important;
}

/* ─── Captions & small text ───────────────────────────────────────── */
[data-testid="stCaptionContainer"] p {
    color: #64748b !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.01em;
}

/* ─── Metrics ──────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1e293b 0%, #1a2332 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 20px 18px 16px;
    transition: border-color 0.25s ease, box-shadow 0.25s ease;
}
[data-testid="stMetric"]:hover {
    border-color: #14b8a644;
    box-shadow: 0 0 20px #14b8a612;
}
[data-testid="stMetric"] label {
    color: #94a3b8 !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #f1f5f9 !important;
    font-weight: 700 !important;
    font-size: 1.6rem !important;
}

/* ─── Buttons ──────────────────────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #14b8a6 0%, #0d9488 100%) !important;
    color: #042f2e !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 0.55rem 1.6rem !important;
    letter-spacing: 0.01em;
    transition: all 0.2s ease !important;
    box-shadow: 0 1px 3px rgba(20, 184, 166, 0.2);
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(20, 184, 166, 0.25) !important;
    background: linear-gradient(135deg, #2dd4bf 0%, #14b8a6 100%) !important;
}
.stButton > button:active {
    transform: translateY(0px) !important;
}
/* Secondary / non-primary buttons */
.stButton > button[kind="secondary"] {
    background: transparent !important;
    color: #94a3b8 !important;
    border: 1px solid #334155 !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #14b8a6 !important;
    color: #14b8a6 !important;
    background: #14b8a60a !important;
}

/* ─── Download button ─────────────────────────────────────────────── */
.stDownloadButton > button {
    background: transparent !important;
    color: #94a3b8 !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}
.stDownloadButton > button:hover {
    border-color: #14b8a6 !important;
    color: #14b8a6 !important;
    background: #14b8a60a !important;
}

/* ─── Inputs ───────────────────────────────────────────────────────── */
.stTextArea textarea, .stTextInput input {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif !important;
    transition: border-color 0.2s ease !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #14b8a6 !important;
    box-shadow: 0 0 0 2px #14b8a622 !important;
}

/* ─── Selectbox / Multiselect ─────────────────────────────────────── */
.stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div {
    background: #1e293b !important;
    border-color: #334155 !important;
    border-radius: 10px !important;
}

/* ─── Dataframes ───────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid #1e293b;
    border-radius: 12px;
    overflow: hidden;
}

/* ─── Expander ─────────────────────────────────────────────────────── */
.streamlit-expanderHeader {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-weight: 500 !important;
}

/* ─── Divider ──────────────────────────────────────────────────────── */
[data-testid="stHorizontalBlock"] hr,
hr {
    border-color: #1e293b !important;
    opacity: 0.6;
}

/* ─── Alerts ───────────────────────────────────────────────────────── */
.stAlert [data-testid="stAlertContentInfo"] {
    background: #1e3a5f20 !important;
    border-left-color: #3b82f6 !important;
}
.stAlert [data-testid="stAlertContentSuccess"] {
    background: #14532d20 !important;
}
.stAlert [data-testid="stAlertContentWarning"] {
    background: #78350f20 !important;
}
.stAlert [data-testid="stAlertContentError"] {
    background: #7f1d1d20 !important;
}

/* ─── Tabs ─────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 1px solid #1e293b;
}
.stTabs [data-baseweb="tab"] {
    color: #64748b !important;
    font-weight: 500;
    border-bottom: 2px solid transparent;
    padding: 8px 18px;
    transition: all 0.2s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #94a3b8 !important;
}
.stTabs [aria-selected="true"] {
    color: #14b8a6 !important;
    border-bottom: 2px solid #14b8a6 !important;
}

/* ─── Progress bar ─────────────────────────────────────────────────── */
.stProgress > div > div {
    background: linear-gradient(90deg, #14b8a6, #0d9488) !important;
    border-radius: 999px;
}

/* ─── Slider ───────────────────────────────────────────────────────── */
[data-testid="stSlider"] [role="slider"] {
    background: #14b8a6 !important;
}

/* ─── Toggle ───────────────────────────────────────────────────────── */
[data-testid="stCheckbox"] label span {
    color: #94a3b8 !important;
}


/* ─── Custom component classes ─────────────────────────────────────── */

.eg-page-header {
    margin-bottom: 2rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid #1e293b;
}
.eg-page-header h1 {
    margin-bottom: 0 !important;
    padding-bottom: 0 !important;
}
.eg-page-header .subtitle {
    color: #64748b;
    font-size: 0.92rem;
    margin-top: 6px;
    line-height: 1.6;
}

.eg-card {
    background: linear-gradient(135deg, #1e293b 0%, #1a2332 100%);
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 22px 24px;
    margin-bottom: 16px;
    transition: border-color 0.25s ease, box-shadow 0.25s ease, transform 0.2s ease;
}
.eg-card:hover {
    border-color: #475569;
    box-shadow: 0 4px 24px rgba(0,0,0,0.15);
    transform: translateY(-1px);
}

.eg-card-accent {
    border-left: 3px solid #14b8a6;
    border-color: #14b8a622;
}

.eg-stat-card {
    text-align: center;
    padding: 24px 16px;
}
.eg-stat-card .stat-label {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #64748b;
    margin-bottom: 8px;
}
.eg-stat-card .stat-value {
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    line-height: 1.1;
}
.eg-stat-card .stat-sub {
    font-size: 0.78rem;
    color: #64748b;
    margin-top: 6px;
}

.eg-score-green { color: #22c55e; }
.eg-score-amber { color: #f59e0b; }
.eg-score-red   { color: #ef4444; }
.eg-score-teal  { color: #14b8a6; }
.eg-score-blue  { color: #3b82f6; }

.eg-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 4px 12px;
    border-radius: 999px;
    line-height: 1.4;
}
.eg-badge-green  { background: #22c55e18; color: #4ade80; border: 1px solid #22c55e33; }
.eg-badge-red    { background: #ef444418; color: #f87171; border: 1px solid #ef444433; }
.eg-badge-amber  { background: #f59e0b18; color: #fbbf24; border: 1px solid #f59e0b33; }
.eg-badge-teal   { background: #14b8a618; color: #2dd4bf; border: 1px solid #14b8a633; }
.eg-badge-blue   { background: #3b82f618; color: #60a5fa; border: 1px solid #3b82f633; }
.eg-badge-purple { background: #8b5cf618; color: #a78bfa; border: 1px solid #8b5cf633; }
.eg-badge-gray   { background: #64748b18; color: #94a3b8; border: 1px solid #64748b33; }

.eg-section-title {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #64748b;
    margin-bottom: 16px;
    padding-bottom: 10px;
    border-bottom: 1px solid #1e293b;
}

/* Breathing glow for important live indicators */
@keyframes breathe {
    0%, 100% { box-shadow: 0 0 8px #14b8a620; }
    50% { box-shadow: 0 0 20px #14b8a640; }
}
.eg-live-indicator {
    animation: breathe 3s ease-in-out infinite;
}

/* Fade in animation for cards */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
}
.eg-animate {
    animation: fadeInUp 0.4s ease-out forwards;
}

/* Pulse dot for live status */
@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(1.3); }
}
.eg-pulse-dot {
    display: inline-block;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #22c55e;
    animation: pulse-dot 2s ease-in-out infinite;
    margin-right: 6px;
    vertical-align: middle;
}

/* Reduce motion for accessibility */
@media (prefers-reduced-motion: reduce) {
    .eg-animate { animation: none; }
    .eg-live-indicator { animation: none; }
    .eg-pulse-dot { animation: none; }
    .eg-card:hover { transform: none; }
    .stButton > button:hover { transform: none !important; }
}

/* ─── Responsive ───────────────────────────────────────────────────── */
@media (max-width: 768px) {
    h1 { font-size: 1.4rem !important; }
    .eg-stat-card .stat-value { font-size: 1.6rem; }
    .eg-card { padding: 16px; }
}

/* ─── Scrollbar ────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0b1120; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: #475569; }

/* ─── Hide default Streamlit branding ──────────────────────────────── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* ─── Layout spacing ──────────────────────────────────────────────── */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 1rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}
</style>
"""


# ── Injection function — call once at the top of every page ──────────────────

def inject_theme():
    """Inject the master CSS into the current page."""
    st.markdown(_MASTER_CSS, unsafe_allow_html=True)


# ── Reusable component helpers ───────────────────────────────────────────────

def page_header(title: str, subtitle: str = ""):
    """Render a styled page header with optional subtitle."""
    sub_html = f'<div class="subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div class="eg-page-header eg-animate">'
        f'<h1>{title}</h1>'
        f'{sub_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def section_label(text: str):
    """Render an uppercase section divider label."""
    st.markdown(f'<div class="eg-section-title">{text}</div>', unsafe_allow_html=True)


def stat_card(label: str, value, color_class: str = "eg-score-teal", sub: str = ""):
    """Render a single stat card as styled HTML."""
    # Accept short names like "green" and auto-prefix
    if not color_class.startswith("eg-score-"):
        color_class = f"eg-score-{color_class}"
    sub_html = f'<div class="stat-sub">{sub}</div>' if sub else ""
    st.markdown(
        f'<div class="eg-card eg-stat-card eg-animate">'
        f'<div class="stat-label">{label}</div>'
        f'<div class="stat-value {color_class}">{value}</div>'
        f'{sub_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def score_color_class(value: float) -> str:
    """Return a CSS class based on score value."""
    if value >= 80:
        return "eg-score-green"
    if value >= 60:
        return "eg-score-amber"
    return "eg-score-red"


def score_color_hex(value: float) -> str:
    """Return a hex color string based on score value."""
    if value >= 80:
        return C_SUCCESS
    if value >= 60:
        return C_WARNING
    return C_DANGER


def badge(text: str, variant: str = "teal") -> str:
    """Return HTML for an inline badge. Use inside st.markdown(unsafe_allow_html=True)."""
    return f'<span class="eg-badge eg-badge-{variant}">{text}</span>'


def status_badge(status: str) -> str:
    """Return HTML badge for ALLOWED / BLOCKED / FLAGGED status."""
    variant_map = {
        "ALLOWED": "green",
        "BLOCKED": "red",
        "FLAGGED": "amber",
        "ERROR": "red",
        "UNKNOWN": "gray",
        "PASS": "green",
    }
    return badge(status, variant_map.get(status.upper(), "gray"))


def live_dot() -> str:
    """Return HTML for a green pulsing dot indicator."""
    return '<span class="eg-pulse-dot"></span>'


def card_open(accent: bool = False, extra_class: str = "") -> str:
    """Return opening div for an eg-card."""
    classes = "eg-card eg-animate"
    if accent:
        classes += " eg-card-accent"
    if extra_class:
        classes += f" {extra_class}"
    return f'<div class="{classes}">'


def card_close() -> str:
    return "</div>"


def sidebar_branding():
    """Render subtle branding in the sidebar."""
    st.sidebar.markdown(
        '<div style="text-align:center; padding:18px 0 10px; border-top:1px solid #1e293b; margin-top:32px;">'
        '<div style="font-size:0.7rem; color:#475569; letter-spacing:0.05em;">'
        'ETHICSGUARD v0.4'
        '</div>'
        '<div style="font-size:0.62rem; color:#334155; margin-top:4px;">'
        'AI Safety Middleware'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
