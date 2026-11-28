import streamlit as st
import os
import subprocess
from engine import run_forensic_analysis

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="VocalGuard · Voice Forensics",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ─── Global CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;500;600;700&family=Orbitron:wght@400;700;900&display=swap');

/* ══════════════════════════════════════════
   ROOT TOKENS — dark mode defaults
   ══════════════════════════════════════════ */
:root {
    --bg-primary:   #060a10;
    --bg-card:      #0b1120;
    --bg-card2:     #0e1628;
    --border:       #1a2d4a;
    --border-glow:  #00e5ff;
    --cyan:         #00e5ff;
    --cyan-dim:     #00bcd4;
    --green:        #00c97a;
    --red:          #ff3b5c;
    --yellow:       #f5c400;
    --text:         #c8d8e8;
    --text-dim:     #5a7a9a;
    --mono:         'Share Tech Mono', 'Courier New', monospace;
    --head:         'Orbitron', 'Arial Black', monospace;
    --body:         'Rajdhani', system-ui, sans-serif;
}

/* ── Light mode overrides ── */
@media (prefers-color-scheme: light) {
    :root {
        --bg-primary:  #f0f4f8;
        --bg-card:     #ffffff;
        --bg-card2:    #e8eef5;
        --border:      #c0cdd8;
        --border-glow: #0097b2;
        --cyan:        #007a99;
        --cyan-dim:    #005f77;
        --green:       #007a4a;
        --red:         #cc1f3c;
        --yellow:      #9a7a00;
        --text:        #1a2535;
        --text-dim:    #5a7080;
    }
}

/* ══════════════════════════════════════════
   GLOBAL RESET
   ══════════════════════════════════════════ */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"] {
    background: var(--bg-primary) !important;
    color: var(--text) !important;
    font-family: var(--body) !important;
}

/* Scanline overlay — dark mode only */
@media (prefers-color-scheme: dark) {
    [data-testid="stApp"]::before {
        content: '';
        position: fixed;
        inset: 0;
        background: repeating-linear-gradient(
            0deg,
            transparent 0px,
            transparent 2px,
            rgba(0,229,255,0.010) 2px,
            rgba(0,229,255,0.010) 4px
        );
        pointer-events: none;
        z-index: 9999;
    }
}

/* ══════════════════════════════════════════
   STREAMLIT HEADER — keep visible for sidebar toggle
   ══════════════════════════════════════════ */
#MainMenu,
footer,
.stDeployButton,
[data-testid="stToolbar"] {
    display: none !important;
    visibility: hidden !important;
}

/* Keep header shell alive (holds sidebar button) */
header[data-testid="stHeader"] {
    background: transparent !important;
    box-shadow: none !important;
    visibility: visible !important;
    pointer-events: auto !important;
}

/* ══════════════════════════════════════════
   SIDEBAR TOGGLE BUTTON — all Streamlit versions
   ══════════════════════════════════════════ */
/* Collapsed state button */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    pointer-events: auto !important;
    z-index: 10000 !important;
}

/* Expanded state close button */
[data-testid="stSidebarCollapseButton"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    pointer-events: auto !important;
}

/* Button styling — both states */
[data-testid="collapsedControl"] button,
[data-testid="stSidebarCollapsedControl"] button,
[data-testid="stSidebarCollapseButton"] button {
    background: var(--bg-card) !important;
    border: 1px solid var(--cyan-dim) !important;
    border-radius: 6px !important;
    color: var(--cyan) !important;
    box-shadow: 0 0 10px rgba(0,180,210,0.20) !important;
    transition: background 0.18s ease, box-shadow 0.18s ease !important;
    min-width: 36px !important;
    min-height: 36px !important;
}

[data-testid="collapsedControl"] button:hover,
[data-testid="stSidebarCollapsedControl"] button:hover,
[data-testid="stSidebarCollapseButton"] button:hover {
    background: rgba(0,180,210,0.12) !important;
    box-shadow: 0 0 16px rgba(0,180,210,0.35) !important;
}

/* SVG icons inside buttons */
[data-testid="collapsedControl"] svg,
[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="stSidebarCollapseButton"] svg {
    fill: var(--cyan) !important;
    stroke: var(--cyan) !important;
    color: var(--cyan) !important;
}

/* ══════════════════════════════════════════
   SIDEBAR
   ══════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: var(--bg-card) !important;
    border-right: 1px solid var(--border) !important;
    min-width: 240px !important;
}

[data-testid="stSidebar"] * {
    font-family: var(--body) !important;
}

[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] li {
    color: var(--text) !important;
}

/* Sidebar scrollbar */
[data-testid="stSidebar"]::-webkit-scrollbar { width: 3px; }
[data-testid="stSidebar"]::-webkit-scrollbar-track { background: transparent; }
[data-testid="stSidebar"]::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

/* ══════════════════════════════════════════
   MAIN CONTAINER
   ══════════════════════════════════════════ */
.block-container {
    max-width: 820px !important;
    padding: 2rem 1.5rem 4rem !important;
    margin: 0 auto !important;
}

@media (max-width: 600px) {
    .block-container {
        padding: 1rem 0.75rem 3rem !important;
    }
}

/* ══════════════════════════════════════════
   HEADER
   ══════════════════════════════════════════ */
.vg-header {
    text-align: center;
    padding: 2rem 0 1.2rem;
}

.vg-logo {
    font-family: var(--head);
    font-size: clamp(1.6rem, 5vw, 2.4rem);
    font-weight: 900;
    letter-spacing: 0.12em;
    background: linear-gradient(135deg, var(--cyan) 0%, #7b61ff 55%, var(--cyan-dim) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.2;
}

.vg-sub {
    font-family: var(--mono);
    font-size: clamp(0.58rem, 1.5vw, 0.7rem);
    color: var(--text-dim);
    letter-spacing: 0.22em;
    text-transform: uppercase;
    margin-top: 0.4rem;
}

.vg-version {
    display: inline-block;
    font-family: var(--mono);
    font-size: 0.6rem;
    color: var(--cyan-dim);
    border: 1px solid var(--cyan-dim);
    border-radius: 3px;
    padding: 2px 10px;
    letter-spacing: 0.15em;
    margin-top: 0.6rem;
}

.vg-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--cyan), transparent);
    margin: 1.2rem 0;
    opacity: 0.35;
}

/* ══════════════════════════════════════════
   UPLOAD ZONE
   ══════════════════════════════════════════ */
.upload-label {
    font-family: var(--mono);
    font-size: 0.7rem;
    color: var(--cyan-dim);
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}

[data-testid="stFileUploaderDropzone"] {
    background: var(--bg-card) !important;
    border: 1px dashed var(--border-glow) !important;
    border-radius: 8px !important;
    transition: background 0.25s, border-color 0.25s, box-shadow 0.25s !important;
}

[data-testid="stFileUploaderDropzone"]:hover {
    background: var(--bg-card2) !important;
    border-color: var(--cyan) !important;
    box-shadow: 0 0 18px rgba(0,180,210,0.10) !important;
}

[data-testid="stFileUploaderDropzoneInstructions"] p,
[data-testid="stFileUploaderDropzoneInstructions"] span {
    color: var(--text-dim) !important;
    font-family: var(--mono) !important;
    font-size: 0.72rem !important;
}

/* File name after upload */
[data-testid="stFileUploaderFileName"],
.uploadedFileName {
    color: var(--text) !important;
    font-family: var(--mono) !important;
    font-size: 0.72rem !important;
}

/* ══════════════════════════════════════════
   SCANNING ANIMATION
   ══════════════════════════════════════════ */
@keyframes scanPulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.4; }
}
@keyframes scanLine {
    0%   { top: 0%; }
    100% { top: 100%; }
}

.scan-box {
    background: var(--bg-card);
    border: 1px solid var(--cyan);
    border-radius: 8px;
    padding: 1.5rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 0 24px rgba(0,180,210,0.10);
}
.scan-box::after {
    content: '';
    position: absolute;
    left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--cyan), transparent);
    animation: scanLine 1.8s linear infinite;
    top: 0;
}
.scan-text {
    font-family: var(--mono);
    font-size: 0.72rem;
    color: var(--cyan);
    letter-spacing: 0.22em;
    text-transform: uppercase;
    animation: scanPulse 1.2s ease-in-out infinite;
}

/* ══════════════════════════════════════════
   CHAIN BADGE
   ══════════════════════════════════════════ */
.chain-badge {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.65rem 1rem;
    border-radius: 5px;
    font-family: var(--mono);
    font-size: clamp(0.58rem, 1.6vw, 0.70rem);
    letter-spacing: 0.10em;
    text-transform: uppercase;
    margin-bottom: 1.2rem;
    border-left: 3px solid;
    word-break: break-word;
}
.chain-direct  { background: rgba(0,201,122,0.08); border-color: var(--green); color: var(--green); }
.chain-chain   { background: rgba(245,196,0,0.08);  border-color: var(--yellow); color: var(--yellow); }
.chain-overlap { background: rgba(0,180,210,0.08);  border-color: var(--cyan); color: var(--cyan); }

.chain-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    flex-shrink: 0;
    animation: scanPulse 1.6s ease-in-out infinite;
}

/* ══════════════════════════════════════════
   VERDICT CARD
   ══════════════════════════════════════════ */
.verdict-card {
    border-radius: 10px;
    padding: 1.6rem 1.5rem;
    position: relative;
    overflow: hidden;
    margin-bottom: 1.5rem;
}
.verdict-ai {
    background: linear-gradient(135deg, rgba(255,59,92,0.10) 0%, rgba(255,59,92,0.03) 100%);
    border: 1px solid rgba(255,59,92,0.45);
    box-shadow: 0 0 32px rgba(255,59,92,0.07);
}
.verdict-human {
    background: linear-gradient(135deg, rgba(0,201,122,0.09) 0%, rgba(0,201,122,0.02) 100%);
    border: 1px solid rgba(0,201,122,0.38);
    box-shadow: 0 0 32px rgba(0,201,122,0.06);
}
.verdict-uncertain {
    background: linear-gradient(135deg, rgba(245,196,0,0.09) 0%, rgba(245,196,0,0.02) 100%);
    border: 1px solid rgba(245,196,0,0.38);
    box-shadow: 0 0 32px rgba(245,196,0,0.06);
}

.verdict-icon {
    font-size: clamp(1.6rem, 4vw, 2.2rem);
    margin-bottom: 0.4rem;
    display: block;
}
.verdict-label {
    font-family: var(--head);
    font-size: clamp(1rem, 3.5vw, 1.4rem);
    font-weight: 700;
    letter-spacing: 0.08em;
    margin-bottom: 0.4rem;
    line-height: 1.2;
}
.verdict-label-ai       { color: var(--red); }
.verdict-label-human    { color: var(--green); }
.verdict-label-uncertain{ color: var(--yellow); }

.verdict-sub {
    font-family: var(--mono);
    font-size: 0.65rem;
    color: var(--text-dim);
    letter-spacing: 0.10em;
    margin-bottom: 1.1rem;
}
.verdict-warning {
    font-family: var(--body);
    font-size: clamp(0.78rem, 2vw, 0.88rem);
    font-weight: 500;
    color: var(--text);
    background: rgba(0,0,0,0.20);
    border-radius: 5px;
    padding: 0.6rem 0.9rem;
    letter-spacing: 0.03em;
    line-height: 1.5;
}

/* ── Confidence bars ── */
.conf-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.5rem;
}
.conf-label {
    font-family: var(--mono);
    font-size: 0.62rem;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    width: 50px;
    flex-shrink: 0;
}
.conf-bar-outer {
    flex: 1;
    height: 6px;
    background: rgba(128,128,128,0.15);
    border-radius: 3px;
    overflow: hidden;
}
.conf-bar-inner {
    height: 100%;
    border-radius: 3px;
}
.conf-bar-ai    { background: linear-gradient(90deg, #ff3b5c, #ff7090); }
.conf-bar-human { background: linear-gradient(90deg, #00c97a, #00e5c0); }
.conf-pct {
    font-family: var(--mono);
    font-size: 0.72rem;
    width: 40px;
    text-align: right;
    flex-shrink: 0;
}
.conf-pct-ai    { color: var(--red); }
.conf-pct-human { color: var(--green); }

/* ══════════════════════════════════════════
   SECTION HEADING
   ══════════════════════════════════════════ */
.section-head {
    font-family: var(--mono);
    font-size: 0.62rem;
    letter-spacing: 0.24em;
    text-transform: uppercase;
    color: var(--text-dim);
    margin: 1.6rem 0 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.6rem;
}
.section-head::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, var(--border), transparent);
}

/* ══════════════════════════════════════════
   METRIC GRID — responsive
   ══════════════════════════════════════════ */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.5rem;
    margin-bottom: 0.5rem;
}

@media (max-width: 520px) {
    .metric-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 7px;
    padding: 0.7rem 0.65rem;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.metric-card:hover {
    border-color: var(--cyan);
    box-shadow: 0 0 10px rgba(0,180,210,0.08);
}
.metric-key {
    font-family: var(--mono);
    font-size: 0.52rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--text-dim);
    margin-bottom: 0.28rem;
}
.metric-val {
    font-family: var(--mono);
    font-size: clamp(0.9rem, 2.5vw, 1.1rem);
    color: var(--cyan);
    line-height: 1;
}
.metric-desc {
    font-family: var(--mono);
    font-size: 0.46rem;
    letter-spacing: 0.08em;
    color: var(--text-dim);
    opacity: 0.6;
    margin-top: 0.2rem;
    text-transform: uppercase;
}

/* ══════════════════════════════════════════
   PROFILE MATCH CARD
   ══════════════════════════════════════════ */
.profile-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-left: 3px solid var(--cyan);
    border-radius: 5px;
    padding: 0.7rem 1rem;
    font-family: var(--mono);
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.5rem;
    font-size: clamp(0.62rem, 1.8vw, 0.75rem);
    flex-wrap: wrap;
}
.profile-name { color: var(--cyan); letter-spacing: 0.04em; }
.profile-dist { color: var(--text-dim); font-size: 0.62rem; white-space: nowrap; }

/* ══════════════════════════════════════════
   FLAG LIST
   ══════════════════════════════════════════ */
.flag-item {
    display: flex;
    align-items: flex-start;
    gap: 0.65rem;
    padding: 0.5rem 0.75rem;
    margin-bottom: 0.28rem;
    border-radius: 5px;
    font-family: var(--mono);
    font-size: clamp(0.58rem, 1.6vw, 0.67rem);
    letter-spacing: 0.03em;
    line-height: 1.55;
    border-left: 2px solid;
    word-break: break-word;
}
.flag-ai           { background: rgba(255,59,92,0.06);  border-color: var(--red);    color: #ff8fa8; }
.flag-human        { background: rgba(0,201,122,0.05);  border-color: var(--green);  color: #40dfa0; }
.flag-chain-direct { background: rgba(0,201,122,0.04);  border-color: var(--green);  color: var(--green); }
.flag-chain-chain  { background: rgba(245,196,0,0.05);  border-color: var(--yellow); color: var(--yellow); }
.flag-chain-overlap{ background: rgba(0,180,210,0.05);  border-color: var(--cyan);   color: var(--cyan); }
.flag-warn         { background: rgba(245,196,0,0.05);  border-color: var(--yellow); color: var(--yellow); }
.flag-neutral      { background: rgba(128,128,128,0.04);border-color: var(--border); color: var(--text-dim); }
.flag-dot          { flex-shrink: 0; margin-top: 1px; font-size: 0.75rem; }

/* ══════════════════════════════════════════
   STREAMLIT WIDGET OVERRIDES
   ══════════════════════════════════════════ */
/* File uploader label */
.stFileUploader label {
    color: var(--text) !important;
    font-family: var(--body) !important;
}

/* Select box */
.stSelectbox label {
    color: var(--text) !important;
    font-family: var(--body) !important;
    font-size: 0.85rem !important;
}
.stSelectbox > div > div,
div[data-baseweb="select"] > div {
    background: var(--bg-card2) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
    font-family: var(--mono) !important;
    font-size: 0.78rem !important;
    border-radius: 5px !important;
}
div[data-baseweb="select"] * {
    color: var(--text) !important;
    font-family: var(--mono) !important;
}
/* Dropdown menu */
div[data-baseweb="popover"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
}
div[data-baseweb="menu"] li {
    background: var(--bg-card) !important;
    color: var(--text) !important;
}
div[data-baseweb="menu"] li:hover {
    background: var(--bg-card2) !important;
}

/* Alert / info boxes */
.stAlert { border-radius: 5px !important; }

/* Spinner */
.stSpinner > div { border-top-color: var(--cyan) !important; }

/* Markdown paragraphs */
div[data-testid="stMarkdownContainer"] p {
    font-family: var(--body) !important;
    color: var(--text) !important;
}

/* ══════════════════════════════════════════
   SIDEBAR CONTENT STYLES
   ══════════════════════════════════════════ */
.sb-title {
    font-family: var(--head);
    font-size: 0.72rem;
    letter-spacing: 0.18em;
    color: var(--cyan-dim);
    text-transform: uppercase;
    margin-bottom: 0.75rem;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid var(--border);
}
.sb-badge {
    display: flex;
    align-items: center;
    gap: 0.55rem;
    padding: 0.45rem 0.65rem;
    background: rgba(0,180,210,0.04);
    border: 1px solid var(--border);
    border-radius: 5px;
    margin-bottom: 0.35rem;
    font-family: var(--mono);
    font-size: 0.63rem;
    color: var(--text-dim);
    letter-spacing: 0.06em;
}
.sb-dot-green  { color: var(--green); font-size: 0.8rem; }
.sb-dot-yellow { color: var(--yellow); font-size: 0.8rem; }
.sb-dot-blue   { color: var(--cyan); font-size: 0.8rem; }

.sb-info {
    font-family: var(--mono);
    font-size: 0.62rem;
    color: var(--text-dim);
    letter-spacing: 0.05em;
    line-height: 1.7;
    padding: 0.6rem 0;
    border-top: 1px solid var(--border);
    margin-top: 0.75rem;
}

/* Target label */
.sb-target {
    font-family: var(--mono);
    font-size: 0.62rem;
    color: var(--cyan);
    letter-spacing: 0.10em;
    padding: 0.4rem 0 0.75rem;
}

/* ══════════════════════════════════════════
   GLOBAL SCROLLBAR
   ══════════════════════════════════════════ */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

/* ══════════════════════════════════════════
   FADE-IN ANIMATION
   ══════════════════════════════════════════ */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
.anim-1 { animation: fadeUp 0.35s ease forwards; }
.anim-2 { animation: fadeUp 0.35s 0.08s ease both; }
.anim-3 { animation: fadeUp 0.35s 0.16s ease both; }
.anim-4 { animation: fadeUp 0.35s 0.24s ease both; }

/* ══════════════════════════════════════════
   EMPTY STATE
   ══════════════════════════════════════════ */
.empty-state {
    margin-top: 1.2rem;
    padding: 2rem 1.5rem;
    background: var(--bg-card);
    border: 1px dashed var(--border);
    border-radius: 10px;
    text-align: center;
}
.empty-icon {
    font-size: clamp(1.6rem, 5vw, 2.2rem);
    margin-bottom: 0.75rem;
}
.empty-title {
    font-family: var(--head);
    font-size: clamp(0.65rem, 2vw, 0.8rem);
    letter-spacing: 0.18em;
    color: var(--text-dim);
    text-transform: uppercase;
}
.empty-sub {
    font-family: var(--mono);
    font-size: 0.62rem;
    color: var(--text-dim);
    opacity: 0.6;
    margin-top: 0.4rem;
    letter-spacing: 0.08em;
}
</style>
""", unsafe_allow_html=True)


# ─── Helper: render flag ─────────────────────────────────────────────────────
def render_flag(flag_text: str) -> str:
    t = flag_text
    if any(k in t for k in ["AI]", "JS-RATIO-AI", "SHIMMER-FLAT", "SHIMMER-CONTROLLED",
                              "PITCHSD-FLAT", "HNR-HIGH+AI", "OVERLAP-AI", "CHAIN-AI",
                              "CHAIN-DETECTED: CHAIN", "CHAIN-DETECTED: DIRECT",
                              "CHAIN-DETECTED: OVERLAP"]):
        # Chain detected line gets its own class
        if "CHAIN-DETECTED" in t:
            if "DIRECT" in t:
                return _flag_html("flag-chain-direct", "🟢", t)
            elif "CHAIN" in t and "OVERLAP" not in t:
                return _flag_html("flag-chain-chain", "🟡", t)
            else:
                return _flag_html("flag-chain-overlap", "🔵", t)
        return _flag_html("flag-ai", "🔴", t)

    elif any(k in t for k in ["Human]", "JS-RATIO-HUMAN", "SHIMMER-HIGH", "SHIMMER-EXTREME",
                                "HNR-NOISY", "PITCHSD-EXTREME", "OVERLAP-HUMAN", "CHAIN-HUMAN",
                                "DIRECT-HUMAN"]):
        return _flag_html("flag-human", "🟢", t)

    elif "WARNING" in t:
        return _flag_html("flag-warn", "⚠", t)

    else:
        return _flag_html("flag-neutral", "◆", t)


def _flag_html(cls: str, icon: str, text: str) -> str:
    return f"""
    <div class="flag-item {cls}">
        <span class="flag-dot">{icon}</span>
        <span>{text}</span>
    </div>"""


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sb-title">⚙ Forensic Context</div>', unsafe_allow_html=True)

    use_case = st.selectbox(
        "Analysis Target",
        ["Voice Note Scam", "Insurance Fraud", "Bank Vishing",
         "Legal Evidence", "KYC Verification", "Deepfake Investigation"],
        label_visibility="visible"
    )

    st.markdown(f'<div class="sb-target">▸ {use_case.upper()}</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="sb-title" style="margin-top:0.5rem">Recording Chain</div>
    <div class="sb-badge"><span class="sb-dot-green">●</span> Direct — Studio / clean mic</div>
    <div class="sb-badge"><span class="sb-dot-yellow">●</span> Chain — WhatsApp / Phone line</div>
    <div class="sb-badge"><span class="sb-dot-blue">●</span> Overlap — Borderline quality</div>
    <div class="sb-info">
        Engine v6.1 · 63-file calibration<br>
        Test accuracy ~95%<br>
        Features: HNR · Shimmer · Jitter<br>
        JS Ratio · PitchSD · Voiced %
    </div>
    """, unsafe_allow_html=True)


# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="vg-header">
    <div class="vg-logo">VOCALGUARD</div>
    <div class="vg-sub">Acoustic Forensics · Voice Authenticity Detection</div>
    <div class="vg-version">ENGINE v6.1</div>
</div>
<div class="vg-divider"></div>
""", unsafe_allow_html=True)


# ─── Upload ───────────────────────────────────────────────────────────────────
st.markdown('<div class="upload-label">▸ Upload Audio Evidence</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader(
    "MP3 · WAV · OGG · OPUS (WhatsApp) · M4A",
    type=["mp3", "wav", "ogg", "opus", "m4a"],
    label_visibility="visible"
)

if uploaded_file is not None:
    # ── Save + convert ───────────────────────────────────────────────
    temp_path = f"temp_upload_{uploaded_file.name}"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    analysis_path = temp_path
    if uploaded_file.name.endswith((".opus", ".m4a")):
        converted_path = temp_path.replace(".opus", ".mp3").replace(".m4a", ".mp3")
        try:
            subprocess.run(["ffmpeg", "-y", "-i", temp_path, converted_path],
                           capture_output=True, check=False)
            analysis_path = converted_path
        except Exception:
            pass

    # ── Scanning animation ────────────────────────────────────────────
    scan_ph = st.empty()
    scan_ph.markdown("""
    <div class="scan-box">
        <div class="scan-text">⬡ Initialising acoustic analysis ⬡</div>
    </div>""", unsafe_allow_html=True)

    with st.spinner(""):
        r = run_forensic_analysis(analysis_path)

    scan_ph.empty()

    if r.get("error"):
        st.markdown(_flag_html("flag-warn", "⚠", f"Analysis Error: {r['error']}"),
                    unsafe_allow_html=True)
    else:
        chain = r.get("chain", "UNKNOWN")

        # ── Chain badge ───────────────────────────────────────────────
        if chain == "DIRECT":
            st.markdown("""
            <div class="chain-badge chain-direct anim-1">
                <div class="chain-dot" style="background:var(--green)"></div>
                Direct audio — High quality · Studio / Headset mic
            </div>""", unsafe_allow_html=True)
        elif chain == "CHAIN":
            st.markdown("""
            <div class="chain-badge chain-chain anim-1">
                <div class="chain-dot" style="background:var(--yellow)"></div>
                Chain audio — Compressed · WhatsApp / Phone line
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="chain-badge chain-overlap anim-1">
                <div class="chain-dot" style="background:var(--cyan)"></div>
                Overlap zone — Borderline quality · Dual-mode analysis applied
            </div>""", unsafe_allow_html=True)

        # ── Verdict card ──────────────────────────────────────────────
        verdict  = r["verdict"]
        ai_conf  = r["ai_confidence"]
        hum_conf = r["human_confidence"]

        if verdict == "AI_GENERATED":
            v_cls, v_lcls = "verdict-ai", "verdict-label-ai"
            v_icon   = "🤖"
            v_label  = "Synthetic Voice Detected"
            v_sub    = "Acoustic markers indicate AI generation"
            v_warn   = "⚠️ High probability of synthesized or cloned voice. Do not authorise financial transactions or identity actions."
        elif verdict == "HUMAN":
            v_cls, v_lcls = "verdict-human", "verdict-label-human"
            v_icon   = "👤"
            v_label  = "Authentic Human Voice"
            v_sub    = "Acoustic markers align with natural vocal dynamics"
            v_warn   = "✅ Vocal patterns consistent with live human speech. Standard verification protocols apply."
        else:
            v_cls, v_lcls = "verdict-uncertain", "verdict-label-uncertain"
            v_icon   = "⚠"
            v_label  = "Inconclusive Result"
            v_sub    = "Mixed acoustic signals — further review required"
            v_warn   = "🔍 Edge case detected. Manual forensic review or re-recording in controlled conditions recommended."

        st.markdown(f"""
        <div class="verdict-card {v_cls} anim-2">
            <span class="verdict-icon">{v_icon}</span>
            <div class="verdict-label {v_lcls}">{v_label}</div>
            <div class="verdict-sub">{v_sub}</div>
            <div style="margin:0.9rem 0 0.75rem">
                <div class="conf-row">
                    <span class="conf-label" style="color:var(--red)">AI</span>
                    <div class="conf-bar-outer">
                        <div class="conf-bar-inner conf-bar-ai" style="width:{ai_conf}%"></div>
                    </div>
                    <span class="conf-pct conf-pct-ai">{ai_conf}%</span>
                </div>
                <div class="conf-row">
                    <span class="conf-label" style="color:var(--green)">Human</span>
                    <div class="conf-bar-outer">
                        <div class="conf-bar-inner conf-bar-human" style="width:{hum_conf}%"></div>
                    </div>
                    <span class="conf-pct conf-pct-human">{hum_conf}%</span>
                </div>
            </div>
            <div class="verdict-warning">{v_warn}</div>
        </div>
        """, unsafe_allow_html=True)

        # ── Acoustic Metrics ──────────────────────────────────────────
        if "metrics" in r:
            m = r["metrics"]
            st.markdown('<div class="section-head">Acoustic Metrics</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="metric-grid anim-3">
                <div class="metric-card">
                    <div class="metric-key">HNR</div>
                    <div class="metric-val">{m['hnr_db']}</div>
                    <div class="metric-desc">dB · chain detector</div>
                </div>
                <div class="metric-card">
                    <div class="metric-key">Shimmer</div>
                    <div class="metric-val">{m['shimmer_pct']}</div>
                    <div class="metric-desc">% amplitude var</div>
                </div>
                <div class="metric-card">
                    <div class="metric-key">Jitter</div>
                    <div class="metric-val">{m['jitter_pct']}</div>
                    <div class="metric-desc">% freq variation</div>
                </div>
                <div class="metric-card">
                    <div class="metric-key">JS Ratio</div>
                    <div class="metric-val">{m['js_ratio']}</div>
                    <div class="metric-desc">jitter / shimmer</div>
                </div>
            </div>
            <div class="metric-grid anim-3">
                <div class="metric-card">
                    <div class="metric-key">Pitch SD</div>
                    <div class="metric-val">{m['pitch_sd_hz']}</div>
                    <div class="metric-desc">Hz std deviation</div>
                </div>
                <div class="metric-card">
                    <div class="metric-key">Pitch</div>
                    <div class="metric-val">{m['pitch_hz']}</div>
                    <div class="metric-desc">Hz mean F0</div>
                </div>
                <div class="metric-card">
                    <div class="metric-key">Voiced</div>
                    <div class="metric-val">{round(m['voiced_fraction']*100)}%</div>
                    <div class="metric-desc">voiced frames</div>
                </div>
                <div class="metric-card">
                    <div class="metric-key">Duration</div>
                    <div class="metric-val">{m['duration_sec']}s</div>
                    <div class="metric-desc">analysed length</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Closest Profile ────────────────────────────────────────────
        st.markdown('<div class="section-head">Closest Acoustic Profile</div>',
                    unsafe_allow_html=True)
        st.markdown(f"""
        <div class="profile-card anim-3">
            <span class="profile-name">⬡ {r['closest_profile']}</span>
            <span class="profile-dist">dist: {r['profile_distance']}</span>
        </div>
        """, unsafe_allow_html=True)

        # ── Signal Flags ───────────────────────────────────────────────
        st.markdown('<div class="section-head anim-4">Signal Analysis Flags</div>',
                    unsafe_allow_html=True)
        if "flags" in r and r["flags"]:
            flags_html = "".join(render_flag(f) for f in r["flags"])
            st.markdown(f'<div class="anim-4">{flags_html}</div>', unsafe_allow_html=True)

    # ── Cleanup ────────────────────────────────────────────────────────
    for path in {temp_path, analysis_path}:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

else:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">📡</div>
        <div class="empty-title">Awaiting Audio Evidence</div>
        <div class="empty-sub">MP3 · WAV · OGG · OPUS · M4A</div>
    </div>
    """, unsafe_allow_html=True)
