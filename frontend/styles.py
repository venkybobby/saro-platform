"""
SARO Enterprise Dark Theme v2.2
================================
Inject via styles.apply() in app.py and each tab's render() function.
"""
from __future__ import annotations

import streamlit as st


ENTERPRISE_CSS = """
<style>
/* ═══════════════════════════════════════════════════════
   SARO Enterprise Dark Theme v2.2
   ═══════════════════════════════════════════════════════ */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── App shell ────────────────────────────────────────── */
.stApp {
    background-color: #0f1117 !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}
.main .block-container {
    padding: 1.5rem 2rem !important;
    max-width: 1440px !important;
    background: #0f1117 !important;
}

/* ── Hide Streamlit chrome ────────────────────────────── */
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
[data-testid="stDecoration"] { display: none !important; }
header[data-testid="stHeader"] {
    background: #0f1117 !important;
    border-bottom: 1px solid #1e2433 !important;
}

/* ── Sidebar ──────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #12172a !important;
    border-right: 1px solid #1e2d45 !important;
}
[data-testid="stSidebar"] .block-container {
    padding-top: 1.2rem !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label {
    color: #94a3b8 !important;
    font-size: 0.85rem !important;
}
[data-testid="stSidebar"] strong,
[data-testid="stSidebar"] b {
    color: #e2e8f0 !important;
}
[data-testid="stSidebar"] h2 {
    color: #f1f5f9 !important;
    font-size: 1.1rem !important;
}

/* ── Typography ───────────────────────────────────────── */
h1, h2, h3, h4, h5, h6 {
    color: #f1f5f9 !important;
    font-family: 'Inter', sans-serif !important;
    letter-spacing: -0.02em !important;
}
h1 { font-size: 1.8rem !important; font-weight: 700 !important; }
h2 { font-size: 1.35rem !important; font-weight: 600 !important; }
h3 { font-size: 1.1rem !important; font-weight: 600 !important; }
p, li { color: #cbd5e1 !important; }

/* ── Metric cards ─────────────────────────────────────── */
[data-testid="stMetric"] {
    background: #1a2035 !important;
    border: 1px solid #243050 !important;
    border-radius: 10px !important;
    padding: 14px 18px !important;
    transition: border-color 0.18s ease, box-shadow 0.18s ease !important;
}
[data-testid="stMetric"]:hover {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 1px rgba(59,130,246,0.15) !important;
}
[data-testid="stMetricLabel"] > div {
    color: #64748b !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}
[data-testid="stMetricValue"] {
    color: #f1f5f9 !important;
    font-size: 1.9rem !important;
    font-weight: 700 !important;
}

/* ── Primary buttons ──────────────────────────────────── */
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 7px !important;
    letter-spacing: 0.01em !important;
    transition: all 0.15s ease !important;
    font-size: 0.87rem !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
    border: none !important;
    color: #fff !important;
    box-shadow: 0 1px 3px rgba(59,130,246,0.35) !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%) !important;
    box-shadow: 0 4px 14px rgba(59,130,246,0.45) !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="secondary"] {
    background: #1a2035 !important;
    border: 1px solid #2d3f5e !important;
    color: #cbd5e1 !important;
}
.stButton > button[kind="secondary"]:hover {
    background: #243050 !important;
    border-color: #3b82f6 !important;
    color: #e2e8f0 !important;
}

/* ── Download buttons ─────────────────────────────────── */
.stDownloadButton > button {
    background: #1a2035 !important;
    border: 1px solid #2d3f5e !important;
    color: #cbd5e1 !important;
    border-radius: 7px !important;
    font-weight: 600 !important;
    font-size: 0.87rem !important;
    transition: all 0.15s ease !important;
}
.stDownloadButton > button:hover {
    background: #243050 !important;
    border-color: #3b82f6 !important;
    color: #e2e8f0 !important;
}

/* ── Tabs ─────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: #12172a !important;
    border-radius: 9px !important;
    padding: 4px !important;
    gap: 2px !important;
    border-bottom: none !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #64748b !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    border: none !important;
    padding: 8px 18px !important;
    font-size: 0.87rem !important;
    transition: all 0.15s ease !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #cbd5e1 !important;
    background: #1a2035 !important;
}
.stTabs [aria-selected="true"] {
    background: #243050 !important;
    color: #e2e8f0 !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.3) !important;
}

/* ── Inputs & Textareas ───────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
    background: #1a2035 !important;
    color: #e2e8f0 !important;
    border: 1px solid #2d3f5e !important;
    border-radius: 7px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.12) !important;
    outline: none !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {
    color: #4a5568 !important;
}
label,
.stTextInput label,
.stTextArea label,
.stSelectbox label,
.stNumberInput label,
.stSlider label {
    color: #64748b !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
}

/* ── Selectbox ────────────────────────────────────────── */
[data-baseweb="select"] > div {
    background: #1a2035 !important;
    border: 1px solid #2d3f5e !important;
    border-radius: 7px !important;
    color: #e2e8f0 !important;
}
[data-baseweb="popover"] > div {
    background: #1a2035 !important;
    border: 1px solid #2d3f5e !important;
    border-radius: 8px !important;
}
[data-baseweb="menu"] {
    background: #1a2035 !important;
}
[role="option"] {
    color: #cbd5e1 !important;
    background: #1a2035 !important;
}
[role="option"]:hover {
    background: #243050 !important;
}

/* ── Expanders ────────────────────────────────────────── */
.streamlit-expanderHeader {
    background: #1a2035 !important;
    border: 1px solid #243050 !important;
    border-radius: 8px !important;
    color: #cbd5e1 !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    transition: background 0.15s ease !important;
}
.streamlit-expanderHeader:hover {
    background: #243050 !important;
    border-color: #3b82f6 !important;
}
.streamlit-expanderContent {
    background: #111827 !important;
    border: 1px solid #1e2d45 !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
    padding: 12px !important;
}

/* ── Alert / Info / Warning / Error / Success ─────────── */
[data-testid="stAlert"] {
    border-radius: 8px !important;
    border-left-width: 4px !important;
}
div[data-testid="stAlert"][data-baseweb="notification"] {
    background: #1a2035 !important;
}
/* Info */
div[class*="stInfo"] {
    background: rgba(30,58,138,0.25) !important;
    border-left-color: #3b82f6 !important;
    color: #bfdbfe !important;
}
/* Success */
div[class*="stSuccess"] {
    background: rgba(6,78,59,0.3) !important;
    border-left-color: #10b981 !important;
    color: #6ee7b7 !important;
}
/* Warning */
div[class*="stWarning"] {
    background: rgba(78,56,8,0.4) !important;
    border-left-color: #f59e0b !important;
    color: #fde68a !important;
}
/* Error */
div[class*="stError"] {
    background: rgba(127,29,29,0.35) !important;
    border-left-color: #ef4444 !important;
    color: #fca5a5 !important;
}

/* ── Code / Pre ───────────────────────────────────────── */
code, .stCode {
    background: #0d1117 !important;
    border: 1px solid #1e2d45 !important;
    border-radius: 5px !important;
    color: #7dd3fc !important;
    font-size: 0.85rem !important;
}
pre, [data-testid="stCodeBlock"] {
    background: #0d1117 !important;
    border: 1px solid #1e2d45 !important;
    border-radius: 8px !important;
}

/* ── Dividers ─────────────────────────────────────────── */
hr {
    border-color: #1e2d45 !important;
    margin: 1rem 0 !important;
}

/* ── Radio buttons ────────────────────────────────────── */
.stRadio > div > label {
    color: #94a3b8 !important;
    font-size: 0.9rem !important;
}
.stRadio > div > label[data-checked="true"],
.stRadio [aria-checked="true"] + div {
    color: #f1f5f9 !important;
}

/* ── Toggle ───────────────────────────────────────────── */
.stToggle label {
    color: #94a3b8 !important;
    font-size: 0.85rem !important;
    text-transform: none !important;
    letter-spacing: 0 !important;
}

/* ── Checkbox ─────────────────────────────────────────── */
.stCheckbox > label {
    color: #cbd5e1 !important;
    font-size: 0.9rem !important;
    font-weight: 400 !important;
    text-transform: none !important;
    letter-spacing: 0 !important;
}

/* ── Multiselect ──────────────────────────────────────── */
[data-baseweb="tag"] {
    background: #1d4ed8 !important;
    border-radius: 5px !important;
}
[data-baseweb="tag"] span {
    color: #bfdbfe !important;
}

/* ── Captions ─────────────────────────────────────────── */
.stCaption, small {
    color: #475569 !important;
    font-size: 0.8rem !important;
}

/* ── Spinner ──────────────────────────────────────────── */
[data-testid="stSpinner"] > div {
    border-top-color: #3b82f6 !important;
}

/* ── Form ─────────────────────────────────────────────── */
[data-testid="stForm"] {
    background: #12172a !important;
    border: 1px solid #1e2d45 !important;
    border-radius: 10px !important;
    padding: 20px !important;
}

/* ── Scrollbars ───────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #0f1117; }
::-webkit-scrollbar-thumb { background: #2d3f5e; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #3b82f6; }

/* ── SARO Utility Classes ─────────────────────────────── */

/* Enterprise card */
.saro-card {
    background: #1a2035;
    border: 1px solid #243050;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 14px;
    transition: border-color 0.18s ease;
}
.saro-card:hover { border-color: #3b4f7c; }

/* Loading skeleton */
@keyframes saro-shimmer {
    0%   { background-position: -800px 0; }
    100% { background-position:  800px 0; }
}
.saro-skeleton {
    background: linear-gradient(90deg, #1a2035 25%, #243050 50%, #1a2035 75%);
    background-size: 800px 100%;
    animation: saro-shimmer 1.8s infinite linear;
    border-radius: 6px;
    height: 20px;
    margin: 6px 0;
}

/* Risk badge */
.saro-risk-low    { background:#052e16; color:#4ade80; border:1px solid #166534; }
.saro-risk-mod    { background:#422006; color:#fbbf24; border:1px solid #92400e; }
.saro-risk-high   { background:#450a0a; color:#f87171; border:1px solid #991b1b; }
.saro-risk-badge  {
    display:inline-flex; align-items:center; gap:6px;
    padding:3px 12px; border-radius:20px;
    font-weight:700; font-size:0.78rem; letter-spacing:0.06em;
}

/* Visual timeline (trace) */
.saro-timeline {
    display: flex;
    align-items: flex-start;
    gap: 0;
    margin: 24px 0;
    overflow-x: auto;
    padding-bottom: 8px;
}
.saro-tl-step {
    flex: 1;
    min-width: 110px;
    text-align: center;
    position: relative;
    padding: 0 4px;
}
.saro-tl-line {
    position: absolute;
    top: 19px;
    left: 0; right: 0;
    height: 2px;
    background: #1e2d45;
    z-index: 0;
}
.saro-tl-step:first-child .saro-tl-line { left: 50%; }
.saro-tl-step:last-child  .saro-tl-line { right: 50%; }
.saro-tl-node {
    width: 38px; height: 38px;
    border-radius: 50%;
    background: #1a2035;
    border: 2px solid #3b82f6;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 8px;
    font-weight: 700; font-size: 0.85rem; color: #60a5fa;
    position: relative; z-index: 1;
}
.saro-tl-node.done  { background: #1e3a5f; border-color: #10b981; color: #34d399; }
.saro-tl-node.warn  { background: #3d2a00; border-color: #f59e0b; color: #fbbf24; }
.saro-tl-node.fail  { background: #450a0a; border-color: #ef4444; color: #f87171; }
.saro-tl-label {
    font-size: 0.68rem; font-weight: 600;
    color: #475569; text-transform: uppercase; letter-spacing: 0.05em;
    line-height: 1.3;
}

/* Deviation callout */
.saro-deviation {
    background: rgba(127,29,29,0.3);
    border: 1px solid #dc2626;
    border-left: 4px solid #dc2626;
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    margin: 8px 0;
}
.saro-deviation-title {
    color: #f87171;
    font-weight: 700; font-size: 0.8rem;
    text-transform: uppercase; letter-spacing: 0.08em;
    margin-bottom: 4px;
}

/* Human-in-the-loop missing */
.saro-hitl-missing {
    background: rgba(78,56,8,0.35);
    border: 1px solid #d97706;
    border-left: 4px solid #d97706;
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    margin: 8px 0;
    color: #fde68a;
    font-size: 0.87rem;
    font-weight: 500;
}

/* Magic-link warning banner */
.saro-magic-link-banner {
    background: rgba(127,29,29,0.4);
    border: 1px solid #dc2626;
    border-left: 4px solid #dc2626;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin: 12px 0;
    color: #fca5a5;
    font-weight: 600;
    font-size: 0.9rem;
}

/* Audit log preview */
.saro-audit-log {
    background: #0d1117;
    border: 1px solid #1e2d45;
    border-radius: 8px;
    padding: 12px 16px;
    font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
    font-size: 0.78rem;
    color: #4ade80;
    max-height: 180px;
    overflow-y: auto;
    line-height: 1.7;
}

/* Empty state */
.saro-empty {
    text-align: center;
    padding: 56px 24px;
}
.saro-empty-icon { font-size: 3.5rem; margin-bottom: 16px; opacity: 0.35; }
.saro-empty-title { font-size: 1.15rem; font-weight: 600; color: #64748b; margin-bottom: 8px; }
.saro-empty-body  { font-size: 0.88rem; color: #475569; margin-bottom: 24px; }

/* Section header pill */
.saro-section-pill {
    display: inline-flex; align-items: center; gap: 8px;
    background: #1a2035; border: 1px solid #243050;
    border-radius: 20px; padding: 4px 14px;
    font-size: 0.75rem; font-weight: 600; color: #64748b;
    text-transform: uppercase; letter-spacing: 0.08em;
    margin-bottom: 16px;
}

/* Effort pill */
.saro-effort-HIGH { background:#450a0a; color:#f87171; border:1px solid #991b1b; }
.saro-effort-MED  { background:#422006; color:#fbbf24; border:1px solid #92400e; }
.saro-effort-LOW  { background:#052e16; color:#4ade80; border:1px solid #166534; }
.saro-effort-pill {
    display:inline-flex; align-items:center; gap:5px;
    padding:2px 10px; border-radius:20px;
    font-weight:700; font-size:0.72rem; letter-spacing:0.06em;
}

/* Confidence badge */
.saro-conf-badge {
    display:inline-flex; align-items:center; gap:6px;
    padding:4px 14px; border-radius:20px;
    font-weight:700; font-size:0.85rem;
    margin-bottom:12px;
}
.saro-conf-high { background:#052e16; color:#4ade80; border:1px solid #166534; }
.saro-conf-med  { background:#422006; color:#fbbf24; border:1px solid #92400e; }
.saro-conf-low  { background:#450a0a; color:#f87171; border:1px solid #991b1b; }

/* MFA locked badge */
.saro-mfa-locked {
    background: #052e16;
    border: 1px solid #166534;
    border-radius: 8px;
    padding: 10px 16px;
    color: #4ade80;
    font-weight: 600;
    font-size: 0.88rem;
    display: flex; align-items: center; gap: 8px;
}

/* Highlighted metadata row */
.saro-meta-row {
    display: flex; flex-wrap: wrap; gap: 16px;
    background: #12172a; border: 1px solid #1e2d45;
    border-radius: 8px; padding: 10px 16px;
    margin: 10px 0; font-size: 0.82rem;
}
.saro-meta-item { color: #64748b; }
.saro-meta-item b { color: #94a3b8; }
</style>
"""


def apply() -> None:
    """Inject the enterprise dark CSS into the current Streamlit page."""
    st.markdown(ENTERPRISE_CSS, unsafe_allow_html=True)


def magic_link_banner() -> str:
    """Return the locked magic-link warning HTML."""
    return (
        '<div class="saro-magic-link-banner">'
        '⚠️ Non-Enterprise / Testing Mode Only — '
        'Not recommended for production AI risk/ethics workloads. '
        'Enable SSO above to remove this restriction.'
        '</div>'
    )


def risk_badge_html(color: str | None, score: float | None) -> str:
    cls = {"green": "saro-risk-low", "yellow": "saro-risk-mod", "red": "saro-risk-high"}.get(color or "", "saro-risk-mod")
    label = {"green": "LOW RISK", "yellow": "MODERATE RISK", "red": "HIGH RISK"}.get(color or "", "—")
    if score is None:
        return "—"
    return (
        f'<span class="saro-risk-badge {cls}">'
        f'{score:.0f} {label}'
        f'</span>'
    )


def effort_pill(effort: str) -> str:
    cls = f"saro-effort-{effort}"
    return f'<span class="saro-effort-pill {cls}">EFFORT: {effort}</span>'


def conf_badge(conf: float | None) -> str:
    if conf is None:
        return '<span class="saro-conf-badge saro-conf-low">Confidence: N/A</span>'
    if conf >= 0.9:
        cls, label = "saro-conf-high", f"Confidence: {conf:.0%}"
    elif conf >= 0.7:
        cls, label = "saro-conf-med", f"Confidence: {conf:.0%}"
    else:
        cls, label = "saro-conf-low", f"Confidence: {conf:.0%} — Review Required"
    return f'<span class="saro-conf-badge {cls}">● {label}</span>'


def timeline_html(steps: list[dict]) -> str:
    """
    Render the 6-step SARO trace timeline as HTML.
    steps is a list of dicts: {"label": str, "status": "done"|"warn"|"fail"|"pending"}
    """
    parts = ['<div class="saro-timeline">']
    for i, step in enumerate(steps):
        status = step.get("status", "done")
        node_class = f"saro-tl-node {status}"
        parts.append(
            f'<div class="saro-tl-step">'
            f'  <div class="saro-tl-line"></div>'
            f'  <div class="{node_class}">{i + 1}</div>'
            f'  <div class="saro-tl-label">{step["label"]}</div>'
            f'</div>'
        )
    parts.append("</div>")
    return "\n".join(parts)


def deviation_callout(text: str) -> str:
    return (
        '<div class="saro-deviation">'
        '<div class="saro-deviation-title">⚠ Deviation Detected</div>'
        f'<div style="color:#fca5a5;font-size:0.87rem">{text}</div>'
        '</div>'
    )


def hitl_missing_banner() -> str:
    return (
        '<div class="saro-hitl-missing">'
        '⚠ <b>Human-in-the-Loop checkpoint not detected</b> — '
        'this output was processed without an explicit human review gate. '
        'NIST AI RMF GOVERN 1.7 requires documented human oversight for high-risk decisions.'
        '</div>'
    )


def empty_state(icon: str, title: str, body: str) -> str:
    return (
        f'<div class="saro-empty">'
        f'  <div class="saro-empty-icon">{icon}</div>'
        f'  <div class="saro-empty-title">{title}</div>'
        f'  <div class="saro-empty-body">{body}</div>'
        f'</div>'
    )


def audit_log_html(entries: list[str]) -> str:
    rows = "\n".join(entries)
    return f'<div class="saro-audit-log">{rows}</div>'


def meta_row(**kwargs: str) -> str:
    items = "".join(
        f'<span class="saro-meta-item"><b>{k}:</b> {v}</span>'
        for k, v in kwargs.items()
    )
    return f'<div class="saro-meta-row">{items}</div>'
