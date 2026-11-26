import streamlit as st
import os
import subprocess
from engine import run_forensic_analysis

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="VocalGuard · Voice Forensics",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ─── Global CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;500;600;700&family=Orbitron:wght@400;700;900&display=swap');

/* ── Root vars ── */
:root {
    --bg-primary:   #060a10;
    --bg-card:      #0b1120;
    --bg-card2:     #0e1628;
    --border:       #1a2d4a;
    --border-glow:  #00e5ff;
    --cyan:         #00e5ff;
    --cyan-dim:     #00bcd4;
    --green:        #00ff9d;
    --red:          #ff3b5c;
    --yellow:       #ffd600;
    --text:         #c8d8e8;
    --text-dim:     #5a7a9a;
    --mono:         'Share Tech Mono', monospace;
    --head:         'Orbitron', monospace;
    --body:         'Rajdhani', sans-serif;
}

/* ── Global reset ── */
html, body, [data-testid="stAppViewContainer"],
[data-testid="stApp"] {
    background: var(--bg-primary) !important;
    color: var(--text) !important;
    font-family: var(--body) !important;
}

/* Scanline overlay */
[data-testid="stApp"]::before {
    content: '';
    position: fixed;
    inset: 0;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(0,229,255,0.012) 2px,
        rgba(0,229,255,0.012) 4px
    );
    pointer-events: none;
    z-index: 9999;
}

/* ── Sidebar — always visible, no collapse ── */
[data-testid="stSidebar"] {
    background: #060d1a !important;
    border-right: 1px solid var(--border) !important;
    min-width: 240px !important;
    max-width: 240px !important;
    transform: none !important;
    visibility: visible !important;
}
/* Hide the collapse/expand arrow button completely */
[data-testid="stSidebarCollapseButton"],
button[kind="header"],
.st-emotion-cache-1rtdyuf,
.st-emotion-cache-zt5igj,
[data-testid="collapsedControl"] {
    display: none !important;
    visibility: hidden !important;
}
[data-testid="stSidebar"] * { font-family: var(--body) !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] li { color: var(--text) !important; }

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Main container ── */
.block-container {
    max-width: 820px !important;
    padding: 2rem 2rem 4rem !important;
}

/* ── Header block ── */
.vg-header {
    text-align: center;
    padding: 2.5rem 0 1.5rem;
    position: relative;
}
.vg-logo {
    font-family: var(--head);
    font-size: 2.2rem;
    font-weight: 900;
    letter-spacing: 0.15em;
    background: linear-gradient(135deg, var(--cyan) 0%, #7b61ff 60%, var(--cyan-dim) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    text-shadow: none;
}
.vg-sub {
    font-family: var(--mono);
    font-size: 0.7rem;
    color: var(--text-dim);
    letter-spacing: 0.3em;
    text-transform: uppercase;
    margin-top: 0.3rem;
}
.vg-version {
    display: inline-block;
    font-family: var(--mono);
    font-size: 0.6rem;
    color: var(--cyan-dim);
    border: 1px solid var(--cyan-dim);
    border-radius: 2px;
    padding: 1px 8px;
    letter-spacing: 0.15em;
    margin-top: 0.6rem;
}
.vg-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--cyan), transparent);
    margin: 1.5rem 0;
    opacity: 0.4;
}

/* ── Upload zone ── */
.upload-label {
    font-family: var(--mono);
    font-size: 0.72rem;
    color: var(--cyan-dim);
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
}
[data-testid="stFileUploaderDropzone"] {
    background: var(--bg-card) !important;
    border: 1px dashed var(--border-glow) !important;
    border-radius: 6px !important;
    transition: all 0.3s !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
    background: #0d1830 !important;
    border-color: var(--cyan) !important;
    box-shadow: 0 0 20px rgba(0,229,255,0.08) !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] p {
    color: var(--text-dim) !important;
    font-family: var(--mono) !important;
    font-size: 0.75rem !important;
}

/* ── Scanning animation ── */
@keyframes scanPulse {
    0%   { opacity: 1; }
    50%  { opacity: 0.4; }
    100% { opacity: 1; }
}
@keyframes scanLine {
    0%   { transform: translateY(-100%); }
    100% { transform: translateY(400px); }
}
.scan-box {
    background: var(--bg-card);
    border: 1px solid var(--cyan);
    border-radius: 6px;
    padding: 1.5rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 0 30px rgba(0,229,255,0.1), inset 0 0 30px rgba(0,229,255,0.03);
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
    font-size: 0.75rem;
    color: var(--cyan);
    letter-spacing: 0.25em;
    text-transform: uppercase;
    animation: scanPulse 1.2s ease-in-out infinite;
}

/* ── Chain badge ── */
.chain-badge {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.7rem 1.1rem;
    border-radius: 4px;
    font-family: var(--mono);
    font-size: 0.72rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 1.5rem;
    border-left: 3px solid;
}
.chain-direct {
    background: rgba(0,255,157,0.07);
    border-color: var(--green);
    color: var(--green);
}
.chain-chain {
    background: rgba(255,214,0,0.07);
    border-color: var(--yellow);
    color: var(--yellow);
}
.chain-overlap {
    background: rgba(0,229,255,0.07);
    border-color: var(--cyan);
    color: var(--cyan);
}
.chain-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    flex-shrink: 0;
    animation: scanPulse 1.5s ease-in-out infinite;
}

/* ── Verdict card ── */
.verdict-card {
    border-radius: 8px;
    padding: 1.8rem 2rem;
    position: relative;
    overflow: hidden;
    margin-bottom: 1.5rem;
}
.verdict-ai {
    background: linear-gradient(135deg, rgba(255,59,92,0.12) 0%, rgba(255,59,92,0.04) 100%);
    border: 1px solid rgba(255,59,92,0.5);
    box-shadow: 0 0 40px rgba(255,59,92,0.08);
}
.verdict-human {
    background: linear-gradient(135deg, rgba(0,255,157,0.1) 0%, rgba(0,255,157,0.03) 100%);
    border: 1px solid rgba(0,255,157,0.4);
    box-shadow: 0 0 40px rgba(0,255,157,0.07);
}
.verdict-uncertain {
    background: linear-gradient(135deg, rgba(255,214,0,0.1) 0%, rgba(255,214,0,0.03) 100%);
    border: 1px solid rgba(255,214,0,0.4);
    box-shadow: 0 0 40px rgba(255,214,0,0.07);
}
.verdict-icon {
    font-size: 2.2rem;
    margin-bottom: 0.5rem;
    display: block;
}
.verdict-label {
    font-family: var(--head);
    font-size: 1.4rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    margin-bottom: 0.4rem;
}
.verdict-label-ai      { color: var(--red); }
.verdict-label-human   { color: var(--green); }
.verdict-label-uncertain { color: var(--yellow); }
.verdict-sub {
    font-family: var(--mono);
    font-size: 0.68rem;
    color: var(--text-dim);
    letter-spacing: 0.12em;
    margin-bottom: 1.2rem;
}
.verdict-warning {
    font-family: var(--body);
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--text);
    background: rgba(0,0,0,0.3);
    border-radius: 4px;
    padding: 0.6rem 0.9rem;
    letter-spacing: 0.04em;
}

/* ── Confidence bars ── */
.conf-row {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin-bottom: 0.5rem;
}
.conf-label {
    font-family: var(--mono);
    font-size: 0.65rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    width: 55px;
    flex-shrink: 0;
}
.conf-bar-outer {
    flex: 1;
    height: 6px;
    background: rgba(255,255,255,0.06);
    border-radius: 3px;
    overflow: hidden;
}
.conf-bar-inner {
    height: 100%;
    border-radius: 3px;
    transition: width 0.8s ease;
}
.conf-bar-ai    { background: linear-gradient(90deg, #ff3b5c, #ff6b85); }
.conf-bar-human { background: linear-gradient(90deg, #00ff9d, #00e5ff); }
.conf-pct {
    font-family: var(--mono);
    font-size: 0.75rem;
    width: 42px;
    text-align: right;
    flex-shrink: 0;
}
.conf-pct-ai    { color: var(--red); }
.conf-pct-human { color: var(--green); }

/* ── Section heading ── */
.section-head {
    font-family: var(--mono);
    font-size: 0.65rem;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    color: var(--text-dim);
    margin: 1.8rem 0 0.8rem;
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

/* ── Metric grid ── */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.6rem;
    margin-bottom: 0.6rem;
}
.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.75rem 0.7rem;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.metric-card:hover {
    border-color: var(--cyan);
    box-shadow: 0 0 12px rgba(0,229,255,0.06);
}
.metric-key {
    font-family: var(--mono);
    font-size: 0.55rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--text-dim);
    margin-bottom: 0.3rem;
}
.metric-val {
    font-family: var(--mono);
    font-size: 1.1rem;
    font-weight: 400;
    color: var(--cyan);
    line-height: 1;
}
.metric-desc {
    font-family: var(--mono);
    font-size: 0.48rem;
    letter-spacing: 0.1em;
    color: #3a5070;
    margin-top: 0.2rem;
    text-transform: uppercase;
}

/* ── Profile match card ── */
.profile-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-left: 3px solid var(--cyan);
    border-radius: 4px;
    padding: 0.7rem 1rem;
    font-family: var(--mono);
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.75rem;
}
.profile-name { color: var(--cyan); letter-spacing: 0.05em; }
.profile-dist { color: var(--text-dim); font-size: 0.65rem; }

/* ── Flag list ── */
.flag-item {
    display: flex;
    align-items: flex-start;
    gap: 0.7rem;
    padding: 0.55rem 0.8rem;
    margin-bottom: 0.3rem;
    border-radius: 4px;
    font-family: var(--mono);
    font-size: 0.68rem;
    letter-spacing: 0.04em;
    line-height: 1.5;
    border-left: 2px solid;
}
.flag-ai {
    background: rgba(255,59,92,0.06);
    border-color: var(--red);
    color: #ff8a9e;
}
.flag-human {
    background: rgba(0,255,157,0.05);
    border-color: var(--green);
    color: #66ffcc;
}
.flag-chain-direct {
    background: rgba(0,255,157,0.04);
    border-color: var(--green);
    color: var(--green);
}
.flag-chain-chain {
    background: rgba(255,214,0,0.05);
    border-color: var(--yellow);
    color: var(--yellow);
}
.flag-chain-overlap {
    background: rgba(0,229,255,0.05);
    border-color: var(--cyan);
    color: var(--cyan);
}
.flag-warn {
    background: rgba(255,214,0,0.05);
    border-color: var(--yellow);
    color: var(--yellow);
}
.flag-neutral {
    background: rgba(255,255,255,0.03);
    border-color: var(--border);
    color: var(--text-dim);
}
.flag-dot { flex-shrink: 0; margin-top: 2px; }

/* ── Override Streamlit widget styles ── */
.stFileUploader label { color: var(--text) !important; font-family: var(--body) !important; }
.stSelectbox label    { color: var(--text) !important; font-family: var(--body) !important; font-size: 0.85rem !important; }
.stSelectbox > div > div {
    background: var(--bg-card2) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
    font-family: var(--mono) !important;
    font-size: 0.8rem !important;
}
div[data-baseweb="select"] * {
    background: var(--bg-card2) !important;
    color: var(--text) !important;
    font-family: var(--mono) !important;
}
.stAlert { border-radius: 4px !important; }
div[data-testid="stMarkdownContainer"] p { font-family: var(--body) !important; }

/* ── Spinner override ── */
.stSpinner > div { border-top-color: var(--cyan) !important; }

/* ── Sidebar styles ── */
.sb-title {
    font-family: var(--head);
    font-size: 0.75rem;
    letter-spacing: 0.2em;
    color: var(--cyan-dim);
    text-transform: uppercase;
    margin-bottom: 0.8rem;
}
.sb-badge {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.5rem 0.7rem;
    background: rgba(0,229,255,0.04);
    border: 1px solid var(--border);
    border-radius: 4px;
    margin-bottom: 0.4rem;
    font-family: var(--mono);
    font-size: 0.65rem;
    color: var(--text-dim);
    letter-spacing: 0.08em;
}
.sb-dot-green  { color: var(--green); }
.sb-dot-yellow { color: var(--yellow); }
.sb-dot-blue   { color: var(--cyan); }
.sb-info {
    font-family: var(--mono);
    font-size: 0.65rem;
    color: var(--text-dim);
    letter-spacing: 0.06em;
    line-height: 1.6;
    padding: 0.6rem 0;
    border-top: 1px solid var(--border);
    margin-top: 0.8rem;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

/* ── Stagger animation ── */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}
.anim-1 { animation: fadeUp 0.4s ease forwards; }
.anim-2 { animation: fadeUp 0.4s 0.1s ease forwards; opacity: 0; }
.anim-3 { animation: fadeUp 0.4s 0.2s ease forwards; opacity: 0; }
.anim-4 { animation: fadeUp 0.4s 0.3s ease forwards; opacity: 0; }

</style>
""", unsafe_allow_html=True)


# ─── Helper: render flag item ────────────────────────────────────────────────
def render_flag(flag_text):
    t = flag_text
    if any(k in t for k in ["AI]", "JS-RATIO-AI", "SHIMMER-FLAT", "SHIMMER-CONTROLLED",
                              "PITCHSD-FLAT", "HNR-HIGH+AI", "OVERLAP-AI", "CHAIN-AI"]):
        cls, icon = "flag-ai", "🔴"
    elif any(k in t for k in ["Human]", "JS-RATIO-HUMAN", "SHIMMER-HIGH", "SHIMMER-EXTREME",
                                "HNR-NOISY", "PITCHSD-EXTREME", "OVERLAP-HUMAN", "CHAIN-HUMAN"]):
        cls, icon = "flag-human", "🟢"
    elif "CHAIN-DETECTED" in t:
        if "DIRECT" in t:
            cls, icon = "flag-chain-direct", "🟢"
        elif "CHAIN" in t:
            cls, icon = "flag-chain-chain", "🟡"
        else:
            cls, icon = "flag-chain-overlap", "🔵"
    elif "WARNING" in t:
        cls, icon = "flag-warn", "⚠"
    else:
        cls, icon = "flag-neutral", "◆"

    return f"""
    <div class="flag-item {cls}">
        <span class="flag-dot">{icon}</span>
        <span>{t}</span>
    </div>"""


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sb-title">⚙ Forensic Context</div>', unsafe_allow_html=True)

    use_case = st.selectbox(
        "Analysis Target",
        ["Voice Note Scam", "Insurance Fraud", "Bank Vishing", "Legal Evidence",
         "KYC Verification", "Deepfake Investigation"],
        label_visibility="visible"
    )

    st.markdown(f"""
    <div style="font-family:'Share Tech Mono',monospace;font-size:0.65rem;
                color:#00e5ff;letter-spacing:0.1em;padding:0.5rem 0 0.8rem;">
        TARGET → {use_case.upper()}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="sb-title" style="margin-top:0.5rem">Chain Modes</div>
    <div class="sb-badge"><span class="sb-dot-green">●</span> DIRECT — Studio / clean mic</div>
    <div class="sb-badge"><span class="sb-dot-yellow">●</span> CHAIN — WhatsApp / Phone</div>
    <div class="sb-badge"><span class="sb-dot-blue">●</span> OVERLAP — Borderline quality</div>
    <div class="sb-info">
        Engine v6.1 · 63-file calibration<br>
        Accuracy ~95% on test set<br>
        Features: HNR · Shimmer · Jitter<br>
        JS Ratio · PitchSD · Voiced%
    </div>
    """, unsafe_allow_html=True)


# ─── Header ──────────────────────────────────────────────────────────────────
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
    # ── Save + convert ──────────────────────────────────────────────
    temp_path = f"temp_upload_{uploaded_file.name}"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    analysis_path = temp_path
    if uploaded_file.name.endswith((".opus", ".m4a")):
        converted_path = temp_path.replace(".opus", ".mp3").replace(".m4a", ".mp3")
        try:
            subprocess.run(["ffmpeg", "-y", "-i", temp_path, converted_path],
                           capture_output=True)
            analysis_path = converted_path
        except Exception:
            pass

    # ── Scanning animation ───────────────────────────────────────────
    scan_ph = st.empty()
    scan_ph.markdown("""
    <div class="scan-box">
        <div class="scan-text">⬡ Initializing acoustic analysis ⬡</div>
    </div>""", unsafe_allow_html=True)

    with st.spinner(""):
        r = run_forensic_analysis(analysis_path)

    scan_ph.empty()

    if r.get("error"):
        st.markdown(f"""
        <div class="flag-item flag-warn">
            <span>⚠</span>
            <span>Analysis Error: {r['error']}</span>
        </div>""", unsafe_allow_html=True)
    else:
        chain = r.get("chain", "UNKNOWN")

        # ── Chain badge ──────────────────────────────────────────────
        if chain == "DIRECT":
            st.markdown("""
            <div class="chain-badge chain-direct anim-1">
                <div class="chain-dot" style="background:#00ff9d"></div>
                DIRECT AUDIO — High quality recording · Studio / Headset mic
            </div>""", unsafe_allow_html=True)
        elif chain == "CHAIN":
            st.markdown("""
            <div class="chain-badge chain-chain anim-1">
                <div class="chain-dot" style="background:#ffd600"></div>
                CHAIN AUDIO — Compressed recording · WhatsApp / Phone line detected
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="chain-badge chain-overlap anim-1">
                <div class="chain-dot" style="background:#00e5ff"></div>
                OVERLAP ZONE — Borderline audio quality · Dual-mode analysis applied
            </div>""", unsafe_allow_html=True)

        # ── Verdict card ─────────────────────────────────────────────
        verdict  = r["verdict"]
        ai_conf  = r["ai_confidence"]
        hum_conf = r["human_confidence"]

        if verdict == "AI_GENERATED":
            v_cls   = "verdict-ai"
            v_lcls  = "verdict-label-ai"
            v_icon  = "🤖"
            v_label = "SYNTHETIC VOICE DETECTED"
            v_sub   = "Acoustic markers indicate AI generation"
            v_warn  = "⚠️ High probability of synthesized / cloned voice. Do not authorize financial transactions or identity actions."
        elif verdict == "HUMAN":
            v_cls   = "verdict-human"
            v_lcls  = "verdict-label-human"
            v_icon  = "👤"
            v_label = "AUTHENTIC HUMAN VOICE"
            v_sub   = "Acoustic markers align with natural vocal dynamics"
            v_warn  = "✅ Vocal patterns consistent with live human speech. Standard verification protocols apply."
        else:
            v_cls   = "verdict-uncertain"
            v_lcls  = "verdict-label-uncertain"
            v_icon  = "⚠"
            v_label = "INCONCLUSIVE RESULT"
            v_sub   = "Mixed acoustic signals — further review required"
            v_warn  = "🔍 Edge-case detected. Manual forensic review or re-recording in controlled conditions recommended."

        st.markdown(f"""
        <div class="verdict-card {v_cls} anim-2">
            <span class="verdict-icon">{v_icon}</span>
            <div class="verdict-label {v_lcls}">{v_label}</div>
            <div class="verdict-sub">{v_sub}</div>
            <div style="margin:1rem 0 0.8rem">
                <div class="conf-row">
                    <span class="conf-label" style="color:#ff8a9e">AI</span>
                    <div class="conf-bar-outer">
                        <div class="conf-bar-inner conf-bar-ai" style="width:{ai_conf}%"></div>
                    </div>
                    <span class="conf-pct conf-pct-ai">{ai_conf}%</span>
                </div>
                <div class="conf-row">
                    <span class="conf-label" style="color:#66ffcc">Human</span>
                    <div class="conf-bar-outer">
                        <div class="conf-bar-inner conf-bar-human" style="width:{hum_conf}%"></div>
                    </div>
                    <span class="conf-pct conf-pct-human">{hum_conf}%</span>
                </div>
            </div>
            <div class="verdict-warning">{v_warn}</div>
        </div>
        """, unsafe_allow_html=True)

        # ── Acoustic Metrics ─────────────────────────────────────────
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
                    <div class="metric-desc">analyzed length</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Closest Profile ───────────────────────────────────────────
        st.markdown('<div class="section-head">Closest Acoustic Profile</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="profile-card anim-3">
            <span class="profile-name">⬡ {r['closest_profile']}</span>
            <span class="profile-dist">dist: {r['profile_distance']}</span>
        </div>
        """, unsafe_allow_html=True)

        # ── Signal Flags ──────────────────────────────────────────────
        st.markdown('<div class="section-head anim-4">Signal Analysis Flags</div>', unsafe_allow_html=True)
        if "flags" in r and r["flags"]:
            flags_html = "".join(render_flag(f) for f in r["flags"])
            st.markdown(f'<div class="anim-4">{flags_html}</div>', unsafe_allow_html=True)

    # ── Cleanup ───────────────────────────────────────────────────────
    for path in [temp_path, analysis_path]:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

else:
    st.markdown("""
    <div style="
        margin-top: 1.5rem;
        padding: 2rem;
        background: var(--bg-card);
        border: 1px dashed rgba(26,45,74,0.8);
        border-radius: 8px;
        text-align: center;
    ">
        <div style="font-size:2rem;margin-bottom:0.8rem">📡</div>
        <div style="font-family:'Orbitron',monospace;font-size:0.8rem;
                    letter-spacing:0.2em;color:#1a4060;text-transform:uppercase">
            Awaiting Audio Evidence
        </div>
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.65rem;
                    color:#1a3050;margin-top:0.5rem;letter-spacing:0.1em">
            MP3 · WAV · OGG · OPUS · M4A
        </div>
    </div>
    """, unsafe_allow_html=True)