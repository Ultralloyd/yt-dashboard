import streamlit as st
import pandas as pd
import plotly.express as px
from googleapiclient.discovery import build
import anthropic
import requests
from datetime import datetime
import json
import re
import isodate
from collections import Counter
from pytrends.request import TrendReq
import time

# ─────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Channel Intelligence System",
    page_icon="📺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────
# STYLING — TACTICAL SITUATION ROOM
# ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=Share+Tech+Mono&family=Rajdhani:wght@400;500;600&display=swap');

:root {
  --bg-deep:    #020c0e;
  --bg-panel:   #050f12;
  --bg-raised:  #081418;
  --cyan:       #00d4b4;
  --cyan-dim:   #007a68;
  --cyan-glow:  rgba(0,212,180,0.15);
  --red:        #ff3a2d;
  --red-dim:    #6b1510;
  --amber:      #f59e0b;
  --purple:     #a855f7;
  --purple-dim: #581c87;
  --pink:       #ec4899;
  --pink-dim:   #831843;
  --text-pri:   #c8f0ea;
  --text-sec:   #5a8a82;
  --text-dim:   #2a5550;
  --border:     #0d3530;
  --border-hot: #00d4b4;
  --grid:       rgba(0,180,160,0.04);
}

/* Global reset */
html, body, [class*="css"] {
    font-family: 'Share Tech Mono', monospace !important;
    background-color: var(--bg-deep) !important;
    color: var(--text-pri) !important;
}

/* Scanline + grid texture on body */
body::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image:
        repeating-linear-gradient(0deg, transparent, transparent 2px, var(--grid) 2px, var(--grid) 4px),
        repeating-linear-gradient(90deg, transparent, transparent 40px, var(--grid) 40px, var(--grid) 41px);
    pointer-events: none;
    z-index: 0;
}

h1, h2, h3, h4 { font-family: 'Orbitron', monospace !important; color: var(--cyan) !important; letter-spacing: 0.1em; }
h3 { font-size: 0.95rem !important; }

.block-container { padding: 1.5rem 2.5rem; max-width: 1500px; position: relative; z-index: 1; }

/* ── SIDEBAR ─────────────────────── */
section[data-testid="stSidebar"] {
    background: var(--bg-panel) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image: repeating-linear-gradient(0deg,transparent,transparent 3px,var(--grid) 3px,var(--grid) 4px);
    pointer-events: none;
}
section[data-testid="stSidebar"] label {
    font-family: 'Orbitron', monospace !important;
    font-size: 0.65rem !important;
    color: var(--text-sec) !important;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

/* ── METRIC CARDS ────────────────── */
div[data-testid="metric-container"] {
    background: var(--bg-raised) !important;
    border: 1px solid var(--border) !important;
    border-radius: 0 !important;
    padding: 0.7rem 0.8rem !important;
    position: relative;
    overflow: hidden;
    clip-path: polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 10px 100%, 0 calc(100% - 10px));
}
div[data-testid="metric-container"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, var(--cyan) 0%, transparent 100%);
}
div[data-testid="metric-container"] label {
    font-family: 'Orbitron', monospace !important;
    font-size: 0.55rem !important;
    color: var(--text-sec) !important;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'Share Tech Mono', monospace !important;
    color: var(--cyan) !important;
    font-size: 1.05rem !important;
    text-shadow: 0 0 10px var(--cyan);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    letter-spacing: -0.01em;
}
div[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.65rem !important;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* ── TABS ─────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-panel) !important;
    border-radius: 0 !important;
    padding: 2px !important;
    gap: 2px !important;
    border: 1px solid var(--border) !important;
    border-bottom: 2px solid var(--cyan-dim) !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 0 !important;
    color: var(--text-sec) !important;
    font-family: 'Orbitron', monospace !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.1em;
    padding: 8px 16px !important;
    text-transform: uppercase;
    transition: all 0.15s;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--cyan) !important; }
.stTabs [aria-selected="true"] {
    background: var(--bg-raised) !important;
    color: var(--cyan) !important;
    border-bottom: 2px solid var(--cyan) !important;
    text-shadow: 0 0 8px var(--cyan);
}

/* ── BUTTONS ─────────────────────── */
.stButton > button {
    background: transparent !important;
    color: var(--cyan) !important;
    border: 1px solid var(--cyan) !important;
    border-radius: 0 !important;
    font-family: 'Orbitron', monospace !important;
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    padding: 0.6rem 1.8rem !important;
    clip-path: polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 8px 100%, 0 calc(100% - 8px));
    transition: all 0.2s !important;
    box-shadow: inset 0 0 20px rgba(0,212,180,0.05), 0 0 10px rgba(0,212,180,0.1) !important;
}
.stButton > button:hover {
    background: var(--cyan-glow) !important;
    box-shadow: 0 0 20px rgba(0,212,180,0.3), inset 0 0 20px rgba(0,212,180,0.1) !important;
    text-shadow: 0 0 8px var(--cyan) !important;
}

/* ── ALERT BOXES ─────────────────── */
div[data-testid="stSuccess"] {
    background: rgba(0,80,60,0.2) !important;
    border: 1px solid #006644 !important;
    border-left: 3px solid #00d4b4 !important;
    border-radius: 0 !important;
    font-family: 'Share Tech Mono', monospace !important;
    color: var(--text-pri) !important;
}
div[data-testid="stWarning"] {
    background: rgba(80,50,0,0.2) !important;
    border: 1px solid #664400 !important;
    border-left: 3px solid var(--amber) !important;
    border-radius: 0 !important;
    font-family: 'Share Tech Mono', monospace !important;
}
div[data-testid="stInfo"] {
    background: rgba(0,50,60,0.3) !important;
    border: 1px solid var(--border) !important;
    border-left: 3px solid var(--cyan-dim) !important;
    border-radius: 0 !important;
    font-family: 'Share Tech Mono', monospace !important;
    color: var(--text-pri) !important;
}
div[data-testid="stError"] {
    background: rgba(80,10,5,0.3) !important;
    border: 1px solid var(--red-dim) !important;
    border-left: 3px solid var(--red) !important;
    border-radius: 0 !important;
    font-family: 'Share Tech Mono', monospace !important;
}

/* ── EXPANDERS ───────────────────── */
details {
    background: var(--bg-panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: 0 !important;
}
details summary {
    font-family: 'Orbitron', monospace !important;
    font-size: 0.7rem !important;
    color: var(--cyan-dim) !important;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

/* ── TEXT INPUTS ─────────────────── */
.stTextInput input, .stSelectbox select {
    background: var(--bg-raised) !important;
    border: 1px solid var(--border) !important;
    border-radius: 0 !important;
    color: var(--cyan) !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.85rem !important;
}
.stTextInput input:focus {
    border-color: var(--cyan) !important;
    box-shadow: 0 0 8px var(--cyan-glow) !important;
}

/* ── SLIDER ──────────────────────── */
.stSlider [data-baseweb="slider"] { }
.stSlider [data-baseweb="thumb"] { background: var(--cyan) !important; }

/* ── DATAFRAMES ──────────────────── */
.stDataFrame { border: 1px solid var(--border) !important; }
.stDataFrame table { background: var(--bg-panel) !important; font-family: 'Share Tech Mono', monospace !important; font-size: 0.8rem !important; }
.stDataFrame th { background: var(--bg-raised) !important; color: var(--cyan) !important; font-family: 'Orbitron', monospace !important; font-size: 0.62rem !important; letter-spacing: 0.1em; border-color: var(--border) !important; }
.stDataFrame td { color: var(--text-pri) !important; border-color: var(--border) !important; }

/* ── SCROLLBAR ───────────────────── */
::-webkit-scrollbar { width: 4px; background: var(--bg-deep); }
::-webkit-scrollbar-thumb { background: var(--cyan-dim); }

hr { border-color: var(--border) !important; border-style: dashed !important; }

/* ── CUSTOM COMPONENTS ───────────── */

/* Channel header panel */
.ch-header {
    background: transparent;
    border: none;
    border-top: 2px solid var(--cyan);
    border-bottom: 1px solid var(--border);
    padding: 1rem 0;
    margin-bottom: 1.2rem;
    position: relative;
}
.ch-header::after {
    content: attr(data-label);
    position: absolute;
    top: -1px; right: 0;
    background: var(--cyan);
    color: var(--bg-deep);
    font-family: 'Orbitron', monospace;
    font-size: 0.5rem;
    font-weight: 700;
    letter-spacing: 0.2em;
    padding: 2px 8px;
    text-transform: uppercase;
}
.ch-name {
    font-family: 'Orbitron', monospace;
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--cyan);
    letter-spacing: 0.08em;
    text-shadow: 0 0 16px rgba(0,212,180,0.4);
}
.ch-sub {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.75rem;
    color: var(--text-sec);
    margin-top: 6px;
    letter-spacing: 0.05em;
}

/* Data pill tags */
.pill {
    display: inline-block;
    background: var(--bg-deep);
    border: 1px solid var(--cyan-dim);
    padding: 3px 10px;
    font-size: 0.72rem;
    color: var(--cyan);
    margin: 2px;
    font-family: 'Share Tech Mono', monospace;
    clip-path: polygon(6px 0%, 100% 0%, calc(100% - 6px) 100%, 0% 100%);
    letter-spacing: 0.05em;
}
.pill-purple {
    display: inline-block;
    background: var(--bg-deep);
    border: 1px solid var(--purple-dim);
    padding: 3px 10px;
    font-size: 0.72rem;
    color: var(--purple);
    margin: 2px;
    font-family: 'Share Tech Mono', monospace;
    clip-path: polygon(6px 0%, 100% 0%, calc(100% - 6px) 100%, 0% 100%);
    letter-spacing: 0.05em;
}
.pill-pink {
    display: inline-block;
    background: var(--bg-deep);
    border: 1px solid var(--pink-dim);
    padding: 3px 10px;
    font-size: 0.72rem;
    color: var(--pink);
    margin: 2px;
    font-family: 'Share Tech Mono', monospace;
    clip-path: polygon(6px 0%, 100% 0%, calc(100% - 6px) 100%, 0% 100%);
    letter-spacing: 0.05em;
}
.pill-amber {
    display: inline-block;
    background: var(--bg-deep);
    border: 1px solid rgba(245,158,11,0.3);
    padding: 3px 10px;
    font-size: 0.72rem;
    color: var(--amber);
    margin: 2px;
    font-family: 'Share Tech Mono', monospace;
    clip-path: polygon(6px 0%, 100% 0%, calc(100% - 6px) 100%, 0% 100%);
    letter-spacing: 0.05em;
}
.pill-red {
    display: inline-block;
    background: var(--bg-deep);
    border: 1px solid var(--red-dim);
    padding: 3px 10px;
    font-size: 0.72rem;
    color: var(--red);
    margin: 2px;
    font-family: 'Share Tech Mono', monospace;
    clip-path: polygon(6px 0%, 100% 0%, calc(100% - 6px) 100%, 0% 100%);
    letter-spacing: 0.05em;
}

/* API source badges */
.api-badge {
    display: inline-block;
    padding: 2px 8px;
    font-size: 0.6rem;
    font-family: 'Orbitron', monospace;
    margin-left: 6px;
    vertical-align: middle;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
.badge-claude {
    background: transparent;
    color: var(--cyan);
    border: 1px solid var(--cyan-dim);
}
.badge-dataforseo {
    background: transparent;
    color: #4ade80;
    border: 1px solid #166534;
}
.badge-yt {
    background: transparent;
    color: var(--red);
    border: 1px solid var(--red-dim);
}
.badge-reddit {
    background: transparent;
    color: #ff4500;
    border: 1px solid #7c2d12;
}
.badge-tiktok {
    background: transparent;
    color: var(--pink);
    border: 1px solid var(--pink-dim);
}
.badge-ig {
    background: transparent;
    color: #ec4899;
    border: 1px solid #831843;
}

/* Section label (like "CLASSIFIED", "INTEL", etc.) */
.section-label {
    font-family: 'Orbitron', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.25em;
    color: var(--text-sec);
    text-transform: uppercase;
    border-left: 2px solid var(--cyan-dim);
    padding-left: 8px;
    margin-bottom: 12px;
}

/* Tactical panel wrapper */
.tac-panel {
    background: transparent;
    border: none;
    border-top: 1px solid var(--border);
    padding: 1rem 0;
    position: relative;
    margin-bottom: 0.25rem;
}
.tac-panel::before {
    content: '';
    position: absolute;
    top: -1px; left: 0;
    width: 120px;
    height: 1px;
    background: var(--cyan);
}

/* Social panel variant — purple accent */
.social-panel {
    background: transparent;
    border: none;
    border-top: 1px solid #2e1065;
    padding: 1rem 0;
    position: relative;
    margin-bottom: 0.25rem;
}
.social-panel::before {
    content: '';
    position: absolute;
    top: -1px; left: 0;
    width: 120px;
    height: 1px;
    background: var(--purple);
}

/* Listening panel variant — amber accent */
.listen-panel {
    background: transparent;
    border: none;
    border-top: 1px solid rgba(245,158,11,0.15);
    padding: 1rem 0;
    position: relative;
    margin-bottom: 0.25rem;
}
.listen-panel::before {
    content: '';
    position: absolute;
    top: -1px; left: 0;
    width: 120px;
    height: 1px;
    background: var(--amber);
}

/* Blinking status dot */
@keyframes blink {
  0%,100% { opacity: 1; }
  50%      { opacity: 0.2; }
}
.status-live {
    display: inline-block;
    width: 7px; height: 7px;
    background: var(--cyan);
    border-radius: 50%;
    margin-right: 6px;
    animation: blink 1.4s ease-in-out infinite;
    box-shadow: 0 0 6px var(--cyan);
    vertical-align: middle;
}
.status-alert {
    display: inline-block;
    width: 7px; height: 7px;
    background: var(--red);
    border-radius: 50%;
    margin-right: 6px;
    animation: blink 0.8s ease-in-out infinite;
    box-shadow: 0 0 6px var(--red);
    vertical-align: middle;
}
.status-purple {
    display: inline-block;
    width: 7px; height: 7px;
    background: var(--purple);
    border-radius: 50%;
    margin-right: 6px;
    animation: blink 1.4s ease-in-out infinite;
    box-shadow: 0 0 6px var(--purple);
    vertical-align: middle;
}

/* Captions / helper text */
.stCaption, small, .caption { color: var(--text-sec) !important; font-family: 'Share Tech Mono', monospace !important; font-size: 0.72rem !important; }

/* Spinner */
.stSpinner > div { border-top-color: var(--cyan) !important; }

/* Download button */
.stDownloadButton > button {
    background: transparent !important;
    border: 1px solid var(--cyan-dim) !important;
    color: var(--text-sec) !important;
    font-family: 'Orbitron', monospace !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.1em;
    border-radius: 0 !important;
}
.stDownloadButton > button:hover {
    border-color: var(--cyan) !important;
    color: var(--cyan) !important;
}

/* ── LAYOUT TIGHTENING ──────────── */
/* Reduce vertical gap between streamlit elements */
div[data-testid="stVerticalBlockBorderWrapper"] {
    gap: 0.25rem !important;
}

/* Reduce gap between columns */
div[data-testid="column"] {
    padding: 0 0.3rem !important;
}

/* Tighter horizontal rule */
hr {
    margin: 0.5rem 0 !important;
    border-color: var(--border) !important;
    border-style: dashed !important;
}

/* Section divider — use between major sections for visual rhythm */
.section-divider {
    border: none;
    border-top: 1px dashed var(--border);
    margin: 0.5rem 0;
    position: relative;
}
.section-divider::before {
    content: '◇';
    position: absolute;
    top: -0.5em;
    left: 50%;
    transform: translateX(-50%);
    background: var(--bg-deep);
    padding: 0 6px;
    font-size: 0.5rem;
    color: var(--text-dim);
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    yt_api_key     = st.text_input("YouTube Data API Key", type="password", placeholder="AIza...")
    claude_api_key = st.text_input("Claude API Key",       type="password", placeholder="sk-ant-...")

    st.markdown("---")
    st.markdown("### 🔍 Competitor Data *(optional)*")
    dataforseo_login    = st.text_input("DataForSEO Login (email)", placeholder="you@email.com")
    dataforseo_password = st.text_input("DataForSEO Password", type="password", placeholder="password")
    st.caption("Adds real competitor channel metrics. Sign up at dataforseo.com — pay-as-you-go, ~$0.60/1000 searches.")

    st.markdown("---")
    st.markdown("### 📈 Growth Intelligence *(optional)*")
    socialblade_client_id = st.text_input("SocialBlade Client ID", type="password", placeholder="client id")
    socialblade_token     = st.text_input("SocialBlade Token",     type="password", placeholder="token")
    st.caption("Subscriber trajectory, growth grade, earnings estimates. Get API keys at socialblade.com/developers")

    st.markdown("---")
    st.markdown("### 📺 Channels to Analyze")
    channel_1   = st.text_input("Target Channel", placeholder="@handle or YouTube URL")
    video_limit = st.slider("Videos to analyze", 10, 50, 25)

    # Convert seconds to mm:ss for display
    def secs_to_mmss(s): return f"{s//60}:{s%60:02d}"
    shorts_cutoff = st.slider("Shorts cutoff (max duration)", 30, 300, 160, step=5,
                              format="%d sec",
                              help="Videos at or below this duration are treated as Shorts")
    st.caption(f"Cutoff = {secs_to_mmss(shorts_cutoff)} — adjust per channel type")

    estimate_geo = st.checkbox("🌍 Estimate Audience Geography",
                               value=st.session_state.get('estimate_geo', False),
                               help="Proxy-based US vs International estimate using comment language, "
                                    "upload timing, and keyword signals. Directional, not exact.")

    st.markdown("---")
    enable_social = st.checkbox("🌐 Enable Social Intelligence",
                                value=st.session_state.get('enable_social', False),
                                help="Adds TikTok, Instagram, and Reddit analysis layers")

    tiktok_handle = ""
    instagram_handle = ""
    reddit_search_terms = ""
    if enable_social:
        tiktok_handle = st.text_input("TikTok Handle", placeholder="@username")
        instagram_handle = st.text_input("Instagram Handle", placeholder="@username")
        reddit_search_terms = st.text_input("Reddit Search Terms", placeholder="brand name, creator name, topic")
        st.caption("Reddit: Free public data. TikTok/Instagram: Profile stats via public page extraction.")

    st.markdown("---")
    if st.button("🔍 Analyze Channel", type="primary", use_container_width=True):
        st.session_state['analyzed']       = True
        st.session_state['ch1']            = channel_1
        st.session_state['vid_limit']      = video_limit
        st.session_state['shorts_cutoff']  = shorts_cutoff
        st.session_state['estimate_geo']    = estimate_geo
        st.session_state['enable_social']  = enable_social
        st.session_state['tiktok_handle']  = tiktok_handle
        st.session_state['reddit_terms']   = reddit_search_terms
        st.session_state['ig_handle']      = instagram_handle
        st.rerun()
    analyze_btn = st.session_state.get('analyzed', False)

    if st.button("🗑 Clear Cache & Re-run", use_container_width=True,
                 help="Clears all cached API results and forces fresh analysis"):
        st.cache_data.clear()
        st.session_state['analyzed'] = False
        st.rerun()

    st.markdown("---")
    with st.expander("📋 Setup Guide"):
        st.markdown("""
**1. YouTube API Key** (free)
- [console.cloud.google.com](https://console.cloud.google.com)
- Enable **YouTube Data API v3**
- Credentials → Create → API Key

**2. Claude API Key**
- [console.anthropic.com](https://console.anthropic.com)
- API Keys → Create Key

**3. DataForSEO** (optional, pay-as-you-go)
- [dataforseo.com](https://dataforseo.com)
- Sign up → use email + password here

**4. Social Intelligence**
- **Reddit**: No API key needed — searches public Reddit data
- **TikTok**: Enter the TikTok handle to analyze
- **Instagram**: Enter the Instagram handle to analyze

**5. Install & run**
```bash
pip install streamlit google-api-python-client anthropic plotly pandas isodate requests pytrends
streamlit run app.py
```
        """)


# ─────────────────────────────────────────────────────────
# YOUTUBE HELPERS
# ─────────────────────────────────────────────────────────

def fmt_num(n):
    """Format large numbers compactly: 1.2M, 345K, etc."""
    n = int(n)
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.2f}B"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 100_000:
        return f"{n/1_000:.0f}K"
    if n >= 10_000:
        return f"{n/1_000:.1f}K"
    return f"{n:,}"

def extract_handle(text):
    text = text.strip()
    for pattern in [r'@[\w.\-]+', r'channel/(UC[\w\-]+)']:
        m = re.search(pattern, text)
        if m:
            return m.group(0)
    return text


@st.cache_data(ttl=3600, show_spinner=False)
def get_channel_info(api_key, channel_input):
    yt = build('youtube', 'v3', developerKey=api_key)
    handle = extract_handle(channel_input)
    try:
        channel_id = handle if handle.startswith('UC') else None
        if not channel_id:
            q = handle.lstrip('@')
            r = yt.search().list(part='snippet', q=q, type='channel', maxResults=1).execute()
            if not r.get('items'):
                return None
            channel_id = r['items'][0]['snippet']['channelId']
        r = yt.channels().list(
            part='snippet,statistics,contentDetails',
            id=channel_id
        ).execute()
        if not r.get('items'):
            return None
        return r['items'][0], channel_id
    except Exception as e:
        st.error(f"Channel lookup error: {e}")
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def get_channel_videos(api_key, channel_id, max_results=25):
    yt = build('youtube', 'v3', developerKey=api_key)
    ch = yt.channels().list(part='contentDetails', id=channel_id).execute()
    uploads_id = ch['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    video_ids, next_token = [], None
    while len(video_ids) < max_results:
        pl = yt.playlistItems().list(
            part='snippet',
            playlistId=uploads_id,
            maxResults=min(50, max_results - len(video_ids)),
            pageToken=next_token
        ).execute()
        for item in pl['items']:
            video_ids.append(item['snippet']['resourceId']['videoId'])
        next_token = pl.get('nextPageToken')
        if not next_token:
            break

    videos = []
    for i in range(0, len(video_ids), 50):
        resp = yt.videos().list(
            part='snippet,statistics,contentDetails',
            id=','.join(video_ids[i:i+50])
        ).execute()
        for item in resp['items']:
            s, sn = item.get('statistics', {}), item['snippet']
            dur = 0
            try:
                dur = int(isodate.parse_duration(
                    item['contentDetails'].get('duration', 'PT0S')).total_seconds())
            except Exception:
                pass
            videos.append({
                'video_id':      item['id'],
                'title':         sn.get('title', ''),
                'published_at':  sn.get('publishedAt', ''),
                'description':   sn.get('description', '')[:1000],
                'tags':          sn.get('tags', []),
                'views':         int(s.get('viewCount', 0)),
                'likes':         int(s.get('likeCount', 0)),
                'comments':      int(s.get('commentCount', 0)),
                'duration_sec':  dur,
                'duration_min':  round(dur / 60, 1),
                'url':           f"https://www.youtube.com/watch?v={item['id']}",
                'thumbnail_url': (sn.get('thumbnails', {}).get('maxres')
                               or sn.get('thumbnails', {}).get('high')
                               or sn.get('thumbnails', {}).get('medium')
                               or {}).get('url', '')
            })
    return videos


@st.cache_data(ttl=3600, show_spinner=False)
def get_sponsorblock(video_id):
    try:
        url = (f"https://sponsor.ajay.app/api/skipSegments?videoID={video_id}"
               f"&categories=[\"sponsor\",\"selfpromo\",\"exclusive_access\"]")
        r = requests.get(url, timeout=5)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


@st.cache_data(ttl=3600, show_spinner=False)
def get_top_comments(api_key, video_id, max_comments=30):
    """Fetch top-level comments sorted by relevance for a single video."""
    try:
        yt = build('youtube', 'v3', developerKey=api_key)
        resp = yt.commentThreads().list(
            part='snippet',
            videoId=video_id,
            order='relevance',
            maxResults=min(max_comments, 100),
            textFormat='plainText'
        ).execute()
        comments = []
        for item in resp.get('items', []):
            top = item['snippet']['topLevelComment']['snippet']
            comments.append({
                'text':   top.get('textDisplay', ''),
                'likes':  top.get('likeCount', 0),
                'author': top.get('authorDisplayName', '')
            })
        return comments
    except Exception:
        return []


@st.cache_data(ttl=3600, show_spinner=False)
def dataforseo_youtube_search_raw(login, password, query, max_results=10):
    """Raw API call — explicit Base64 auth as DataForSEO docs specify."""
    import base64
    try:
        credentials = base64.b64encode(f"{login}:{password}".encode()).decode()
        url     = "https://api.dataforseo.com/v3/serp/youtube/organic/live/advanced"
        payload = json.dumps([{"keyword": query, "language_code": "en",
                               "location_code": 2840, "max_crawl_pages": 1}])
        r = requests.post(
            url,
            data=payload,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/json"
            },
            timeout=15
        )
        return r.status_code, r.json()
    except Exception as e:
        return None, str(e)


def dataforseo_youtube_search(login, password, query, max_results=10):
    http_status, data = dataforseo_youtube_search_raw(login, password, query, max_results)

    if not isinstance(data, dict) or data.get('status_code') != 20000:
        return None

    tasks  = data.get('tasks') or []
    result = (tasks[0].get('result') or [{}]) if tasks else [{}]
    items  = (result[0].get('items') or []) if result else []

    videos = [i for i in items if i.get('type') in ('youtube_video', 'video')]
    return [{'title':   i.get('title',''),
             'channel': i.get('channel_name','') or i.get('channel',''),
             'views':   i.get('views_count', 0) or i.get('views', 0),
             'url':     i.get('url','')}
            for i in videos] or None


@st.cache_data(ttl=3600, show_spinner=False)
def dataforseo_keyword_cpc(login, password, keywords: tuple):
    """
    Fetch Google Ads search volume + CPC for a list of keywords.
    Uses DataForSEO Keywords Data API.
    """
    import base64
    try:
        credentials = base64.b64encode(f"{login}:{password}".encode()).decode()
        url     = "https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live"
        payload = json.dumps([{
            "keywords":      list(keywords)[:10],
            "location_code": 2840,
            "language_code": "en"
        }])
        r = requests.post(
            url,
            data=payload,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/json"
            },
            timeout=15
        )
        data = r.json()
        if not isinstance(data, dict) or data.get('status_code') != 20000:
            return None
        tasks  = data.get('tasks') or []
        result = (tasks[0].get('result') or []) if tasks else []
        return [
            {
                'keyword':       item.get('keyword', ''),
                'search_volume': item.get('search_volume', 0),
                'cpc':           item.get('cpc', 0.0),
                'competition':   item.get('competition', 0.0)
            }
            for item in result if item.get('keyword')
        ] or None
    except Exception:
        return None


# ─────────────────────────────────────────────────────────
# SOCIALBLADE HELPERS
# ─────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def get_socialblade_data(client_id, token, channel_handle):
    try:
        handle = channel_handle.lstrip('@')
        url    = f"https://matrix.sbapis.com/b/youtube/statistics"
        params = {"query": f"@{handle}", "history": "default"}
        headers = {"clientid": client_id, "token": token}
        r = requests.get(url, params=params, headers=headers, timeout=15)
        data = r.json()
        if not data.get('status', {}).get('success', False):
            return None
        return data.get('data', {})
    except Exception:
        return None


def parse_socialblade(sb_data):
    """Extract the key metrics we display from raw SocialBlade response."""
    if not sb_data:
        return None
    stats  = sb_data.get('statistics', {})
    total  = stats.get('total', {})
    growth = stats.get('growth', {})
    misc   = sb_data.get('misc', {})
    hist   = sb_data.get('daily_statistics', [])

    grade_raw = misc.get('grade', {})
    if isinstance(grade_raw, dict):
        grade = grade_raw.get('grade', 'N/A')
        grade_color_sb = grade_raw.get('color', None)
    else:
        grade = str(grade_raw) if grade_raw else 'N/A'
        grade_color_sb = None

    return {
        'grade':          grade,
        'grade_color_sb': grade_color_sb,
        'subs_30d':       growth.get('subs', {}).get('30', 0),
        'subs_7d':        growth.get('subs', {}).get('7', 0),
        'subs_1d':        growth.get('subs', {}).get('1', 0),
        'views_30d':      growth.get('views', {}).get('30', 0),
        'avg_daily_subs': round(growth.get('subs', {}).get('30', 0) / 30, 0),
        'earnings_min':   misc.get('estimatedMonthlyEarnings', {}).get('min', None),
        'earnings_max':   misc.get('estimatedMonthlyEarnings', {}).get('max', None),
        'history':        hist
    }


# ─────────────────────────────────────────────────────────
# PYTRENDS / GOOGLE TRENDS HELPERS
# ─────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def get_keyword_trends(keywords: tuple, timeframe='today 12-m'):
    try:
        pt = TrendReq(hl='en-US', tz=0, timeout=(10, 30), retries=2, backoff_factor=0.5)
        kw_list = list(keywords)[:5]
        pt.build_payload(kw_list, cat=0, timeframe=timeframe, geo='', gprop='youtube')
        iot   = pt.interest_over_time()
        rq    = pt.related_queries()
        return iot, rq
    except Exception:
        return None, None


# ─────────────────────────────────────────────────────────
# REDDIT HELPERS (Phase 1 — public JSON API, no auth)
# ─────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def reddit_search_posts(query, sort='relevance', limit=100, time_filter='month'):
    """Search Reddit for posts matching a query. Uses the public JSON API (no auth needed)."""
    try:
        headers = {'User-Agent': 'ChannelIntelBot/1.0'}
        url = "https://www.reddit.com/search.json"
        params = {
            'q': query,
            'sort': sort,
            'limit': min(limit, 100),
            't': time_filter,
            'type': 'link'
        }
        r = requests.get(url, params=params, headers=headers, timeout=15)
        if r.status_code == 429:
            time.sleep(2)
            r = requests.get(url, params=params, headers=headers, timeout=15)
        if r.status_code != 200:
            return []
        data = r.json()
        posts = []
        for child in data.get('data', {}).get('children', []):
            d = child.get('data', {})
            posts.append({
                'title':       d.get('title', ''),
                'subreddit':   d.get('subreddit', ''),
                'score':       d.get('score', 0),
                'num_comments': d.get('num_comments', 0),
                'selftext':    (d.get('selftext', '') or '')[:500],
                'url':         f"https://reddit.com{d.get('permalink', '')}",
                'created_utc': d.get('created_utc', 0),
                'upvote_ratio': d.get('upvote_ratio', 0),
                'author':      d.get('author', ''),
                'link_flair':  d.get('link_flair_text', ''),
            })
        return posts
    except Exception as e:
        return []


@st.cache_data(ttl=3600, show_spinner=False)
def reddit_search_comments(query, limit=100, time_filter='month'):
    """Search Reddit comments matching a query."""
    try:
        headers = {'User-Agent': 'ChannelIntelBot/1.0'}
        url = "https://www.reddit.com/search.json"
        params = {
            'q': query,
            'sort': 'relevance',
            'limit': min(limit, 100),
            't': time_filter,
            'type': 'comment'
        }
        r = requests.get(url, params=params, headers=headers, timeout=15)
        if r.status_code == 429:
            time.sleep(2)
            r = requests.get(url, params=params, headers=headers, timeout=15)
        if r.status_code != 200:
            return []
        data = r.json()
        comments = []
        for child in data.get('data', {}).get('children', []):
            d = child.get('data', {})
            comments.append({
                'body':        (d.get('body', '') or '')[:400],
                'subreddit':   d.get('subreddit', ''),
                'score':       d.get('score', 0),
                'url':         f"https://reddit.com{d.get('permalink', '')}",
                'created_utc': d.get('created_utc', 0),
                'author':      d.get('author', ''),
            })
        return comments
    except Exception:
        return []


# ─────────────────────────────────────────────────────────
# TIKTOK HELPERS (Phase 1 — lightweight scrape approach)
# ─────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def get_tiktok_profile_data(handle):
    """
    Attempt to fetch TikTok profile data.
    Phase 1: Uses a lightweight JSON extraction from the public page.
    For production, integrate with a service like socialdata.tools or ensembledata.com.
    Returns dict with follower/following/likes/bio or None.
    """
    handle = handle.strip().lstrip('@')
    if not handle:
        return None
    try:
        url = f"https://www.tiktok.com/@{handle}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            return None
        # Try to extract __UNIVERSAL_DATA_FOR_REHYDRATION__ JSON blob
        match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>({.+?})</script>', r.text)
        if match:
            blob = json.loads(match.group(1))
            user_detail = blob.get('__DEFAULT_SCOPE__', {}).get('webapp.user-detail', {})
            user_info = user_detail.get('userInfo', {})
            user = user_info.get('user', {})
            stats = user_info.get('stats', {})
            return {
                'username':     user.get('uniqueId', handle),
                'nickname':     user.get('nickname', ''),
                'bio':          user.get('signature', ''),
                'verified':     user.get('verified', False),
                'followers':    stats.get('followerCount', 0),
                'following':    stats.get('followingCount', 0),
                'likes':        stats.get('heartCount', 0),
                'videos':       stats.get('videoCount', 0),
                'avatar_url':   user.get('avatarLarger', ''),
            }
        # Fallback: try SIGI_STATE
        match2 = re.search(r'<script id="SIGI_STATE"[^>]*>({.+?})</script>', r.text)
        if match2:
            blob = json.loads(match2.group(1))
            user_module = blob.get('UserModule', {})
            users = user_module.get('users', {})
            stats_map = user_module.get('stats', {})
            if handle in users:
                user = users[handle]
                stats = stats_map.get(handle, {})
                return {
                    'username':     user.get('uniqueId', handle),
                    'nickname':     user.get('nickname', ''),
                    'bio':          user.get('signature', ''),
                    'verified':     user.get('verified', False),
                    'followers':    stats.get('followerCount', 0),
                    'following':    stats.get('followingCount', 0),
                    'likes':        stats.get('heartCount', 0),
                    'videos':       stats.get('videoCount', 0),
                    'avatar_url':   user.get('avatarLarger', ''),
                }
        return None
    except Exception:
        return None


# ─────────────────────────────────────────────────────────
# INSTAGRAM HELPERS (Phase 2 — public page extraction)
# ─────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def get_instagram_profile_data(handle):
    """
    Fetch Instagram profile data from the public page.
    Tries multiple extraction strategies for the embedded JSON data.
    For production at scale, integrate with Apify or PhantomBuster.
    Returns dict with followers/following/posts/bio or None.
    """
    handle = handle.strip().lstrip('@')
    if not handle:
        return None

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }

    # Strategy 1: Try the web profile info API endpoint
    try:
        api_url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={handle}"
        api_headers = {**headers, 'X-IG-App-ID': '936619743392459'}
        r = requests.get(api_url, headers=api_headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            user = data.get('data', {}).get('user', {})
            if user:
                return {
                    'username':     user.get('username', handle),
                    'full_name':    user.get('full_name', ''),
                    'bio':          user.get('biography', ''),
                    'verified':     user.get('is_verified', False),
                    'is_business':  user.get('is_business_account', False),
                    'category':     user.get('category_name', ''),
                    'followers':    user.get('edge_followed_by', {}).get('count', 0),
                    'following':    user.get('edge_follow', {}).get('count', 0),
                    'posts':        user.get('edge_owner_to_timeline_media', {}).get('count', 0),
                    'profile_pic':  user.get('profile_pic_url_hd', ''),
                    'external_url': user.get('external_url', ''),
                    'is_private':   user.get('is_private', False),
                    # Extract recent post engagement if available
                    'recent_posts': _extract_ig_recent_posts(user),
                }
    except Exception:
        pass

    # Strategy 2: Try the public page with ?__a=1&__d=dis
    try:
        url = f"https://www.instagram.com/{handle}/?__a=1&__d=dis"
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            user = data.get('graphql', {}).get('user', {})
            if not user:
                user = data.get('user', {})
            if user:
                return {
                    'username':     user.get('username', handle),
                    'full_name':    user.get('full_name', ''),
                    'bio':          user.get('biography', ''),
                    'verified':     user.get('is_verified', False),
                    'is_business':  user.get('is_business_account', False),
                    'category':     user.get('category_name', ''),
                    'followers':    user.get('edge_followed_by', {}).get('count', 0),
                    'following':    user.get('edge_follow', {}).get('count', 0),
                    'posts':        user.get('edge_owner_to_timeline_media', {}).get('count', 0),
                    'profile_pic':  user.get('profile_pic_url_hd', ''),
                    'external_url': user.get('external_url', ''),
                    'is_private':   user.get('is_private', False),
                    'recent_posts': _extract_ig_recent_posts(user),
                }
    except Exception:
        pass

    # Strategy 3: Scrape the HTML page for embedded JSON
    try:
        url = f"https://www.instagram.com/{handle}/"
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            return None
        # Look for window._sharedData or similar embedded JSON
        match = re.search(r'window\._sharedData\s*=\s*({.+?});</script>', r.text)
        if match:
            blob = json.loads(match.group(1))
            user = (blob.get('entry_data', {})
                       .get('ProfilePage', [{}])[0]
                       .get('graphql', {})
                       .get('user', {}))
            if user:
                return {
                    'username':     user.get('username', handle),
                    'full_name':    user.get('full_name', ''),
                    'bio':          user.get('biography', ''),
                    'verified':     user.get('is_verified', False),
                    'is_business':  user.get('is_business_account', False),
                    'category':     user.get('category_name', ''),
                    'followers':    user.get('edge_followed_by', {}).get('count', 0),
                    'following':    user.get('edge_follow', {}).get('count', 0),
                    'posts':        user.get('edge_owner_to_timeline_media', {}).get('count', 0),
                    'profile_pic':  user.get('profile_pic_url_hd', ''),
                    'external_url': user.get('external_url', ''),
                    'is_private':   user.get('is_private', False),
                    'recent_posts': _extract_ig_recent_posts(user),
                }
        # Look for meta tag og:description as fallback for basic follower count
        og_match = re.search(r'<meta property="og:description" content="([^"]+)"', r.text)
        if og_match:
            desc = og_match.group(1)
            nums = re.findall(r'([\d,.]+[KMB]?)\s+(Followers|Following|Posts)', desc, re.IGNORECASE)
            if nums:
                parsed = {}
                for val, label in nums:
                    parsed[label.lower()] = _parse_ig_count(val)
                return {
                    'username':     handle,
                    'full_name':    '',
                    'bio':          '',
                    'verified':     False,
                    'is_business':  False,
                    'category':     '',
                    'followers':    parsed.get('followers', 0),
                    'following':    parsed.get('following', 0),
                    'posts':        parsed.get('posts', 0),
                    'profile_pic':  '',
                    'external_url': '',
                    'is_private':   False,
                    'recent_posts': [],
                    '_source':      'og_meta_fallback'
                }
    except Exception:
        pass

    return None


def _parse_ig_count(val):
    """Parse Instagram count strings like '1.2M', '345K', '12,345'."""
    val = val.strip().replace(',', '')
    try:
        if val.upper().endswith('B'):
            return int(float(val[:-1]) * 1_000_000_000)
        if val.upper().endswith('M'):
            return int(float(val[:-1]) * 1_000_000)
        if val.upper().endswith('K'):
            return int(float(val[:-1]) * 1_000)
        return int(float(val))
    except (ValueError, TypeError):
        return 0


def _extract_ig_recent_posts(user_data):
    """Extract recent post engagement data from Instagram user graph data."""
    posts = []
    try:
        edges = (user_data.get('edge_owner_to_timeline_media', {})
                          .get('edges', []))
        for edge in edges[:12]:  # Last 12 posts
            node = edge.get('node', {})
            posts.append({
                'likes':     node.get('edge_liked_by', {}).get('count', 0)
                             or node.get('edge_media_preview_like', {}).get('count', 0),
                'comments':  node.get('edge_media_to_comment', {}).get('count', 0)
                             or node.get('edge_media_preview_comment', {}).get('count', 0),
                'is_video':  node.get('is_video', False),
                'caption':   (node.get('edge_media_to_caption', {})
                                  .get('edges', [{}])[0]
                                  .get('node', {})
                                  .get('text', ''))[:200] if node.get('edge_media_to_caption') else '',
                'timestamp': node.get('taken_at_timestamp', 0),
            })
    except Exception:
        pass
    return posts


# ─────────────────────────────────────────────────────────
# AUDIENCE GEOGRAPHY ESTIMATION (proxy-based)
# ─────────────────────────────────────────────────────────

def _detect_language_signals(text):
    """
    Lightweight language detection via character set and common word heuristics.
    Returns a dict of language signal counts.
    """
    signals = {'english': 0, 'spanish': 0, 'portuguese': 0, 'german': 0,
               'french': 0, 'hindi': 0, 'other_latin': 0, 'cjk': 0,
               'cyrillic': 0, 'arabic': 0, 'other': 0}
    if not text:
        return signals

    text_lower = text.lower()

    # CJK characters (Chinese, Japanese, Korean)
    cjk_count = len(re.findall(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]', text))
    if cjk_count > 5:
        signals['cjk'] += 1
        return signals

    # Cyrillic
    cyrillic_count = len(re.findall(r'[\u0400-\u04ff]', text))
    if cyrillic_count > 5:
        signals['cyrillic'] += 1
        return signals

    # Arabic / Hebrew
    arabic_count = len(re.findall(r'[\u0600-\u06ff\u0590-\u05ff]', text))
    if arabic_count > 5:
        signals['arabic'] += 1
        return signals

    # Devanagari (Hindi)
    if len(re.findall(r'[\u0900-\u097f]', text)) > 3:
        signals['hindi'] += 1
        return signals

    # Latin-script language detection via common words
    en_words = {'the', 'is', 'are', 'was', 'this', 'that', 'have', 'has', 'for', 'with',
                'you', 'your', 'not', 'but', 'from', 'they', 'been', 'would', 'about',
                'just', 'like', 'really', 'great', 'video', 'amazing', 'love', 'thanks',
                'awesome', 'best', 'ever', 'much', 'very', 'good', 'more', 'know'}
    es_words = {'los', 'las', 'del', 'que', 'por', 'una', 'con', 'para', 'como', 'pero',
                'muy', 'este', 'esta', 'tiene', 'puede', 'desde', 'más', 'cuando', 'bien'}
    pt_words = {'que', 'não', 'uma', 'como', 'para', 'mais', 'muito', 'isso', 'esse',
                'esse', 'são', 'tem', 'também', 'pela', 'sobre', 'ainda', 'depois', 'sempre'}
    de_words = {'der', 'die', 'das', 'und', 'ist', 'ein', 'eine', 'mit', 'auf', 'den',
                'auch', 'nicht', 'sich', 'ich', 'aber', 'noch', 'kann', 'wird'}
    fr_words = {'les', 'des', 'une', 'que', 'est', 'dans', 'qui', 'pour', 'pas', 'sur',
                'avec', 'mais', 'sont', 'cette', 'aussi', 'comme', 'très', 'bien', 'fait'}

    words = set(re.findall(r'\b[a-záéíóúàèìòùäöüñçãâêîôû]{3,}\b', text_lower))

    en_score = len(words & en_words)
    es_score = len(words & es_words)
    pt_score = len(words & pt_words)
    de_score = len(words & de_words)
    fr_score = len(words & fr_words)

    max_score = max(en_score, es_score, pt_score, de_score, fr_score)
    if max_score == 0:
        signals['other'] += 1
    elif en_score == max_score:
        signals['english'] += 1
    elif es_score == max_score:
        signals['spanish'] += 1
    elif pt_score == max_score:
        signals['portuguese'] += 1
    elif de_score == max_score:
        signals['german'] += 1
    elif fr_score == max_score:
        signals['french'] += 1

    return signals


@st.cache_data(ttl=3600, show_spinner=False)
def collect_geography_signals(api_key, channel_info, videos, _comment_sample=None):
    """
    Collect proxy signals for audience geography estimation.
    Returns a structured dict of all available signals.
    """
    sn = channel_info.get('snippet', {})
    stats = channel_info.get('statistics', {})

    # ── Signal 1: Channel declared country ──────────────────
    channel_country = sn.get('country', 'unknown')

    # ── Signal 2: Upload hour distribution (UTC) ────────────
    upload_hours = []
    for v in videos:
        try:
            pub = pd.to_datetime(v.get('published_at'))
            upload_hours.append(pub.hour)
        except Exception:
            pass

    hour_dist = Counter(upload_hours)
    # US primetime uploads cluster around 14:00-20:00 UTC (9AM-3PM ET)
    us_primetime_uploads = sum(hour_dist.get(h, 0) for h in range(14, 21))
    eu_primetime_uploads = sum(hour_dist.get(h, 0) for h in range(7, 14))  # 8AM-3PM CET
    asia_primetime_uploads = sum(hour_dist.get(h, 0) for h in list(range(0, 7)) + [23])
    total_uploads = max(len(upload_hours), 1)

    # ── Signal 3: Comment language distribution ─────────────
    lang_totals = {'english': 0, 'spanish': 0, 'portuguese': 0, 'german': 0,
                   'french': 0, 'hindi': 0, 'other_latin': 0, 'cjk': 0,
                   'cyrillic': 0, 'arabic': 0, 'other': 0}

    comments_analyzed = 0
    if _comment_sample:
        for c in _comment_sample:
            text = c.get('text', '') or c.get('body', '')
            signals = _detect_language_signals(text)
            for k, v_count in signals.items():
                lang_totals[k] += v_count
            comments_analyzed += 1

    total_lang = max(sum(lang_totals.values()), 1)
    english_pct = round(lang_totals['english'] / total_lang * 100, 1)

    # ── Signal 4: Video title/description language ──────────
    title_lang = {'english': 0, 'non_english': 0}
    for v in videos[:25]:
        sig = _detect_language_signals(v.get('title', ''))
        if sig.get('english', 0) > 0:
            title_lang['english'] += 1
        else:
            title_lang['non_english'] += 1

    # ── Signal 5: Default audio language from API ───────────
    default_language = sn.get('defaultAudioLanguage', sn.get('defaultLanguage', 'unknown'))

    # ── Assemble all signals ────────────────────────────────
    return {
        'channel_country':       channel_country,
        'default_language':      default_language,
        'upload_hour_distribution': dict(hour_dist.most_common(10)),
        'upload_timezone_signals': {
            'us_primetime_pct':   round(us_primetime_uploads / total_uploads * 100, 1),
            'eu_primetime_pct':   round(eu_primetime_uploads / total_uploads * 100, 1),
            'asia_primetime_pct': round(asia_primetime_uploads / total_uploads * 100, 1),
        },
        'comment_language_distribution': {
            k: round(v / total_lang * 100, 1) for k, v in lang_totals.items() if v > 0
        },
        'english_comment_pct':   english_pct,
        'comments_analyzed':     comments_analyzed,
        'title_language': {
            'english_pct': round(title_lang['english'] / max(sum(title_lang.values()), 1) * 100, 1)
        },
        'methodology_note': (
            'Geography estimated via proxy signals: channel declared country, '
            'comment language distribution, upload hour clustering, content language. '
            'This is DIRECTIONAL — not verified analytics data. Confidence improves '
            'with more comments analyzed. For exact geography, channel owner must '
            'provide YouTube Analytics access.'
        )
    }


# ─────────────────────────────────────────────────────────
# CLAUDE HELPERS (existing + new social/listening prompts)
# ─────────────────────────────────────────────────────────

def claude_call(client, prompt, max_tokens=1400):
    try:
        resp = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.content[0].text
    except Exception as e:
        raise RuntimeError(f"Claude API error: {e}") from e


def parse_json(text):
    text = re.sub(r'```json|```', '', text).strip()
    try:
        return json.loads(text)
    except Exception:
        return None


# ── EXISTING YOUTUBE CLAUDE FUNCTIONS ──────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def claude_content_analysis(_client, titles_json, descriptions_json, tags_json, stats_json, channel_name):
    prompt = f"""You are an expert YouTube content strategist. Analyze "{channel_name}".

TITLES: {titles_json}
DESCRIPTIONS: {descriptions_json}
TOP TAGS: {tags_json}
VIDEO STATS (title, views, likes, comments, duration_min): {stats_json}

Return ONLY valid JSON, no markdown, no extra text:
{{
  "main_topics": ["topic1","topic2","topic3","topic4","topic5"],
  "topic_breakdown": {{"Topic A": 35, "Topic B": 25, "Topic C": 20, "Topic D": 20}},
  "content_pillars": ["pillar1","pillar2","pillar3"],
  "content_style": "description",
  "target_audience": "specific description",
  "tone": "tone description",
  "upload_series": ["series or recurring format 1","series 2"],
  "top_performing_themes": ["theme1","theme2","theme3"],
  "strengths": ["strength1","strength2","strength3"],
  "content_gaps": ["gap1","gap2","gap3"],
  "programming_cadence_notes": "observations about upload patterns and scheduling"
}}"""
    return parse_json(claude_call(_client, prompt, max_tokens=1200))


@st.cache_data(ttl=3600, show_spinner=False)
def claude_sponsor_analysis(_client, titles_json, descriptions_json, channel_name):
    prompt = f"""You are a sponsorship intelligence analyst for YouTube channel "{channel_name}".

VIDEO TITLES: {titles_json}

FULL VIDEO DESCRIPTIONS (contains sponsor disclosures, affiliate links, promo codes):
{descriptions_json}

Scan for: "sponsored by", affiliate links, promo codes, #ad/#sponsored, brand URLs, discount codes.

Return ONLY valid JSON, no markdown, no extra text:
{{
  "sponsors_found": ["Brand1","Brand2"],
  "sponsor_categories": ["category1","category2"],
  "promo_codes": ["CODE1","CODE2"],
  "affiliate_programs": ["Amazon Associates","program2"],
  "typical_placement": "beginning/mid-roll/end/multiple",
  "ad_read_style": "host-read/scripted/natural/integrated",
  "estimated_frequency": "X out of 10 videos",
  "brand_fit_assessment": "assessment",
  "self_promotion": ["own products/courses/memberships"],
  "monetization_tier": "low/mid/high with brief reason",
  "untapped_categories": ["category1","category2","category3"]
}}"""
    return parse_json(claude_call(_client, prompt, max_tokens=1200))


@st.cache_data(ttl=3600, show_spinner=False)
def claude_generate_search_queries(_client, channel_name, titles_json, tags_json, stats_json):
    prompt = f"""You are a YouTube competitive intelligence analyst. Your job is to generate YouTube search queries that will surface the most relevant competitor channels when entered into YouTube search.

Channel: {channel_name}
Recent titles (sample): {titles_json}
Top tags: {tags_json}
Top videos by views: {stats_json}

Generate 8 distinct search queries across these 4 dimensions — 2 queries per dimension:

1. TOPIC QUERIES — the core subject matter this channel covers (what the content is ABOUT)
2. GENRE QUERIES — the style/format of content (e.g. "science explainer", "documentary style", "experiment channel")
3. AUDIENCE QUERIES — who watches this (e.g. "science for curious adults", "engineering education")
4. ADJACENT QUERIES — neighbouring niches that share the same audience but cover different ground

Rules:
- Each query should be 2-5 words
- Queries must be diverse — no two should return the same channels
- Think like someone searching YouTube for channels to watch, not articles to read
- Don't include the channel name itself
- Prioritise queries that would surface mid-size competitors (100k-5M subs), not just the giants

Return ONLY valid JSON, no markdown:
{{
  "topic":    ["query1", "query2"],
  "genre":    ["query1", "query2"],
  "audience": ["query1", "query2"],
  "adjacent": ["query1", "query2"]
}}"""
    return parse_json(claude_call(_client, prompt, max_tokens=400))


@st.cache_data(ttl=3600, show_spinner=False)
def claude_competitor_analysis(_client, ch1_json, ch2_json, dfs_json):
    ch2_block = f"\nChannel 2: {ch2_json}" if ch2_json else ""
    dfs_block = f"\nReal DataForSEO search results for context: {dfs_json}" if dfs_json else \
                "\nNo DataForSEO data — infer competitors from channel content and topics."
    prompt = f"""You are a senior YouTube strategy consultant.

Channel 1: {ch1_json}{ch2_block}{dfs_block}

Identify specific real YouTube channels as competitors and map strategic opportunities.

Return ONLY valid JSON, no markdown, no extra text:
{{
  "competitor_channels": [
    {{"name":"Real Name","handle":"@handle","subscribers":"est.","why":"overlap reason","threat_level":"high/medium/low"}},
    {{"name":"Real Name","handle":"@handle","subscribers":"est.","why":"overlap reason","threat_level":"high/medium/low"}},
    {{"name":"Real Name","handle":"@handle","subscribers":"est.","why":"overlap reason","threat_level":"high/medium/low"}},
    {{"name":"Real Name","handle":"@handle","subscribers":"est.","why":"overlap reason","threat_level":"high/medium/low"}},
    {{"name":"Real Name","handle":"@handle","subscribers":"est.","why":"overlap reason","threat_level":"high/medium/low"}}
  ],
  "competitive_position": "where this channel sits in the landscape",
  "key_differentiators": ["differentiator1","differentiator2","differentiator3"],
  "white_space_topics": ["topic1","topic2","topic3","topic4","topic5"],
  "format_opportunities": ["format1","format2","format3"],
  "audience_expansion_opportunities": ["opportunity1","opportunity2","opportunity3"],
  "subchannel_concepts": [
    {{"name":"Name","concept":"what it covers","target_audience":"who","rationale":"why"}},
    {{"name":"Name","concept":"what it covers","target_audience":"who","rationale":"why"}},
    {{"name":"Name","concept":"what it covers","target_audience":"who","rationale":"why"}}
  ],
  "business_extensions": ["idea1","idea2","idea3","idea4"],
  "strategic_summary": "2-3 sentence synthesis"
}}"""
    return parse_json(claude_call(_client, prompt, max_tokens=2000))


@st.cache_data(ttl=3600, show_spinner=False)
def claude_comment_intelligence(_client, comments_json, channel_name):
    prompt = f"""You are an audience intelligence analyst studying YouTube comments for "{channel_name}".

Here are the top comments (sorted by likes/relevance) from the channel's highest-performing videos:
{comments_json}

Analyse these comments to extract deep audience intelligence. Look for:
- Recurring questions the audience is asking (= future video ideas)
- Emotional reactions (what made people feel something)
- What people say they learned or discovered
- Requests and demands ("you should do a video on...")
- Complaints or frustrations (= unmet needs)
- Demographic signals (how people describe themselves)
- What people share with others or say they're sharing
- Topics that sparked debate or strong disagreement

Return ONLY valid JSON, no markdown:
{{
  "top_questions": [
    {{"question": "exact recurring question type", "frequency": "how often", "opportunity": "video concept this suggests"}},
    {{"question": "...", "frequency": "...", "opportunity": "..."}},
    {{"question": "...", "frequency": "...", "opportunity": "..."}},
    {{"question": "...", "frequency": "...", "opportunity": "..."}},
    {{"question": "...", "frequency": "...", "opportunity": "..."}}
  ],
  "emotional_triggers": ["what made people feel wonder/shock/joy/etc"],
  "content_requests": ["specific topics audience has explicitly asked for"],
  "audience_personas": ["description of distinct viewer types who show up in comments"],
  "pain_points": ["frustrations or unmet needs expressed"],
  "shareability_signals": ["topics/moments people said they shared or tagged others in"],
  "controversy_zones": ["topics that sparked debate"],
  "demographic_signals": ["age/profession/background signals found in comments"],
  "sentiment_summary": "overall tone and relationship between creator and audience",
  "top_content_ideas": ["5 specific video ideas directly derived from comment patterns"]
}}"""
    return parse_json(claude_call(_client, prompt, max_tokens=2000))


@st.cache_data(ttl=3600, show_spinner=False)
def claude_thumbnail_intelligence(_client, thumbnail_data_json, channel_name):
    prompt = f"""You are a visual content strategist and YouTube thumbnail analyst for "{channel_name}".

I'm providing you thumbnail URLs and performance data for this channel's videos.
Analyse the patterns across high-performing vs low-performing thumbnails.

Data: {thumbnail_data_json}

Analyse:
- Face presence patterns (creator face vs no face, emotion on face)
- Text usage (how much text, what style, where positioned)
- Color palette patterns (dominant colors, contrast levels, backgrounds)
- Composition patterns (close-up vs wide, single subject vs multiple)
- What the top-10 by views thumbnails have in common visually
- What the bottom-10 by views thumbnails have in common visually
- Click-bait vs informational thumbnail styles and which performs better
- Consistency of brand identity across thumbnails
- Comparison to what typically works in this content niche

Return ONLY valid JSON, no markdown:
{{
  "high_performer_patterns": ["visual pattern 1", "visual pattern 2", "visual pattern 3"],
  "low_performer_patterns":  ["visual pattern 1", "visual pattern 2", "visual pattern 3"],
  "face_strategy": "analysis of how creator face is used and its effect",
  "text_strategy": "analysis of text usage patterns and effectiveness",
  "color_palette": "dominant colors, contrast strategy, brand consistency",
  "composition_style": "framing, subject placement, background patterns",
  "brand_consistency_score": "strong/moderate/weak with explanation",
  "ctr_hypothesis": "what is likely driving click-through rate based on patterns",
  "immediate_improvements": ["specific actionable change 1", "specific actionable change 2", "specific actionable change 3"],
  "winning_formula": "single sentence describing the thumbnail formula that performs best for this channel",
  "competitor_gap": "what thumbnail approaches competitors likely use that this channel isn't exploiting"
}}"""
    return parse_json(claude_call(_client, prompt, max_tokens=1500))


# ── GEOGRAPHY ESTIMATION CLAUDE FUNCTION ───────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def claude_geography_estimation(_client, geo_signals_json, cpc_context_json, channel_name):
    prompt = f"""You are a YouTube audience geography analyst. Your job is to estimate the likely
geographic breakdown of a channel's audience using PROXY signals — not direct analytics.

CHANNEL: "{channel_name}"

PROXY SIGNALS COLLECTED:
{geo_signals_json}

CPC / KEYWORD DATA (if available — US-heavy keyword CPCs suggest US advertiser demand):
{cpc_context_json}

Using ALL available signals, estimate the audience geography breakdown.

Reasoning framework:
- English comments at 80%+ with US channel country = likely 50-70% US domestic
- English comments at 80%+ with UK/AU/CA country = likely 30-50% US (English-speaking international)
- High Spanish/Portuguese comment % = significant LatAm audience
- Upload hours clustering in US primetime (14:00-20:00 UTC) = creator likely targets US viewers
- High CPC keywords in US market = advertisers pay US rates, suggesting US-heavy audience
- CJK/Cyrillic/Arabic comments = significant non-Western audience segments

Be precise about confidence levels. This is estimation, not measurement.

Return ONLY valid JSON, no markdown:
{{
  "estimated_us_domestic_pct": 55,
  "estimated_regions": [
    {{"region": "United States", "pct": 55, "confidence": "moderate"}},
    {{"region": "United Kingdom", "pct": 10, "confidence": "low"}},
    {{"region": "Canada", "pct": 7, "confidence": "low"}},
    {{"region": "Other English-speaking", "pct": 8, "confidence": "low"}},
    {{"region": "Non-English", "pct": 20, "confidence": "directional"}}
  ],
  "english_speaking_total_pct": 80,
  "primary_market": "United States",
  "market_classification": "US-dominant / English-international / Global-mixed / Non-English-dominant",
  "confidence_level": "moderate/low/directional",
  "confidence_reasoning": "1-2 sentence explanation of why this confidence level",
  "key_signals_used": ["signal 1 that most influenced the estimate", "signal 2"],
  "advertiser_implications": "what this geographic mix means for CPM rates and sponsor value",
  "caveats": "specific limitations of this estimate"
}}"""
    return parse_json(claude_call(_client, prompt, max_tokens=1200))


# ── NEW: SOCIAL CROSS-PLATFORM CLAUDE FUNCTIONS ───────────

@st.cache_data(ttl=3600, show_spinner=False)
def claude_cross_platform_analysis(_client, youtube_data_json, tiktok_data_json, instagram_data_json, reddit_data_json, channel_name):
    prompt = f"""You are a cross-platform social media strategist analyzing "{channel_name}".

YOUTUBE DATA:
{youtube_data_json}

TIKTOK DATA:
{tiktok_data_json}

INSTAGRAM DATA:
{instagram_data_json}

REDDIT PRESENCE DATA:
{reddit_data_json}

Analyse this creator/brand's cross-platform presence. Consider:
- Platform allocation: where are they investing the most effort?
- Audience overlap vs. fragmentation across platforms
- Content repurposing patterns (same content adapted vs. unique per platform)
- Platform-audience fit: is their content style suited to each platform?
- Growth velocity comparison across platforms
- Which platform is under-invested relative to opportunity?
- Instagram Reels vs TikTok vs YouTube Shorts overlap and cannibalization risk

Return ONLY valid JSON, no markdown:
{{
  "platform_summary": {{
    "youtube": {{"status": "primary/secondary/inactive", "strength": "what works here", "weakness": "what could improve"}},
    "tiktok": {{"status": "primary/secondary/inactive", "strength": "what works here", "weakness": "what could improve"}},
    "instagram": {{"status": "primary/secondary/inactive", "strength": "what works here", "weakness": "what could improve"}},
    "reddit": {{"status": "high/moderate/low presence", "sentiment": "positive/mixed/negative", "key_subreddits": ["sub1","sub2"]}}
  }},
  "content_repurposing_score": "high/moderate/low — with explanation",
  "short_form_strategy": "how TikTok, Reels, and Shorts should be coordinated vs cannibalized",
  "platform_audience_fit": "analysis of which platforms match the audience best",
  "cross_platform_strategy_grade": "A/B/C/D/F — with explanation",
  "biggest_cross_platform_opportunity": "specific actionable recommendation",
  "platform_priority_ranking": ["platform1", "platform2", "platform3", "platform4"],
  "content_adaptation_recommendations": [
    {{"platform": "TikTok", "recommendation": "specific tactic", "expected_impact": "high/medium/low"}},
    {{"platform": "Instagram", "recommendation": "specific tactic", "expected_impact": "high/medium/low"}},
    {{"platform": "Reddit", "recommendation": "specific tactic", "expected_impact": "high/medium/low"}}
  ],
  "audience_migration_potential": "assessment of moving audience between platforms",
  "risk_factors": ["platform-specific risk 1", "risk 2"],
  "90_day_social_expansion_plan": ["week 1-2 action", "week 3-4 action", "month 2 action", "month 3 action"]
}}"""
    return parse_json(claude_call(_client, prompt, max_tokens=2500))


@st.cache_data(ttl=3600, show_spinner=False)
def claude_reddit_listening(_client, posts_json, comments_json, channel_name):
    prompt = f"""You are a social listening analyst specializing in Reddit intelligence for "{channel_name}".

REDDIT POSTS MENTIONING THIS CREATOR/BRAND:
{posts_json}

REDDIT COMMENTS MENTIONING THIS CREATOR/BRAND:
{comments_json}

Perform deep social listening analysis:

1. SENTIMENT: What is the overall sentiment toward this creator/brand on Reddit?
2. PERCEPTION: How does Reddit perceive this creator vs how they present themselves?
3. RECURRING THEMES: What topics come up repeatedly in discussions?
4. CRITICISM PATTERNS: What are the most common criticisms? Are they valid?
5. PRAISE PATTERNS: What do fans specifically praise?
6. AUDIENCE INTELLIGENCE: What can we learn about the audience from how they discuss this creator?
7. CONTROVERSY: Any PR risks, controversies, or negative sentiment spikes?
8. CONTENT DEMAND: What does the Reddit audience want that the creator isn't providing?
9. COMPETITOR MENTIONS: Are other creators/brands frequently mentioned alongside this one?
10. BRAND SAFETY: Would a sponsor be comfortable associating with this Reddit discussion profile?

Return ONLY valid JSON, no markdown:
{{
  "overall_sentiment": "positive/mixed/negative — with nuance",
  "sentiment_score": 7,
  "perception_gap": "how Reddit sees them vs how they present themselves",
  "recurring_themes": [
    {{"theme": "topic", "sentiment": "positive/negative/mixed", "frequency": "high/medium/low"}},
    {{"theme": "topic", "sentiment": "positive/negative/mixed", "frequency": "high/medium/low"}},
    {{"theme": "topic", "sentiment": "positive/negative/mixed", "frequency": "high/medium/low"}},
    {{"theme": "topic", "sentiment": "positive/negative/mixed", "frequency": "high/medium/low"}},
    {{"theme": "topic", "sentiment": "positive/negative/mixed", "frequency": "high/medium/low"}}
  ],
  "top_criticisms": ["criticism1", "criticism2", "criticism3"],
  "top_praise": ["praise1", "praise2", "praise3"],
  "controversy_flags": ["flag1 or 'none detected'"],
  "brand_safety_score": "safe/caution/risk — with explanation",
  "content_demand_signals": ["what Reddit wants 1", "what Reddit wants 2", "what Reddit wants 3"],
  "competitor_mentions": ["competitor1", "competitor2"],
  "key_subreddits": ["r/subreddit1", "r/subreddit2", "r/subreddit3"],
  "audience_demographics_from_reddit": "inferred demographics based on subreddits and language",
  "actionable_insights": ["insight1", "insight2", "insight3"],
  "quote_highlights": [
    {{"quote_summary": "paraphrased notable comment", "context": "what it tells us", "sentiment": "pos/neg/neutral"}},
    {{"quote_summary": "paraphrased notable comment", "context": "what it tells us", "sentiment": "pos/neg/neutral"}},
    {{"quote_summary": "paraphrased notable comment", "context": "what it tells us", "sentiment": "pos/neg/neutral"}}
  ]
}}"""
    return parse_json(claude_call(_client, prompt, max_tokens=2500))


@st.cache_data(ttl=3600, show_spinner=False)
def claude_tiktok_analysis(_client, tiktok_profile_json, youtube_context_json, channel_name):
    prompt = f"""You are a TikTok growth strategist comparing TikTok presence to YouTube for "{channel_name}".

TIKTOK PROFILE DATA:
{tiktok_profile_json}

YOUTUBE CONTEXT (for comparison):
{youtube_context_json}

Analyse the TikTok presence relative to YouTube:

Return ONLY valid JSON, no markdown:
{{
  "tiktok_health_assessment": "strong/moderate/weak/absent — with context",
  "follower_to_sub_ratio": "TikTok followers vs YouTube subs — what this implies",
  "engagement_comparison": "TikTok likes vs YouTube engagement — relative performance",
  "content_volume_comparison": "posting frequency difference",
  "platform_strategy_type": "repurpose/native/hybrid/absent",
  "tiktok_growth_potential": "high/medium/low — with reasoning",
  "tiktok_content_recommendations": [
    "specific format/style recommendation 1",
    "specific format/style recommendation 2",
    "specific format/style recommendation 3"
  ],
  "cross_promotion_opportunities": ["opportunity 1", "opportunity 2"],
  "tiktok_audience_profile": "who the TikTok audience likely is vs YouTube audience",
  "monetization_readiness": "how close is the TikTok account to meaningful monetization"
}}"""
    return parse_json(claude_call(_client, prompt, max_tokens=1500))


@st.cache_data(ttl=3600, show_spinner=False)
def claude_instagram_analysis(_client, ig_profile_json, youtube_context_json, channel_name):
    prompt = f"""You are an Instagram growth strategist comparing Instagram presence to YouTube for "{channel_name}".

INSTAGRAM PROFILE DATA:
{ig_profile_json}

YOUTUBE CONTEXT (for comparison):
{youtube_context_json}

Analyse the Instagram presence relative to YouTube:

Return ONLY valid JSON, no markdown:
{{
  "ig_health_assessment": "strong/moderate/weak/absent — with context",
  "follower_to_sub_ratio": "Instagram followers vs YouTube subs — what this implies",
  "engagement_rate_assessment": "calculated from recent posts if available, compared to IG norms (1-3% good, 3-6% great, 6%+ exceptional)",
  "content_type_mix": "Reels-heavy / grid-heavy / Stories-dependent / balanced",
  "platform_strategy_type": "repurpose/native/hybrid/absent",
  "ig_growth_potential": "high/medium/low — with reasoning",
  "ig_content_recommendations": [
    "specific format/style recommendation 1",
    "specific format/style recommendation 2",
    "specific format/style recommendation 3"
  ],
  "reels_strategy": "how to leverage Reels given YouTube content library",
  "stories_strategy": "how Stories should complement the content ecosystem",
  "cross_promotion_opportunities": ["opportunity 1", "opportunity 2"],
  "ig_audience_profile": "who the Instagram audience likely is vs YouTube audience",
  "brand_partnership_readiness": "assessment of Instagram's value for brand deals vs YouTube",
  "monetization_readiness": "how close is the IG account to meaningful monetization (Reels bonus, brand deals, shopping)"
}}"""
    return parse_json(claude_call(_client, prompt, max_tokens=1500))


# ── STRATEGIC BRIEF FUNCTIONS ──────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def claude_strategic_brief(_client, context_json):
    prompt = f"""You are a senior YouTube strategy consultant writing a client presentation brief.

DATA PROVIDED:
{context_json}

═══════════════════════════════════════════════════
MANDATORY ANALYTICAL RULES — violating these invalidates the brief
═══════════════════════════════════════════════════

RULE 1 — ENGAGEMENT BENCHMARKING:
Never cite an engagement rate as good or bad in isolation.
Always state: (a) the channel's own engagement_trend — is it RECOVERING, STABLE, or DECLINING?
(b) compare engagement_early_period vs engagement_recent_period to show trajectory.
(c) use avg_engagement_per_1k_subs for any cross-channel comparisons — raw % is scale-dependent
and meaningless across channels of different sizes. If comparing to an external channel not in the
dataset, state "based on published benchmarks, not live data."

RULE 2 — MONETIZATION ESTIMATES MUST BE GROUNDED:
If keyword_cpc_data is available, use it. The sponsorship_rationale field already contains a
calculated implied sponsor value — cite it with its formula. Format:
"At $[avg_cpc] avg topic CPC and [views] avg views, implied integration value is $X–Y
(20–40x CPM multiplier standard for direct integrations)."
If CPC data is unavailable, give a range and label it: "industry estimate, unverified for this channel."
Never assert a dollar figure without grounding.

RULE 3 — CROSS-CHANNEL COMPARISONS:
Only normalize comparisons using engagement_per_1k_subs, never raw engagement%.
A 3% engagement rate on a 20M-sub channel is NOT "low" — subscriber base inflates denominator.
Never use absolute language ("catastrophically low," "destroys benchmarks") for scale-dependent metrics.
If engagement_per_1k_subs is comparable or above industry norm for that tier, say so.

RULE 4 — CONTENT DECAY & CATALOG VALUE:
Use content_decay_by_age buckets (0_to_30d, 31_to_90d, 91_to_180d, over_180d).
Use decay_180d_retention_pct and decay_interpretation verbatim as the basis.
For channels where licensing or B2B is an opportunity, state explicitly whether the catalog
is evergreen (high retention %) or launch-dependent (low retention %) — this determines
whether back-catalog licensing is viable.

RULE 5 — SUB-CHANNEL RECOMMENDATIONS NEED DEMAND EVIDENCE:
If search_demand_data.top_search_queries_used is available, cite those actual queries as evidence
of real audience demand. Do not invent demand figures.
If data is thin, label recommendations as: "hypothesis — validate with keyword research before committing."
The difference between a recommendation and a guess is one sentence of evidence.

RULE 6 — CROSS-PLATFORM SOCIAL CONTEXT (if cross_platform_social_data is present):
If TikTok, Instagram, or Reddit data is included, weave it into the brief naturally — do NOT
add a separate social section. Instead:
- In Executive Summary: note cross-platform presence as context (e.g., "1.2M YouTube subs with
  a growing 300K Instagram following suggests untapped visual content potential").
- In Growth Opportunities: if a social platform shows asymmetric audience size, flag it as an
  opportunity or risk. Instagram/TikTok follower-to-subscriber ratio below 0.3x = under-exploited.
- In Risk Assessment: if Reddit sentiment data shows negative patterns, flag brand safety risk.
- In the 90-Day Action Plan: include 1-2 cross-platform actions if the data supports them.
Do not fabricate social metrics. If data says "not_available," state that gap explicitly.

RULE 7 — AUDIENCE GEOGRAPHY (if audience_geography_estimate is present):
This is a PROXY ESTIMATE — always caveat it as "estimated" or "directional."
- In Executive Summary: include one sentence like "Estimated ~X% US domestic audience (proxy-based)."
- In Monetization: US-heavy audiences command higher CPMs ($7-12) vs global mixed ($2-5).
  If CPC data is also available, cross-reference: high US CPC + high US audience estimate = strong
  sponsor value signal.
- In Risk Assessment: if confidence_level is "low" or "directional," flag geography uncertainty
  as a data gap that would benefit from direct YouTube Analytics access.
Never present the estimate as verified data. The phrase "proxy-based estimate" must appear at
least once when citing geography figures.

═══════════════════════════════════════════════════
Write a sharp, opinionated brief. Use real numbers. Every sentence earns its place.
Flag data gaps honestly — admitting what you don't know is more credible than faking certainty.

STRUCTURE (use these exact headings):

## Executive Summary
3-4 sentences. Lead with the single most important insight. Include subscriber count context.

## Channel Health Assessment
Performance trajectory, engagement analysis per Rules 1+3, upload velocity.
If SocialBlade data is available, weave in growth grade + trajectory (accelerating/steady/decelerating).

## Top 3 Growth Opportunities
Ranked by impact. Each must cite at least one specific data point from the context.
Flag confidence level: DATA-BACKED / DIRECTIONAL / HYPOTHESIS.

## Sub-Channel & Expansion Recommendations
2-3 concepts with: name, concept, target audience, demand evidence (cite search queries or label as hypothesis).

## Competitor Landscape
Use normalized metrics per Rule 3. Note threat levels with reasoning.

## White Space Map
Tie content gaps to search_demand_data queries where available.

## Catalog & Decay Assessment
Use content_decay_by_age and decay_interpretation. State clearly:
is the back catalog an asset (evergreen) or a liability (launch-dependent)?
What does decay_180d_retention_pct imply for licensing, B2B, or long-tail monetization?

## 90-Day Action Plan
Concrete week-by-week priorities. Specific, not generic.

## Risk Assessment
Top 3 risks with specific mitigation for each.

## Data Confidence Notes
One short paragraph flagging which assertions are strongly data-backed (YouTube API + DataForSEO + SocialBlade)
vs directional estimates vs hypotheses that need further validation.
Be specific about what additional data would most improve the next brief."""
    return claude_call(_client, prompt, max_tokens=4500)


@st.cache_data(ttl=3600, show_spinner=False)
def claude_comprehensive_brief(_client, full_context_json):
    prompt = f"""You are a senior multi-platform digital strategy consultant writing a comprehensive intelligence brief.

This brief synthesizes data from MULTIPLE platforms: YouTube, TikTok, Instagram, Reddit, and social listening signals.

FULL CONTEXT DATA (all platforms):
{full_context_json}

═══════════════════════════════════════════════════
MANDATORY RULES
═══════════════════════════════════════════════════

RULE 1 — CROSS-PLATFORM COHERENCE:
Every recommendation must consider multi-platform implications.
A YouTube strategy that ignores TikTok/Instagram audience is incomplete.
A short-form recommendation must address TikTok vs Reels vs Shorts cannibalization.

RULE 2 — EVIDENCE HIERARCHY:
- YouTube API data = high confidence (first-party metrics)
- Instagram profile data = moderate confidence (point-in-time snapshot, engagement rate from recent posts)
- TikTok profile data = moderate confidence (point-in-time snapshot)
- Reddit listening = directional (public sentiment, not representative)
- Inferred insights = hypothesis (label clearly)
Never treat Reddit sentiment as statistically representative. It is signal, not census.
Instagram engagement rates above 3% are strong; above 6% are exceptional. Use these benchmarks.

RULE 3 — PLATFORM-SPECIFIC METRICS:
Each platform has its own benchmark norms. Do not compare raw numbers across platforms.
Instead compare: relative engagement rates, growth velocity, content-to-audience fit.
Follower-to-subscriber ratios reveal platform investment: below 0.3x = under-exploited.

RULE 4 — SHORT-FORM ECOSYSTEM:
TikTok, Instagram Reels, and YouTube Shorts form a connected short-form ecosystem.
Address them as a coordinated strategy, not three separate channels.
Content can flow between them but each platform rewards different signals (audio trends on TikTok,
visual polish on Reels, discovery on Shorts). State clearly how the creator should differentiate.

═══════════════════════════════════════════════════
STRUCTURE (use these exact headings):

## Executive Summary — Multi-Platform
5-6 sentences. The single most important cross-platform insight. Platform presence overview. Key opportunity.

## Platform Health Matrix
For each active platform (YouTube, TikTok, Instagram, Reddit), assess:
- Performance grade (A/B/C/D/F)
- Growth trajectory
- Audience engagement quality
- Content-platform fit
For Instagram specifically: note engagement rate vs benchmarks, Reels adoption, business account features.

## Cross-Platform Audience Intelligence
- Who is the audience across platforms? Same people or different segments?
- Where does the brand have the strongest emotional connection?
- Instagram audience vs YouTube audience — demographic and interest differences
- Reddit perception vs self-presentation gap analysis
- Demographic signals from all sources

## Short-Form Ecosystem Strategy
- How should TikTok, Instagram Reels, and YouTube Shorts work together?
- What gets created natively per short-form platform vs repurposed?
- Cannibalization risk assessment
- Audio/trend strategy per platform

## Social Listening Summary
- Overall brand sentiment (Reddit + any other signals)
- Key themes, criticisms, praise patterns
- Brand safety assessment
- Controversy or PR risk flags

## Integrated Growth Strategy
Top 5 recommendations that span platforms. Each must:
- State which platforms are involved
- Cite specific evidence
- Flag confidence level: DATA-BACKED / DIRECTIONAL / HYPOTHESIS

## Content Ecosystem Plan
How content should flow between platforms:
- What gets created natively per platform
- What gets repurposed and how
- Platform-specific format recommendations
- Posting cadence per platform

## Monetization Across Platforms
- YouTube: sponsorship value, CPM, CPC data if available
- Instagram: brand deal readiness (engagement rate, follower quality, business account features), Reels bonus potential, shopping/affiliate readiness
- TikTok: creator fund readiness, brand deal potential
- Cross-platform brand deal packaging: what's the combined value proposition for a sponsor across YT + IG + TT?

## 90-Day Multi-Platform Action Plan
Week-by-week priorities across ALL platforms. Specific, not generic.

## Risk Assessment
Top 5 risks spanning all platforms. Each with specific mitigation.

## Data Confidence Notes
Which assertions are API-verified vs directional vs hypothetical.
What additional data would most improve the next brief."""
    return claude_call(_client, prompt, max_tokens=5000)


# ─────────────────────────────────────────────────────────
# CHART BASE STYLE — TACTICAL
# ─────────────────────────────────────────────────────────
PLOT_BASE = dict(
    plot_bgcolor='#020c0e',
    paper_bgcolor='#050f12',
    font_color='#c8f0ea',
    font=dict(family='Share Tech Mono, monospace', size=11),
    margin=dict(t=45, b=20, l=20, r=20),
    title_font=dict(family='Orbitron, monospace', size=12, color='#00d4b4'),
    xaxis=dict(gridcolor='#0d3530', linecolor='#0d3530', tickcolor='#5a8a82'),
    yaxis=dict(gridcolor='#0d3530', linecolor='#0d3530', tickcolor='#5a8a82'),
)

PLOT_PURPLE = dict(
    **{k: v for k, v in PLOT_BASE.items() if k != 'title_font'},
    title_font=dict(family='Orbitron, monospace', size=12, color='#a855f7'),
)

PLOT_AMBER = dict(
    **{k: v for k, v in PLOT_BASE.items() if k != 'title_font'},
    title_font=dict(family='Orbitron, monospace', size=12, color='#f59e0b'),
)


# ─────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────
st.markdown("""
<div style="border-bottom:1px solid #0d3530;padding-bottom:1rem;margin-bottom:1.5rem;position:relative;">
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
    <span class="status-live"></span>
    <span style="font-family:'Orbitron',monospace;font-size:0.6rem;color:#5a8a82;letter-spacing:0.3em;text-transform:uppercase;">
      SYSTEM ONLINE // MULTI-PLATFORM INTEL FEED ACTIVE
    </span>
  </div>
  <div style="font-family:'Orbitron',monospace;font-size:1.8rem;font-weight:900;
              color:#00d4b4;letter-spacing:0.12em;
              text-shadow:0 0 30px rgba(0,212,180,0.5),0 0 60px rgba(0,212,180,0.2);">
    ▸ CHANNEL INTELLIGENCE SYSTEM
  </div>
  <div style="font-family:'Share Tech Mono',monospace;font-size:0.75rem;color:#5a8a82;
              margin-top:6px;letter-spacing:0.08em;">
    YOUTUBE &nbsp;/&nbsp; SOCIAL &nbsp;/&nbsp; LISTENING &nbsp;/&nbsp; STRATEGIC BRIEF
  </div>
  <div style="position:absolute;top:0;right:0;font-family:'Orbitron',monospace;
              font-size:0.55rem;color:#2a5550;letter-spacing:0.2em;">
    v2.0 // MULTI-PLATFORM
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────
# LANDING STATE
# ─────────────────────────────────────────────────────────
if not analyze_btn:
    st.markdown("""
<div style="border:1px solid #0d3530;border-left:3px solid #00d4b4;padding:1rem 1.5rem;
            background:#050f12;font-family:'Share Tech Mono',monospace;font-size:0.82rem;
            color:#5a8a82;margin-bottom:2rem;">
  <span class="status-live"></span>
  AWAITING ORDERS — Input API credentials and target channel identifiers in the left panel. Engage analysis when ready.
</div>

<div style="font-family:'Orbitron',monospace;font-size:0.6rem;color:#2a5550;
            letter-spacing:0.3em;text-transform:uppercase;margin-bottom:1rem;
            border-bottom:1px dashed #0d3530;padding-bottom:8px;">
  ▸ INTELLIGENCE LAYERS // OPERATIONAL OVERVIEW
</div>

<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:1rem;">

  <div style="background:#050f12;border:1px solid #0d3530;border-top:2px solid #00d4b4;
              padding:1.2rem;clip-path:polygon(0 0,calc(100% - 10px) 0,100% 10px,100% 100%,10px 100%,0 calc(100% - 10px));">
    <div style="font-family:'Orbitron',monospace;font-size:0.7rem;color:#00d4b4;letter-spacing:0.15em;margin-bottom:8px;">📺 YOUTUBE</div>
    <div style="font-size:0.72rem;color:#5a8a82;line-height:1.6;">
      Performance metrics, content DNA, sponsor detection, audience intelligence, competitor mapping, thumbnail analysis
    </div>
    <div style="margin-top:10px;font-size:0.6rem;color:#2a5550;">7 SUB-MODULES</div>
  </div>

  <div style="background:#050f12;border:1px solid #2e1065;border-top:2px solid #a855f7;
              padding:1.2rem;clip-path:polygon(0 0,calc(100% - 10px) 0,100% 10px,100% 100%,10px 100%,0 calc(100% - 10px));">
    <div style="font-family:'Orbitron',monospace;font-size:0.7rem;color:#a855f7;letter-spacing:0.15em;margin-bottom:8px;">🌐 SOCIAL</div>
    <div style="font-size:0.72rem;color:#5a8a82;line-height:1.6;">
      TikTok profile analysis, Instagram intelligence, Reddit presence mapping, cross-platform comparison
    </div>
    <div style="margin-top:10px;font-size:0.6rem;color:#2a5550;">TIKTOK + INSTAGRAM + REDDIT</div>
  </div>

  <div style="background:#050f12;border:1px solid rgba(245,158,11,0.2);border-top:2px solid #f59e0b;
              padding:1.2rem;clip-path:polygon(0 0,calc(100% - 10px) 0,100% 10px,100% 100%,10px 100%,0 calc(100% - 10px));">
    <div style="font-family:'Orbitron',monospace;font-size:0.7rem;color:#f59e0b;letter-spacing:0.15em;margin-bottom:8px;">👂 LISTENING</div>
    <div style="font-size:0.72rem;color:#5a8a82;line-height:1.6;">
      Reddit sentiment analysis, brand perception, controversy detection, audience demand signals, brand safety scoring
    </div>
    <div style="margin-top:10px;font-size:0.6rem;color:#2a5550;">REDDIT DEEP LISTEN</div>
  </div>

  <div style="background:#050f12;border:1px solid #0d3530;border-top:2px solid #ff3a2d;
              padding:1.2rem;clip-path:polygon(0 0,calc(100% - 10px) 0,100% 10px,100% 100%,10px 100%,0 calc(100% - 10px));">
    <div style="font-family:'Orbitron',monospace;font-size:0.7rem;color:#ff3a2d;letter-spacing:0.15em;margin-bottom:8px;">🎯 STRATEGIC BRIEF</div>
    <div style="font-size:0.72rem;color:#5a8a82;line-height:1.6;">
      YouTube-focused brief + comprehensive multi-platform intelligence brief synthesizing all data layers
    </div>
    <div style="margin-top:10px;font-size:0.6rem;color:#2a5550;">YT BRIEF + FULL BRIEF</div>
  </div>

</div>
    """, unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────────────────
# VALIDATE & INIT
# ─────────────────────────────────────────────────────────
if not yt_api_key:
    st.error("YouTube API Key is required.")
    st.stop()
if not claude_api_key:
    st.error("Claude API Key is required.")
    st.stop()

# Use session-stored values so inner buttons don't lose context
active_ch1    = st.session_state.get('ch1', channel_1)
active_limit  = st.session_state.get('vid_limit', video_limit)
active_cutoff = st.session_state.get('shorts_cutoff', shorts_cutoff)
active_geo    = st.session_state.get('estimate_geo', estimate_geo)
active_tiktok = st.session_state.get('tiktok_handle', tiktok_handle)
active_reddit = st.session_state.get('reddit_terms', reddit_search_terms)
active_ig     = st.session_state.get('ig_handle', instagram_handle)
active_social = st.session_state.get('enable_social', enable_social)

if not active_ch1.strip():
    st.error("Please enter at least one channel.")
    st.stop()

claude_client  = anthropic.Anthropic(api_key=claude_api_key)
has_dataforseo = bool(dataforseo_login and dataforseo_password)
has_socialblade = bool(socialblade_client_id and socialblade_token)
has_tiktok     = active_social and bool(active_tiktok and active_tiktok.strip())
has_reddit     = active_social and bool(active_reddit and active_reddit.strip())
has_instagram  = active_social and bool(active_ig and active_ig.strip())

# ─────────────────────────────────────────────────────────
# LOAD CHANNEL DATA
# ─────────────────────────────────────────────────────────
channel_data = {}
with st.spinner(f"Loading {active_ch1}…"):
    result = get_channel_info(yt_api_key, active_ch1)
    if not result:
        st.error(f"Could not find: **{active_ch1}** — check the handle or URL.")
        st.stop()
    ch_info, ch_id = result
    ch_name = ch_info['snippet']['title']
    channel_data[ch_name] = {
        'info':       ch_info,
        'channel_id': ch_id,
        'videos':     get_channel_videos(yt_api_key, ch_id, active_limit)
    }

if not channel_data:
    st.error("No channel loaded successfully.")
    st.stop()


# ─────────────────────────────────────────────────────────
# SHORTS DETECTION HELPER (used across tabs)
# ─────────────────────────────────────────────────────────
def detect_short(row):
    dur_secs = (row.get('duration_min') or 0) * 60
    title    = str(row.get('title','')).lower()
    tags_str = ' '.join(row.get('tags', [])).lower() if row.get('tags') else ''
    if dur_secs <= active_cutoff:
        return True
    if '#shorts' in title or '#short' in title:
        return True
    if '#shorts' in tags_str or '#short' in tags_str:
        return True
    return False


# ═══════════════════════════════════════════════════════════
# TOP-LEVEL TABS
# ═══════════════════════════════════════════════════════════
main_tab_yt, main_tab_social, main_tab_listen, main_tab_brief = st.tabs([
    "📺 YOUTUBE",
    "🌐 SOCIAL",
    "👂 LISTENING",
    "🎯 STRATEGIC BRIEF"
])


# ═══════════════════════════════════════════════════════════
# ███ TAB 1 — YOUTUBE (with subtabs)
# ═══════════════════════════════════════════════════════════
with main_tab_yt:
    yt_sub1, yt_sub2, yt_sub3, yt_sub4, yt_sub5, yt_sub6 = st.tabs([
        "📊 Performance",
        "📱 Shorts",
        "📝 Content Analysis",
        "💰 Sponsorships",
        "👁 Audience & Visual Intel",
        "🔍 Competitors & White Space",
    ])

    # ═══════════════════════════════════════════════════════
    # YT SUB-TAB 1 — PERFORMANCE
    # ═══════════════════════════════════════════════════════
    with yt_sub1:
        for ch_name, data in channel_data.items():
            info  = data['info']
            stats = info.get('statistics', {})
            sn    = info.get('snippet', {})
            vids  = data['videos']

            subs        = int(stats.get('subscriberCount', 0))
            total_views = int(stats.get('viewCount', 0))
            total_vids  = int(stats.get('videoCount', 0))
            avg_views   = int(sum(v['views'] for v in vids) / max(len(vids), 1))
            avg_eng     = sum((v['likes']+v['comments'])/max(v['views'],1) for v in vids) / max(len(vids),1)

            st.markdown(f"""
<div class="ch-header" data-label="TARGET ACQUIRED">
  <div style="font-family:'Orbitron',monospace;font-size:0.55rem;color:#5a8a82;letter-spacing:0.3em;margin-bottom:6px;">
    ▸ CHANNEL PROFILE // PERFORMANCE ASSESSMENT
  </div>
  <div class="ch-name">⬡ {ch_name}</div>
  <div class="ch-sub">
    HANDLE: {sn.get('customUrl','N/A')} &nbsp;|&nbsp;
    ESTABLISHED: {sn.get('publishedAt','')[:10]} &nbsp;|&nbsp;
    REGION: {sn.get('country','N/A')}
  </div>
</div>""", unsafe_allow_html=True)

            c1,c2,c3,c4,c5 = st.columns(5)
            c1.metric("Subscribers",     fmt_num(subs))
            c2.metric("Total Views",     fmt_num(total_views))
            c3.metric("Total Videos",    f"{total_vids:,}")
            c4.metric("Avg Views/Video", fmt_num(avg_views))
            c5.metric("Avg Engagement",  f"{avg_eng*100:.2f}%")

            # ── PANEL: SocialBlade growth intelligence ─────────
            if has_socialblade:
                st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
                st.markdown("<div class='section-label'>▸ GROWTH VELOCITY // SOCIALBLADE INTELLIGENCE "
                            "<span class='api-badge' style='background:#f97316;color:#000;'>SOCIALBLADE</span>"
                            "</div>", unsafe_allow_html=True)

                handle = sn.get('customUrl', ch_name).lstrip('@')
                with st.spinner("Fetching SocialBlade growth data…"):
                    sb_raw = get_socialblade_data(socialblade_client_id, socialblade_token, handle)
                    sb     = parse_socialblade(sb_raw)
                    if sb_raw:
                        st.session_state[f'sb_{ch_name}'] = sb_raw

                if sb:
                    g1, g2, g3, g4, g5 = st.columns(5)
                    grade = str(sb.get('grade', 'N/A'))
                    grade_color = sb.get('grade_color_sb') or (
                        '#00d4b4' if grade[0] in ('A','S') else
                        '#f59e0b' if grade[0] == 'B' else '#ff3a2d'
                    )
                    g1.markdown(f"<div style='text-align:center'><div style='font-family:Orbitron,monospace;"
                                f"font-size:2rem;color:{grade_color};text-shadow:0 0 12px {grade_color}'>"
                                f"{grade}</div><div style='font-size:0.65rem;color:#5a8a82;letter-spacing:0.1em'>"
                                f"SB GRADE</div></div>", unsafe_allow_html=True)
                    g2.metric("Subs +1 Day",  f"{sb['subs_1d']:+,.0f}")
                    g3.metric("Subs +7 Days", f"{sb['subs_7d']:+,.0f}")
                    g4.metric("Subs +30 Days",f"{sb['subs_30d']:+,.0f}")
                    if sb['earnings_min'] is not None:
                        g5.metric("Est. Monthly Earn.",
                                  f"${sb['earnings_min']:,.0f}–${sb['earnings_max']:,.0f}")
                    else:
                        g5.metric("Avg Daily Subs", f"{sb['avg_daily_subs']:,.0f}")

                    history = sb.get('history', [])
                    if history:
                        st.markdown("<br>", unsafe_allow_html=True)
                        df_h = pd.DataFrame(history)
                        df_h['date'] = pd.to_datetime(df_h['date'])
                        df_h = df_h.sort_values('date')

                        col_h1, col_h2 = st.columns(2)
                        with col_h1:
                            fig_subs = px.area(df_h, x='date', y='subscribers',
                                               title='Subscriber Trajectory',
                                               labels={'subscribers':'Subscribers','date':''})
                            fig_subs.update_traces(line_color='#00d4b4', fillcolor='rgba(0,212,180,0.1)')
                            fig_subs.update_layout(**PLOT_BASE, height=280)
                            fig_subs.update_xaxes(showgrid=False)
                            fig_subs.update_yaxes(gridcolor='#0d3530')
                            st.plotly_chart(fig_subs, use_container_width=True)

                        with col_h2:
                            df_h['daily_gain'] = df_h['subscribers'].diff().fillna(0)
                            fig_vel = px.bar(df_h.tail(30), x='date', y='daily_gain',
                                             title='Daily Subscriber Velocity (last 30 days)',
                                             labels={'daily_gain':'Subs Gained','date':''})
                            fig_vel.update_traces(marker_color=df_h.tail(30)['daily_gain'].apply(
                                lambda x: '#00d4b4' if x >= 0 else '#ff3a2d').tolist())
                            fig_vel.update_layout(**PLOT_BASE, height=280)
                            fig_vel.update_xaxes(showgrid=False)
                            fig_vel.update_yaxes(gridcolor='#0d3530')
                            st.plotly_chart(fig_vel, use_container_width=True)
                else:
                    st.warning("SocialBlade returned no data — check your client ID and token, or the channel handle.")
                st.markdown("</div>", unsafe_allow_html=True)

            if not vids:
                st.warning("No video data returned.")
                continue

            df = pd.DataFrame(vids)
            df['published_at'] = pd.to_datetime(df['published_at'], utc=True)
            df = df.sort_values('published_at')
            df['date'] = df['published_at'].dt.date

            df['is_short'] = df.apply(detect_short, axis=1)
            df_shorts = df[df['is_short']].copy()
            df        = df[~df['is_short']].copy()

            n_shorts = len(df_shorts)
            n_long   = len(df)
            if n_shorts > 0:
                st.info(f"📱 **{n_shorts} Shorts detected** and separated from long-form analysis. "
                        f"Long-form videos: {n_long}. See the **📱 Shorts** tab for Shorts intelligence.",
                        icon="✂️")

            # ── PANEL: Views timeline ──────────────────────────
            st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='section-label'>▸ VIEW PERFORMANCE // UPLOAD HISTORY</div>", unsafe_allow_html=True)
            df30 = df.tail(30).copy()
            fig_v = px.bar(df30, x='date', y='views',
                           title=f"Views Per Video — last {min(30,len(df))} uploads",
                           color='views', color_continuous_scale='Teal',
                           labels={'views':'Views','date':''},
                           custom_data=['title','url'])
            fig_v.update_traces(
                hovertemplate="<b>%{customdata[0]}</b><br>Views: %{y:,}<br><i>Click bar to open video</i><extra></extra>"
            )
            fig_v.update_layout(**PLOT_BASE, height=320, showlegend=False, coloraxis_showscale=False)
            fig_v.update_xaxes(showgrid=False)
            fig_v.update_yaxes(gridcolor='#0d3530')
            sel_v = st.plotly_chart(fig_v, use_container_width=True,
                                    on_select="rerun", key=f"fig_v_{ch_name}")
            if sel_v and sel_v.selection and sel_v.selection.get('points'):
                pt = sel_v.selection['points'][0]
                cd = pt.get('customdata', [])
                if len(cd) >= 2 and cd[1]:
                    st.link_button(f"▶ Watch: {str(cd[0])[:60]}…", cd[1],
                                   use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # ── PANEL: Top videos + upload cadence ────────────
            st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='section-label'>▸ TOP ASSETS // UPLOAD CADENCE</div>", unsafe_allow_html=True)
            col_l, col_r = st.columns(2)
            with col_l:
                top10 = df.nlargest(10,'views')[['title','url','views','likes','comments','duration_min']].copy()
                top10['title'] = top10['title'].str[:50]
                top10.columns  = ['Title','Watch','Views','Likes','Comments','Mins']
                st.caption("TOP 10 VIDEOS BY VIEWS — click ▶ to watch")
                st.dataframe(
                    top10,
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "Watch": st.column_config.LinkColumn(
                            "▶", display_text="▶ Watch",
                            help="Open video in YouTube"
                        )
                    }
                )

            with col_r:
                df['week'] = df['published_at'].dt.to_period('W').astype(str)
                weekly = df.groupby('week').size().reset_index(name='count').tail(24)
                fig_w = px.bar(weekly, x='week', y='count',
                               title='Upload Frequency (Weekly)', labels={'count':'Videos','week':''})
                fig_w.update_traces(marker_color='#005a4e')
                fig_w.update_layout(**PLOT_BASE, height=300)
                fig_w.update_xaxes(showgrid=False, showticklabels=False)
                fig_w.update_yaxes(gridcolor='#0d3530')
                st.plotly_chart(fig_w, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # ── PANEL: Engagement scatter ──────────────────────
            st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='section-label'>▸ ENGAGEMENT MAPPING // VIEWS vs LIKES vs COMMENTS</div>", unsafe_allow_html=True)
            fig_e = px.scatter(df, x='views', y='likes', size='comments', color='duration_min',
                               title='Engagement vs Views  (bubble = comments · color = duration)',
                               color_continuous_scale='Teal',
                               labels={'views':'Views','likes':'Likes','duration_min':'Duration (min)'},
                               custom_data=['title','url'])
            fig_e.update_traces(
                hovertemplate="<b>%{customdata[0]}</b><br>Views: %{x:,}  Likes: %{y:,}<br><i>Click to open video</i><extra></extra>"
            )
            fig_e.update_layout(**PLOT_BASE, height=360)
            fig_e.update_xaxes(gridcolor='#0d3530')
            fig_e.update_yaxes(gridcolor='#0d3530')
            sel_e = st.plotly_chart(fig_e, use_container_width=True,
                                    on_select="rerun", key=f"fig_e_{ch_name}")
            if sel_e and sel_e.selection and sel_e.selection.get('points'):
                pt = sel_e.selection['points'][0]
                cd = pt.get('customdata', [])
                if len(cd) >= 2 and cd[1]:
                    st.link_button(f"▶ Watch: {str(cd[0])[:60]}…", cd[1],
                                   use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # ── PANEL: Audience Geography Estimation ──────────
            if active_geo:
                st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
                st.markdown("<div class='section-label'>▸ AUDIENCE GEOGRAPHY // PROXY ESTIMATION "
                            "<span class='api-badge badge-claude'>CLAUDE</span>"
                            "<span class='api-badge badge-yt'>YT API</span></div>", unsafe_allow_html=True)
                st.caption("⚠ DIRECTIONAL ESTIMATE — based on comment language, upload timing, and keyword signals. Not verified analytics.")

                with st.spinner("Collecting geography signals…"):
                    # Fetch comments for language analysis (sample from top videos)
                    geo_comments = []
                    top_by_views = sorted(vids, key=lambda x: x['views'], reverse=True)
                    for v_item in top_by_views[:8]:
                        c_batch = get_top_comments(yt_api_key, v_item['video_id'], max_comments=25)
                        geo_comments.extend(c_batch)

                    geo_signals = collect_geography_signals(
                        yt_api_key,
                        data['info'],
                        vids,
                        _comment_sample=geo_comments
                    )

                    # Get CPC context if available
                    geo_cpc_ctx = 'not_available'
                    if has_dataforseo:
                        geo_tags = [t for t, _ in Counter(
                            tag for v_item in vids for tag in v_item.get('tags', [])).most_common(6)]
                        if geo_tags:
                            geo_cpc = dataforseo_keyword_cpc(dataforseo_login, dataforseo_password, tuple(geo_tags))
                            if geo_cpc:
                                geo_cpc_ctx = json.dumps(geo_cpc, default=str)

                with st.spinner("Claude is estimating audience geography…"):
                    geo_estimate = claude_geography_estimation(
                        claude_client,
                        json.dumps(geo_signals, default=str),
                        geo_cpc_ctx,
                        ch_name
                    )

                if geo_estimate:
                    # Store for brief context
                    st.session_state[f'geo_{ch_name}'] = geo_estimate
                    st.session_state[f'geo_signals_{ch_name}'] = geo_signals

                    us_pct = geo_estimate.get('estimated_us_domestic_pct', 0)
                    intl_pct = 100 - us_pct
                    conf = geo_estimate.get('confidence_level', 'directional')
                    conf_color = '#00d4b4' if conf == 'moderate' else '#f59e0b' if conf == 'low' else '#5a8a82'

                    # Main metric row
                    g1, g2, g3, g4 = st.columns(4)
                    g1.metric("Est. US Domestic", f"{us_pct}%")
                    g2.metric("Est. International", f"{intl_pct}%")
                    g3.metric("English-Speaking Total",
                              f"{geo_estimate.get('english_speaking_total_pct', 'N/A')}%")
                    g4.markdown(f"<div style='text-align:center;padding:0.3rem'>"
                                f"<div style='font-family:Share Tech Mono,monospace;font-size:1rem;"
                                f"color:{conf_color};text-transform:uppercase'>"
                                f"{conf}</div>"
                                f"<div style='font-size:0.55rem;color:#5a8a82;letter-spacing:0.1em'>CONFIDENCE</div>"
                                f"</div>", unsafe_allow_html=True)

                    # Donut chart — US vs International
                    col_chart, col_detail = st.columns([1.2, 1])
                    with col_chart:
                        regions = geo_estimate.get('estimated_regions', [])
                        if regions:
                            reg_df = pd.DataFrame(regions)
                            fig_geo = px.pie(reg_df, values='pct', names='region',
                                             title='Estimated Audience Geography',
                                             hole=0.45,
                                             color_discrete_sequence=[
                                                 '#00d4b4', '#007a68', '#005a4e',
                                                 '#003d35', '#f59e0b', '#ff3a2d',
                                                 '#a855f7', '#5a8a82'])
                            fig_geo.update_layout(**PLOT_BASE, height=300)
                            fig_geo.update_traces(textinfo='label+percent',
                                                  textfont_size=10,
                                                  textfont_color='#c8f0ea')
                            st.plotly_chart(fig_geo, use_container_width=True)

                    with col_detail:
                        st.caption("MARKET CLASSIFICATION")
                        market = geo_estimate.get('market_classification', 'N/A')
                        st.info(market)

                        st.caption("PRIMARY MARKET")
                        st.markdown(f"<span class='pill'>▸ {geo_estimate.get('primary_market', 'N/A')}</span>",
                                    unsafe_allow_html=True)

                        st.caption("ADVERTISER IMPLICATIONS")
                        st.info(geo_estimate.get('advertiser_implications', 'N/A'))

                        st.caption("KEY SIGNALS USED")
                        for sig in geo_estimate.get('key_signals_used', []):
                            st.markdown(f"<span class='pill'>◇ {sig}</span>", unsafe_allow_html=True)

                    # Underlying signal data in expander
                    with st.expander("▸ Raw proxy signals"):
                        sig_a, sig_b = st.columns(2)
                        with sig_a:
                            st.caption("COMMENT LANGUAGE DISTRIBUTION")
                            lang_dist = geo_signals.get('comment_language_distribution', {})
                            if lang_dist:
                                lang_df = pd.DataFrame(list(lang_dist.items()), columns=['Language', 'Pct'])
                                lang_df = lang_df.sort_values('Pct', ascending=False)
                                fig_lang = px.bar(lang_df, x='Pct', y='Language', orientation='h',
                                                  title=f"Comment Language ({geo_signals.get('comments_analyzed', 0)} analyzed)",
                                                  color='Pct', color_continuous_scale='Teal')
                                fig_lang.update_layout(**PLOT_BASE, height=220, showlegend=False, coloraxis_showscale=False)
                                fig_lang.update_xaxes(showgrid=False)
                                fig_lang.update_yaxes(gridcolor='#0d3530')
                                st.plotly_chart(fig_lang, use_container_width=True)
                            else:
                                st.caption("No comment data available")

                        with sig_b:
                            st.caption("UPLOAD TIMEZONE SIGNALS")
                            tz = geo_signals.get('upload_timezone_signals', {})
                            if tz:
                                tz_df = pd.DataFrame([
                                    {'Window': 'US Primetime (9a-3p ET)', 'Pct': tz.get('us_primetime_pct', 0)},
                                    {'Window': 'EU Primetime (8a-3p CET)', 'Pct': tz.get('eu_primetime_pct', 0)},
                                    {'Window': 'Asia Primetime', 'Pct': tz.get('asia_primetime_pct', 0)},
                                ])
                                fig_tz = px.bar(tz_df, x='Pct', y='Window', orientation='h',
                                                title='Upload Hour Clustering',
                                                color='Pct', color_continuous_scale='Teal')
                                fig_tz.update_layout(**PLOT_BASE, height=180, showlegend=False, coloraxis_showscale=False)
                                fig_tz.update_xaxes(showgrid=False)
                                fig_tz.update_yaxes(gridcolor='#0d3530')
                                st.plotly_chart(fig_tz, use_container_width=True)

                            st.caption("CHANNEL METADATA")
                            st.markdown(f"<span class='pill'>Country: {geo_signals.get('channel_country', 'N/A')}</span> "
                                        f"<span class='pill'>Language: {geo_signals.get('default_language', 'N/A')}</span> "
                                        f"<span class='pill'>English titles: {geo_signals.get('title_language', {}).get('english_pct', 'N/A')}%</span>",
                                        unsafe_allow_html=True)

                    st.caption(geo_estimate.get('caveats', ''))

                else:
                    st.warning("Geography estimation returned no data.")
                st.markdown("</div>", unsafe_allow_html=True)


    # ═══════════════════════════════════════════════════════
    # YT SUB-TAB 2 — SHORTS INTELLIGENCE
    # ═══════════════════════════════════════════════════════
    with yt_sub2:
        for ch_name, data in channel_data.items():
            vids = data['videos']
            st.markdown(f"<div class='section-label'>▸ MODULE 02 // SHORTS INTELLIGENCE — {ch_name}</div>", unsafe_allow_html=True)
            if not vids:
                st.warning("No video data.")
                continue

            df_all = pd.DataFrame(vids)
            df_all['published_at'] = pd.to_datetime(df_all['published_at'], utc=True)
            df_all['is_short'] = df_all.apply(detect_short, axis=1)
            df_s  = df_all[df_all['is_short']].copy()
            df_lf = df_all[~df_all['is_short']].copy()

            total      = len(df_all)
            n_s        = len(df_s)
            n_lf       = len(df_lf)
            pct_shorts = round(n_s / max(total, 1) * 100, 1)

            st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='section-label'>▸ SHORTS OVERVIEW // CHANNEL MIX</div>", unsafe_allow_html=True)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Shorts",        f"{n_s}")
            c2.metric("Long-form Videos",     f"{n_lf}")
            c3.metric("Shorts % of Catalog",  f"{pct_shorts}%")
            if n_s > 0:
                avg_s_views = int(df_s['views'].mean())
                avg_lf_views = int(df_lf['views'].mean()) if n_lf > 0 else 0
                c4.metric("Avg Shorts Views",
                          fmt_num(avg_s_views),
                          delta=f"{'+' if avg_s_views > avg_lf_views else ''}{fmt_num(avg_s_views - avg_lf_views)} vs long-form")
            st.markdown("</div>", unsafe_allow_html=True)

            if n_s == 0:
                st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
                st.markdown("### No Shorts Detected")
                st.markdown("This channel does not appear to publish YouTube Shorts, "
                            "or none were returned within the analyzed video window.")
                st.markdown("</div>", unsafe_allow_html=True)
                continue

            df_s['date'] = df_s['published_at'].dt.date

            # Views bar chart
            st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='section-label'>▸ SHORTS PERFORMANCE // VIEWS</div>", unsafe_allow_html=True)
            df_s_sorted = df_s.sort_values('published_at')
            fig_sv = px.bar(df_s_sorted, x='date', y='views',
                            title=f"Shorts Views — {n_s} Shorts",
                            color='views', color_continuous_scale='Teal',
                            labels={'views': 'Views', 'date': ''},
                            custom_data=['title', 'url'])
            fig_sv.update_traces(
                hovertemplate="<b>%{customdata[0]}</b><br>Views: %{y:,}<br><i>Click to open</i><extra></extra>"
            )
            fig_sv.update_layout(**PLOT_BASE, height=300, showlegend=False, coloraxis_showscale=False)
            fig_sv.update_xaxes(showgrid=False)
            fig_sv.update_yaxes(gridcolor='#0d3530')
            st.plotly_chart(fig_sv, use_container_width=True)

            # Top shorts table
            top_s = df_s.nlargest(10, 'views')[['title', 'url', 'views', 'likes', 'comments']].copy()
            top_s['title'] = top_s['title'].str[:55]
            top_s.columns  = ['Title', 'Watch', 'Views', 'Likes', 'Comments']
            st.dataframe(top_s, hide_index=True, use_container_width=True,
                         column_config={
                             "Watch": st.column_config.LinkColumn("▶", display_text="▶ Watch")
                         })
            st.markdown("</div>", unsafe_allow_html=True)

            # Engagement comparison
            st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='section-label'>▸ ENGAGEMENT COMPARISON // SHORTS vs LONG-FORM</div>", unsafe_allow_html=True)
            if n_lf > 0:
                s_eng  = df_s[['views','likes','comments']].copy()
                lf_eng = df_lf[['views','likes','comments']].copy()
                s_eng['eng_rate']  = (s_eng['likes']  + s_eng['comments'])  / s_eng['views'].replace(0,1)
                lf_eng['eng_rate'] = (lf_eng['likes'] + lf_eng['comments']) / lf_eng['views'].replace(0,1)

                comp_df = pd.DataFrame({
                    'Type':           ['Shorts', 'Long-form'],
                    'Avg Views':      [int(df_s['views'].mean()), int(df_lf['views'].mean())],
                    'Avg Likes':      [int(df_s['likes'].mean()), int(df_lf['likes'].mean())],
                    'Avg Engagement': [f"{s_eng['eng_rate'].mean()*100:.2f}%",
                                       f"{lf_eng['eng_rate'].mean()*100:.2f}%"],
                    'Video Count':    [n_s, n_lf]
                })
                st.dataframe(comp_df, hide_index=True, use_container_width=True)

                fig_cmp = px.bar(
                    pd.DataFrame({'Format': ['Shorts', 'Long-form'],
                                  'Avg Views': [int(df_s['views'].mean()), int(df_lf['views'].mean())]}),
                    x='Format', y='Avg Views', color='Format',
                    color_discrete_map={'Shorts': '#00d4b4', 'Long-form': '#005a4e'},
                    title='Average Views: Shorts vs Long-form'
                )
                fig_cmp.update_layout(**PLOT_BASE, height=280, showlegend=False)
                fig_cmp.update_xaxes(showgrid=False)
                fig_cmp.update_yaxes(gridcolor='#0d3530')
                st.plotly_chart(fig_cmp, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Upload cadence
            st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='section-label'>▸ SHORTS CADENCE // UPLOAD FREQUENCY</div>", unsafe_allow_html=True)
            df_s['month'] = df_s['published_at'].dt.to_period('M').astype(str)
            monthly_s = df_s.groupby('month').size().reset_index(name='count').tail(18)
            fig_sc = px.bar(monthly_s, x='month', y='count',
                            title='Shorts Uploaded per Month',
                            labels={'count': 'Shorts', 'month': ''})
            fig_sc.update_traces(marker_color='#00d4b4')
            fig_sc.update_layout(**PLOT_BASE, height=260)
            fig_sc.update_xaxes(showgrid=False, showticklabels=False)
            fig_sc.update_yaxes(gridcolor='#0d3530')
            st.plotly_chart(fig_sc, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Thumbnail grid
            top_s_thumbs = [v for v in vids
                            if detect_short(v) and v.get('thumbnail_url') and v.get('views', 0) > 0]
            top_s_thumbs = sorted(top_s_thumbs, key=lambda x: x['views'], reverse=True)[:10]
            if top_s_thumbs:
                st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
                st.markdown("<div class='section-label'>▸ TOP SHORTS // THUMBNAIL PREVIEW</div>", unsafe_allow_html=True)
                st.caption("Click a thumbnail to watch the Short")
                t_cols = st.columns(5)
                for i, v in enumerate(top_s_thumbs):
                    with t_cols[i % 5]:
                        st.markdown(
                            f'<a href="{v["url"]}" target="_blank">'
                            f'<img src="{v["thumbnail_url"]}" style="width:100%;border:1px solid #0d3530;'
                            f'transition:border-color 0.2s;" '
                            f'onmouseover="this.style.borderColor=\'#00d4b4\'" '
                            f'onmouseout="this.style.borderColor=\'#0d3530\'">'
                            f'</a>', unsafe_allow_html=True)
                        st.caption(f"{v['views']:,} views")
                st.markdown("</div>", unsafe_allow_html=True)


    # ═══════════════════════════════════════════════════════
    # YT SUB-TAB 3 — CONTENT ANALYSIS
    # ═══════════════════════════════════════════════════════
    with yt_sub3:
        for ch_name, data in channel_data.items():
            vids = data['videos']
            st.markdown(f"<div class='section-label'>▸ MODULE 03 // CONTENT DNA ANALYSIS — {ch_name}</div>", unsafe_allow_html=True)
            if not vids:
                st.warning("No video data.")
                continue

            df = pd.DataFrame(vids)
            df['published_at'] = pd.to_datetime(df['published_at'], utc=True)
            df['is_short'] = df.apply(detect_short, axis=1)
            df = df[~df['is_short']].copy()

            # Scheduling charts
            st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='section-label'>▸ UPLOAD PATTERNS // SCHEDULING ANALYSIS</div>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                df['dow']  = df['published_at'].dt.day_name()
                order      = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
                day_counts = df['dow'].value_counts().reindex(order, fill_value=0)
                fig_d = px.bar(x=day_counts.index, y=day_counts.values,
                               title='Upload Day Distribution', labels={'x':'','y':'Videos'})
                fig_d.update_traces(marker_color='#007a68')
                fig_d.update_layout(**PLOT_BASE, height=280)
                fig_d.update_xaxes(showgrid=False)
                fig_d.update_yaxes(gridcolor='#0d3530')
                st.plotly_chart(fig_d, use_container_width=True)
            with col2:
                fig_dur = px.histogram(df[df['duration_min'] < 120], x='duration_min',
                                       nbins=25, title='Video Duration Distribution',
                                       labels={'duration_min':'Duration (min)'})
                fig_dur.update_traces(marker_color='#00d4b4')
                fig_dur.update_layout(**PLOT_BASE, height=280)
                fig_dur.update_xaxes(showgrid=False)
                fig_dur.update_yaxes(gridcolor='#0d3530')
                st.plotly_chart(fig_dur, use_container_width=True)

            days_span   = max((df['published_at'].max() - df['published_at'].min()).days, 1)
            vids_per_wk = round(len(vids) / (days_span / 7), 1)
            ca, cb, cc  = st.columns(3)
            ca.metric("Upload Cadence",  f"{vids_per_wk} / week")
            cb.metric("Avg Duration",    f"{round(df['duration_min'].mean(),1)} min")
            cc.metric("Median Duration", f"{round(df['duration_min'].median(),1)} min")
            st.markdown("</div>", unsafe_allow_html=True)

            # Claude AI topic analysis
            st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='section-label'>▸ CONTENT INTELLIGENCE // AI ANALYSIS "
                        "<span class='api-badge badge-claude'>CLAUDE</span></div>", unsafe_allow_html=True)

            with st.spinner("Analyzing content strategy…"):
                topic_data = claude_content_analysis(
                    claude_client,
                    json.dumps([v['title'] for v in vids]),
                    json.dumps([v['description'] for v in vids[:20]]),
                    json.dumps(list(Counter(t for v in vids for t in v.get('tags',[])).most_common(30))),
                    json.dumps([{'title':v['title'],'views':v['views'],'likes':v['likes'],
                                 'comments':v['comments'],'duration_min':v['duration_min']} for v in vids]),
                    ch_name
                )

            if topic_data:
                ta, tb = st.columns([1.2, 1])
                with ta:
                    breakdown = topic_data.get('topic_breakdown', {})
                    if breakdown:
                        fig_t = px.pie(
                            pd.DataFrame(list(breakdown.items()), columns=['Topic','Pct']),
                            values='Pct', names='Topic', title='Topic Distribution',
                            color_discrete_sequence=['#00d4b4','#007a68','#005a4e','#003d35','#00c4a4','#009980']
                        )
                        fig_t.update_layout(**PLOT_BASE, height=340)
                        st.plotly_chart(fig_t, use_container_width=True)
                with tb:
                    st.caption("CONTENT PILLARS")
                    for p in topic_data.get('content_pillars', []):
                        st.markdown(f"<span class='pill'>⬡ {p}</span>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.caption("STYLE & TONE")
                    st.info(f"{topic_data.get('content_style','')}  ·  {topic_data.get('tone','')}")
                    st.caption("TARGET AUDIENCE")
                    st.info(topic_data.get('target_audience',''))
                    if topic_data.get('upload_series'):
                        st.caption("RECURRING SERIES")
                        for s in topic_data['upload_series']:
                            st.markdown(f"<span class='pill'>↻ {s}</span>", unsafe_allow_html=True)
                    if topic_data.get('top_performing_themes'):
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.caption("TOP PERFORMING THEMES")
                        for t in topic_data['top_performing_themes']:
                            st.markdown(f"<span class='pill'>↑ {t}</span>", unsafe_allow_html=True)
                    if topic_data.get('programming_cadence_notes'):
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.caption("CADENCE NOTES")
                        st.info(topic_data['programming_cadence_notes'])
            else:
                st.warning("Content analysis returned no data — check your Claude API key.")
            st.markdown("</div>", unsafe_allow_html=True)

            # Strengths & Gaps
            if topic_data:
                st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
                st.markdown("<div class='section-label'>▸ ASSESSMENT // STRENGTHS & GAPS</div>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    st.caption("CONFIRMED STRENGTHS")
                    for s in topic_data.get('strengths', []):
                        st.success(f"✓  {s}")
                with c2:
                    st.caption("IDENTIFIED GAPS")
                    for g in topic_data.get('content_gaps', []):
                        st.warning(f"△  {g}")
                st.markdown("</div>", unsafe_allow_html=True)

            # Google Trends
            st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='section-label'>▸ SEARCH DEMAND // GOOGLE TRENDS — YOUTUBE "
                        "<span class='api-badge' style='background:#4285f4;color:#fff;'>GOOGLE TRENDS</span>"
                        "</div>", unsafe_allow_html=True)
            st.caption("12-month YouTube search interest for this channel's top topics")

            top_tags_t2 = [t for t,_ in Counter(
                t for v in vids for t in v.get('tags',[])).most_common(10)]
            stopwords_t2 = {'the','a','an','in','on','at','to','for','of','and','or','is',
                            'are','was','how','why','what','this','that','my','your','with'}
            title_words_t2 = [w for w,_ in Counter(
                w.lower() for v in vids
                for w in re.findall(r"[a-zA-Z]{5,}", v['title'])
                if w.lower() not in stopwords_t2).most_common(10)]

            trend_kws = list(dict.fromkeys(top_tags_t2[:3] + title_words_t2[:3]))[:5]

            if trend_kws:
                with st.spinner(f"Fetching Google Trends for: {', '.join(trend_kws)}…"):
                    iot_df, rq_data = get_keyword_trends(tuple(trend_kws))

                if iot_df is not None and not iot_df.empty:
                    plot_cols = [c for c in iot_df.columns if c != 'isPartial']
                    iot_plot  = iot_df[plot_cols].reset_index()

                    fig_iot = px.line(
                        iot_plot.melt(id_vars='date', value_vars=plot_cols,
                                      var_name='Keyword', value_name='Interest'),
                        x='date', y='Interest', color='Keyword',
                        title='YouTube Search Interest — Last 12 Months (100 = peak)',
                        color_discrete_sequence=['#00d4b4','#f59e0b','#818cf8','#f87171','#34d399']
                    )
                    fig_iot.update_layout(**PLOT_BASE, height=320)
                    fig_iot.update_xaxes(showgrid=False)
                    fig_iot.update_yaxes(gridcolor='#0d3530', range=[0, 105])
                    st.plotly_chart(fig_iot, use_container_width=True)

                    col_r1, col_r2 = st.columns(2)
                    with col_r1:
                        st.caption("RISING RELATED QUERIES (breakout momentum)")
                        shown = 0
                        for kw in trend_kws:
                            rising = (rq_data or {}).get(kw, {}).get('rising')
                            if rising is not None and not rising.empty:
                                for _, row in rising.head(3).iterrows():
                                    val = row.get('value', '')
                                    label = "🚀 BREAKOUT" if val == 'Breakout' else f"+{val}%"
                                    st.markdown(f"<span class='pill'>↑ {row['query']} "
                                                f"<span style='color:#f59e0b'>{label}</span></span>",
                                                unsafe_allow_html=True)
                                    shown += 1
                        if shown == 0:
                            st.caption("No rising queries detected")

                    with col_r2:
                        st.caption("TOP RELATED QUERIES (search volume)")
                        shown = 0
                        for kw in trend_kws[:2]:
                            top = (rq_data or {}).get(kw, {}).get('top')
                            if top is not None and not top.empty:
                                for _, row in top.head(4).iterrows():
                                    st.markdown(f"<span class='pill'>▸ {row['query']}</span>",
                                                unsafe_allow_html=True)
                                    shown += 1
                        if shown == 0:
                            st.caption("No related query data available")
                else:
                    st.info("Google Trends returned no data for these keywords.")
            else:
                st.info("No keywords extracted — check that the channel has tags or titles with clear topic words.")
            st.markdown("</div>", unsafe_allow_html=True)


    # ═══════════════════════════════════════════════════════
    # YT SUB-TAB 4 — SPONSORSHIPS
    # ═══════════════════════════════════════════════════════
    with yt_sub4:
        for ch_name, data in channel_data.items():
            vids = data['videos']
            st.markdown(f"<div class='section-label'>▸ MODULE 04 // SPONSOR INTELLIGENCE — {ch_name}</div>", unsafe_allow_html=True)
            if not vids:
                st.warning("No video data.")
                continue

            with st.spinner("Scanning SponsorBlock…"):
                sb_checked = min(len(vids), 20)
                sb_hits    = sum(1 for v in vids[:sb_checked] if get_sponsorblock(v['video_id']))

            st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='section-label'>▸ CROWDSOURCED DETECTION // SPONSORBLOCK DATABASE</div>", unsafe_allow_html=True)
            ca, cb, cc = st.columns(3)
            ca.metric("Sponsored Segments", f"{sb_hits} / {sb_checked} sampled")
            cb.metric("Detection Rate",     f"{sb_hits/max(sb_checked,1)*100:.0f}%")
            cc.metric("Sources",            "SponsorBlock + Claude")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='section-label'>▸ AI BRAND DETECTION // SPONSOR INTELLIGENCE "
                        "<span class='api-badge badge-claude'>CLAUDE</span></div>", unsafe_allow_html=True)
            st.caption("Scanning titles and descriptions for brand deals, promo codes, affiliate disclosures")

            with st.spinner("Scanning for sponsors…"):
                sp = claude_sponsor_analysis(
                    claude_client,
                    json.dumps([v['title'] for v in vids]),
                    json.dumps([v['description'] for v in vids]),
                    ch_name
                )

            if sp:
                col_l, col_r = st.columns(2)
                with col_l:
                    st.caption("BRANDS DETECTED")
                    for s in sp.get('sponsors_found', []) or ["None detected"]:
                        st.markdown(f"<span class='pill'>▸ {s}</span>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.caption("SPONSOR CATEGORIES")
                    for c in sp.get('sponsor_categories', []):
                        st.markdown(f"<span class='pill'>▹ {c}</span>", unsafe_allow_html=True)
                    if sp.get('promo_codes'):
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.caption("PROMO CODES")
                        for p in sp['promo_codes']:
                            st.markdown(f"<span class='pill'>🏷 {p}</span>", unsafe_allow_html=True)
                    if sp.get('affiliate_programs'):
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.caption("AFFILIATE PROGRAMS")
                        for a in sp['affiliate_programs']:
                            st.markdown(f"<span class='pill'>↗ {a}</span>", unsafe_allow_html=True)
                with col_r:
                    st.caption("AD PLACEMENT")
                    st.info(sp.get('typical_placement','N/A'))
                    st.caption("READ STYLE")
                    st.info(sp.get('ad_read_style','N/A'))
                    st.caption("ESTIMATED FREQUENCY")
                    st.info(sp.get('estimated_frequency','N/A'))
                    st.caption("MONETIZATION TIER")
                    tier = sp.get('monetization_tier','N/A')
                    if 'high' in tier.lower():
                        st.success(f"● HIGH — {tier}")
                    elif 'mid' in tier.lower():
                        st.warning(f"● MID — {tier}")
                    else:
                        st.info(f"● {tier}")
                    st.caption("BRAND FIT ASSESSMENT")
                    st.info(sp.get('brand_fit_assessment','N/A'))
                    if sp.get('self_promotion'):
                        st.caption("OWN PRODUCTS / MERCH")
                        for p in sp['self_promotion']:
                            st.markdown(f"<span class='pill'>🏷 {p}</span>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            if sp and sp.get('untapped_categories'):
                st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
                st.markdown("<div class='section-label'>▸ REVENUE OPPORTUNITY // UNTAPPED SPONSOR CATEGORIES</div>", unsafe_allow_html=True)
                cols = st.columns(3)
                for i, u in enumerate(sp.get('untapped_categories', [])):
                    cols[i % 3].success(f"▸ {u}")
                st.markdown("</div>", unsafe_allow_html=True)


    # ═══════════════════════════════════════════════════════
    # YT SUB-TAB 5 — AUDIENCE & VISUAL INTEL
    # ═══════════════════════════════════════════════════════
    with yt_sub5:
        for ch_name, data in channel_data.items():
            vids = data['videos']
            if not vids:
                st.warning("No video data.")
                continue

            top_vids    = sorted(vids, key=lambda x: x['views'], reverse=True)
            top_10      = top_vids[:10]
            bottom_10   = top_vids[-10:] if len(top_vids) > 10 else []

            # Comment Intelligence
            st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='section-label'>▸ MODULE 05a // AUDIENCE COMMENT INTELLIGENCE "
                        "<span class='api-badge badge-claude'>CLAUDE</span>"
                        "<span class='api-badge badge-yt'>YT API</span></div>", unsafe_allow_html=True)
            st.caption(f"Fetching top comments from {min(len(top_10),5)} highest-performing videos")

            with st.spinner("Fetching and analysing comments…"):
                all_comments = []
                for v in top_10[:5]:
                    comments = get_top_comments(yt_api_key, v['video_id'], max_comments=30)
                    for c in comments:
                        c['video_title'] = v['title']
                        c['video_views'] = v['views']
                    all_comments.extend(comments)

                comment_intel = claude_comment_intelligence(
                    claude_client,
                    json.dumps(all_comments[:120]),
                    ch_name
                )

            if comment_intel:
                col_a, col_b = st.columns(2)
                with col_a:
                    st.caption("RECURRING AUDIENCE QUESTIONS → VIDEO OPPORTUNITIES")
                    for q in comment_intel.get('top_questions', []):
                        with st.expander(f"▸ {q.get('question','')}"):
                            st.markdown(f"**Frequency:** {q.get('frequency','')}")
                            st.success(f"💡 Opportunity: {q.get('opportunity','')}")

                with col_b:
                    st.caption("CONTENT IDEAS DIRECTLY FROM COMMENTS")
                    for idea in comment_intel.get('top_content_ideas', []):
                        st.success(f"▸ {idea}")

                st.markdown("<br>", unsafe_allow_html=True)

                col_c, col_d = st.columns(2)
                with col_c:
                    st.caption("EMOTIONAL TRIGGERS")
                    for t in comment_intel.get('emotional_triggers', []):
                        st.markdown(f"<span class='pill'>⚡ {t}</span>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.caption("SHAREABILITY SIGNALS")
                    for s in comment_intel.get('shareability_signals', []):
                        st.markdown(f"<span class='pill'>↗ {s}</span>", unsafe_allow_html=True)

                with col_d:
                    st.caption("EXPLICIT CONTENT REQUESTS")
                    for r in comment_intel.get('content_requests', []):
                        st.warning(f"△ {r}")
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.caption("PAIN POINTS / UNMET NEEDS")
                    for p in comment_intel.get('pain_points', []):
                        st.warning(f"△ {p}")

                st.markdown("<br>", unsafe_allow_html=True)

                col_e, col_f = st.columns(2)
                with col_e:
                    st.caption("AUDIENCE PERSONAS DETECTED")
                    for persona in comment_intel.get('audience_personas', []):
                        st.info(f"→ {persona}")

                with col_f:
                    st.caption("DEMOGRAPHIC SIGNALS")
                    for d in comment_intel.get('demographic_signals', []):
                        st.markdown(f"<span class='pill'>👤 {d}</span>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.caption("CONTROVERSY ZONES")
                    for c in comment_intel.get('controversy_zones', []):
                        st.markdown(f"<span class='pill'>⚠ {c}</span>", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                st.caption("SENTIMENT SUMMARY")
                st.info(comment_intel.get('sentiment_summary', ''))

            else:
                st.warning("Comment analysis returned no data.")
            st.markdown("</div>", unsafe_allow_html=True)

            # Thumbnail Intelligence
            st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='section-label'>▸ MODULE 05b // THUMBNAIL VISUAL INTELLIGENCE "
                        "<span class='api-badge badge-claude'>CLAUDE VISION</span></div>", unsafe_allow_html=True)

            vids_with_thumbs = [v for v in vids if v.get('thumbnail_url')]
            top_thumbs    = sorted(vids_with_thumbs, key=lambda x: x['views'], reverse=True)[:10]
            bottom_thumbs = sorted(vids_with_thumbs, key=lambda x: x['views'])[:10]

            if top_thumbs:
                st.caption("TOP 10 VIDEOS BY VIEWS — THUMBNAIL REVIEW — click to watch")
                thumb_cols = st.columns(5)
                for i, v in enumerate(top_thumbs[:10]):
                    with thumb_cols[i % 5]:
                        st.markdown(
                            f'<a href="{v["url"]}" target="_blank">'
                            f'<img src="{v["thumbnail_url"]}" style="width:100%;border:1px solid #0d3530;'
                            f'transition:border-color 0.2s;" '
                            f'onmouseover="this.style.borderColor=\'#00d4b4\'" '
                            f'onmouseout="this.style.borderColor=\'#0d3530\'">'
                            f'</a>', unsafe_allow_html=True)
                        st.caption(f"{v['views']:,} views")

                if bottom_thumbs:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.caption("BOTTOM 10 VIDEOS BY VIEWS — THUMBNAIL REVIEW — click to watch")
                    b_cols = st.columns(5)
                    for i, v in enumerate(bottom_thumbs[:10]):
                        with b_cols[i % 5]:
                            st.markdown(
                                f'<a href="{v["url"]}" target="_blank">'
                                f'<img src="{v["thumbnail_url"]}" style="width:100%;border:1px solid #0d3530;'
                                f'transition:border-color 0.2s;" '
                                f'onmouseover="this.style.borderColor=\'#ff3a2d\'" '
                                f'onmouseout="this.style.borderColor=\'#0d3530\'">'
                                f'</a>', unsafe_allow_html=True)
                            st.caption(f"{v['views']:,} views")

            thumb_data = [{'title': v['title'], 'views': v['views'],
                           'likes': v['likes'], 'thumbnail_url': v['thumbnail_url'],
                           'tier': 'top'} for v in top_thumbs]
            if bottom_thumbs:
                thumb_data += [{'title': v['title'], 'views': v['views'],
                                'likes': v['likes'], 'thumbnail_url': v['thumbnail_url'],
                                'tier': 'bottom'} for v in bottom_thumbs]

            with st.spinner("Claude is analysing thumbnail patterns…"):
                thumb_intel = claude_thumbnail_intelligence(
                    claude_client,
                    json.dumps(thumb_data),
                    ch_name
                )

            if thumb_intel:
                st.markdown("<br>", unsafe_allow_html=True)
                col_a, col_b = st.columns(2)

                with col_a:
                    st.caption("HIGH PERFORMER VISUAL PATTERNS")
                    for p in thumb_intel.get('high_performer_patterns', []):
                        st.success(f"✓ {p}")
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.caption("LOW PERFORMER VISUAL PATTERNS")
                    for p in thumb_intel.get('low_performer_patterns', []):
                        st.warning(f"△ {p}")
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.caption("WINNING FORMULA")
                    st.info(thumb_intel.get('winning_formula', ''))

                with col_b:
                    st.caption("FACE STRATEGY")
                    st.info(thumb_intel.get('face_strategy', ''))
                    st.caption("TEXT STRATEGY")
                    st.info(thumb_intel.get('text_strategy', ''))
                    st.caption("COLOR PALETTE")
                    st.info(thumb_intel.get('color_palette', ''))
                    st.caption("BRAND CONSISTENCY")
                    score = thumb_intel.get('brand_consistency_score', '')
                    if 'strong' in score.lower():
                        st.success(f"● {score}")
                    elif 'weak' in score.lower():
                        st.warning(f"● {score}")
                    else:
                        st.info(f"● {score}")

                st.markdown("<br>", unsafe_allow_html=True)
                col_c, col_d = st.columns(2)
                with col_c:
                    st.caption("IMMEDIATE IMPROVEMENTS")
                    for imp in thumb_intel.get('immediate_improvements', []):
                        st.success(f"▸ {imp}")
                with col_d:
                    st.caption("CTR HYPOTHESIS")
                    st.info(thumb_intel.get('ctr_hypothesis', ''))
                    st.caption("COMPETITOR GAP")
                    st.warning(thumb_intel.get('competitor_gap', ''))

            else:
                st.warning("Thumbnail analysis returned no data.")
            st.markdown("</div>", unsafe_allow_html=True)


    # ═══════════════════════════════════════════════════════
    # YT SUB-TAB 6 — COMPETITORS & WHITE SPACE
    # ═══════════════════════════════════════════════════════
    with yt_sub6:
        st.markdown("<div class='section-label'>▸ MODULE 06 // COMPETITIVE THREAT MAPPING</div>", unsafe_allow_html=True)

        dfs_results = None
        if has_dataforseo:
            st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='section-label'>▸ LIVE SEARCH DATA // DATAFORSEO "
                        "<span class='api-badge badge-dataforseo'>DATAFORSEO</span></div>", unsafe_allow_html=True)

            ch1_name = list(channel_data.keys())[0]
            ch1_vids = channel_data[ch1_name]['videos']

            top_tags   = [t for t,_ in Counter(
                t for v in ch1_vids for t in v.get('tags',[])).most_common(25)]
            top_stats  = [{'title':v['title'],'views':v['views']}
                          for v in sorted(ch1_vids, key=lambda x: x['views'], reverse=True)[:10]]

            with st.spinner("Claude is generating competitive search intelligence…"):
                query_data = claude_generate_search_queries(
                    claude_client,
                    ch1_name,
                    json.dumps([v['title'] for v in ch1_vids[:30]]),
                    json.dumps(top_tags),
                    json.dumps(top_stats)
                )

            if query_data:
                queries = []
                dim_map = {}
                for dim in ['topic','genre','audience','adjacent']:
                    for q in query_data.get(dim, []):
                        queries.append(q)
                        dim_map[q] = dim.upper()

                st.caption(f"SEARCH QUERIES GENERATED — {len(queries)} across 4 dimensions")
                q_cols = st.columns(4)
                for i, dim in enumerate(['topic','genre','audience','adjacent']):
                    with q_cols[i]:
                        st.markdown(f"<div style='font-family:Orbitron,monospace;font-size:0.6rem;color:#5a8a82;"
                                    f"letter-spacing:0.15em;margin-bottom:4px;'>{dim.upper()}</div>",
                                    unsafe_allow_html=True)
                        for q in query_data.get(dim, []):
                            st.markdown(f"<span class='pill'>▸ {q}</span>", unsafe_allow_html=True)

                all_results = []
                seen_channels = set()
                with st.spinner(f"Running {len(queries)} searches against YouTube via DataForSEO…"):
                    for q in queries:
                        batch = dataforseo_youtube_search(dataforseo_login, dataforseo_password, q)
                        if batch:
                            for item in batch:
                                ch = item.get('channel','').strip()
                                if ch and ch.lower() != ch1_name.lower() and ch not in seen_channels:
                                    seen_channels.add(ch)
                                    item['query']     = q
                                    item['dimension'] = dim_map.get(q, '—')
                                    all_results.append(item)

                dfs_results = all_results if all_results else None
                if dfs_results:
                    st.session_state[f'dfs_results_{ch_name}'] = dfs_results

                if dfs_results:
                    df_dfs = pd.DataFrame(dfs_results)[['channel','title','url','views','dimension','query']]
                    df_dfs.columns = ['Channel','Top Video','Watch','Views','Dimension','Query']
                    df_dfs['Top Video'] = df_dfs['Top Video'].str[:50]
                    df_dfs = df_dfs.sort_values('Views', ascending=False).drop_duplicates('Channel').head(15)
                    st.caption(f"COMPETITOR CHANNELS IDENTIFIED — {len(df_dfs)} UNIQUE CHANNELS ACROSS {len(queries)} QUERIES")
                    st.dataframe(
                        df_dfs,
                        hide_index=True,
                        use_container_width=True,
                        column_config={
                            "Watch": st.column_config.LinkColumn(
                                "▶", display_text="▶ Watch",
                                help="Open video in YouTube"
                            )
                        }
                    )
                else:
                    st.warning("No results returned — check DataForSEO credentials.")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
            st.info("Add DataForSEO credentials in the sidebar for real verified competitor metrics.")
            st.markdown("</div>", unsafe_allow_html=True)

        names = list(channel_data.keys())

        def ch_summary(name, d):
            vs, s = d['videos'], d['info'].get('statistics', {})
            days  = max((pd.to_datetime(vs[0]['published_at'],utc=True) -
                         pd.to_datetime(vs[-1]['published_at'],utc=True)).days, 1) if len(vs)>1 else 1
            return {
                'name': name,
                'subscribers': s.get('subscriberCount','?'),
                'total_views':  s.get('viewCount','?'),
                'avg_views_per_video': int(sum(v['views'] for v in vs)/max(len(vs),1)),
                'upload_cadence': f"{round(len(vs)/(days/7),1)} videos/week",
                'recent_titles': [v['title'] for v in vs[:25]],
                'top_tags': [t for t,_ in Counter(
                    t for v in vs for t in v.get('tags',[])).most_common(15)]
            }

        with st.spinner("Claude is mapping the competitive landscape…"):
            comp = claude_competitor_analysis(
                claude_client,
                json.dumps(ch_summary(names[0], channel_data[names[0]])),
                None,
                json.dumps(dfs_results) if dfs_results else None
            )

        if comp:
            st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='section-label'>▸ THREAT ASSESSMENT // COMPETITOR CHANNELS "
                        "<span class='api-badge badge-claude'>CLAUDE</span></div>", unsafe_allow_html=True)
            if comp.get('competitive_position'):
                st.caption("COMPETITIVE POSITION")
                st.info(comp['competitive_position'])
            competitors = comp.get('competitor_channels', [])
            if competitors:
                icons = {'high':'🔴','medium':'🟡','low':'🟢'}
                st.dataframe(pd.DataFrame([{
                    'Threat':           icons.get(c.get('threat_level','medium').lower(),'🟡'),
                    'Channel':          c.get('name',''),
                    'Handle':           c.get('handle',''),
                    'Est. Subs':        c.get('subscribers',''),
                    'Overlap Reason':   c.get('why','')
                } for c in competitors]), hide_index=True, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='section-label'>▸ OPPORTUNITY MAPPING // WHITE SPACE & FORMATS</div>", unsafe_allow_html=True)
            col_a, col_b = st.columns(2)
            with col_a:
                st.caption("UNCLAIMED CONTENT TERRITORY")
                for t in comp.get('white_space_topics', []):
                    st.success(f"▸ {t}")
            with col_b:
                st.caption("FORMAT GAPS")
                for f in comp.get('format_opportunities', []):
                    st.markdown(f"<span class='pill'>▹ {f}</span>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                st.caption("KEY DIFFERENTIATORS")
                for d in comp.get('key_differentiators', []):
                    st.markdown(f"<span class='pill'>✦ {d}</span>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='section-label'>▸ EXPANSION INTEL // SUB-CHANNELS & AUDIENCE GROWTH</div>", unsafe_allow_html=True)
            col_a, col_b = st.columns(2)
            with col_a:
                st.caption("SUB-CHANNEL CONCEPTS")
                for sc in comp.get('subchannel_concepts', []):
                    with st.expander(f"▸ {sc.get('name','')}"):
                        st.markdown(f"**Concept:** {sc.get('concept','')}")
                        st.markdown(f"**Audience:** {sc.get('target_audience','')}")
                        st.markdown(f"**Rationale:** {sc.get('rationale','')}")
            with col_b:
                st.caption("AUDIENCE EXPANSION VECTORS")
                for a in comp.get('audience_expansion_opportunities', []):
                    st.info(f"→ {a}")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='section-label'>▸ MONETIZATION // BUSINESS EXTENSION IDEAS</div>", unsafe_allow_html=True)
            biz_cols = st.columns(2)
            for i, idea in enumerate(comp.get('business_extensions', [])):
                biz_cols[i%2].info(f"▸ {idea}")
            if comp.get('strategic_summary'):
                st.markdown("<br>", unsafe_allow_html=True)
                st.caption("STRATEGIC SUMMARY")
                st.markdown(f"> {comp.get('strategic_summary','')}")
            st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# ███ TAB 2 — SOCIAL (TikTok + Reddit presence)
# ═══════════════════════════════════════════════════════════
with main_tab_social:
    if not active_social:
        st.markdown("""
<div style="border-top:1px solid #2e1065;padding:2rem 0;text-align:center;">
  <div style="font-family:'Orbitron',monospace;font-size:0.7rem;color:#a855f7;letter-spacing:0.2em;margin-bottom:12px;">
    🌐 SOCIAL INTELLIGENCE — DISABLED
  </div>
  <div style="font-family:'Share Tech Mono',monospace;font-size:0.8rem;color:#5a8a82;max-width:500px;margin:0 auto;line-height:1.6;">
    Enable the <strong style="color:#a855f7;">Social Intelligence</strong> checkbox in the sidebar
    to activate TikTok, Instagram, and Reddit analysis layers.
  </div>
</div>""", unsafe_allow_html=True)
        st.session_state.setdefault('tiktok_profile', None)
        st.session_state.setdefault('instagram_profile', None)
        st.session_state.setdefault('reddit_posts', [])
        st.session_state.setdefault('reddit_comments', [])

    if active_social:
        social_sub1, social_sub2, social_sub3, social_sub4 = st.tabs([
            "📊 Cross-Platform Overview",
            "🎵 TikTok Intelligence",
            "📸 Instagram Intelligence",
            "🔶 Reddit Presence",
        ])

        ch1_name = list(channel_data.keys())[0]
        ch1_data = channel_data[ch1_name]
        ch1_vids = ch1_data['videos']
        ch1_stats = ch1_data['info'].get('statistics', {})
        yt_subs = int(ch1_stats.get('subscriberCount', 0))
        yt_views = int(ch1_stats.get('viewCount', 0))

        # ── Fetch social data once ──────────────────────────────
        tiktok_profile = None
        instagram_profile = None
        reddit_posts = []
        reddit_comments = []

        if has_tiktok:
            with st.spinner("Fetching TikTok profile…"):
                tiktok_profile = get_tiktok_profile_data(active_tiktok)

        if has_instagram:
            with st.spinner("Fetching Instagram profile…"):
                instagram_profile = get_instagram_profile_data(active_ig)

        # Build reddit search terms from channel name + custom terms
        reddit_queries = []
        if has_reddit:
            reddit_queries = [t.strip() for t in active_reddit.split(',') if t.strip()]
        elif ch1_name:
            reddit_queries = [ch1_name]

        if reddit_queries:
            with st.spinner("Scanning Reddit…"):
                for q in reddit_queries[:3]:  # limit to 3 queries
                    reddit_posts.extend(reddit_search_posts(q, limit=50, time_filter='year'))
                    time.sleep(1)  # respect rate limits
                    reddit_comments.extend(reddit_search_comments(q, limit=50, time_filter='year'))
                    time.sleep(1)

        # Store in session state for use in other tabs
        st.session_state['tiktok_profile'] = tiktok_profile
        st.session_state['instagram_profile'] = instagram_profile
        st.session_state['reddit_posts'] = reddit_posts
        st.session_state['reddit_comments'] = reddit_comments


        # ═══════════════════════════════════════════════════════
        # SOCIAL SUB-TAB 1 — CROSS-PLATFORM OVERVIEW
        # ═══════════════════════════════════════════════════════
        with social_sub1:
            st.markdown(f"<div class='section-label'>▸ CROSS-PLATFORM OVERVIEW // {ch1_name}</div>", unsafe_allow_html=True)

            st.markdown("<div class='social-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='section-label'>▸ PLATFORM PRESENCE MATRIX</div>", unsafe_allow_html=True)

            p1, p2, p3, p4 = st.columns(4)
            with p1:
                st.markdown(f"""
    <div style="border-top:2px solid #ff0000;border-bottom:1px solid #0d3530;padding:0.8rem 1rem;background:transparent;position:relative;">
      <div style="font-family:'Orbitron',monospace;font-size:0.6rem;color:#ff0000;letter-spacing:0.15em;margin-bottom:6px;">📺 YOUTUBE</div>
      <div style="font-family:'Share Tech Mono',monospace;font-size:1.1rem;color:#00d4b4;text-shadow:0 0 10px rgba(0,212,180,0.4);white-space:nowrap;">{fmt_num(yt_subs)} <span style="font-size:0.6rem;color:#5a8a82;">SUBS</span></div>
      <div style="margin-top:6px;font-size:0.7rem;color:#5a8a82;">{fmt_num(yt_views)} views · {len(ch1_vids)} analyzed</div>
    </div>""", unsafe_allow_html=True)

            with p2:
                if tiktok_profile:
                    tt = tiktok_profile
                    st.markdown(f"""
    <div style="border-top:2px solid #a855f7;border-bottom:1px solid #2e1065;padding:0.8rem 1rem;background:transparent;position:relative;">
      <div style="font-family:'Orbitron',monospace;font-size:0.6rem;color:#a855f7;letter-spacing:0.15em;margin-bottom:6px;">🎵 TIKTOK</div>
      <div style="font-family:'Share Tech Mono',monospace;font-size:1.1rem;color:#a855f7;text-shadow:0 0 10px rgba(168,85,247,0.4);white-space:nowrap;">{fmt_num(tt['followers'])} <span style="font-size:0.6rem;color:#5a8a82;">FOLLOWERS</span></div>
      <div style="margin-top:6px;font-size:0.7rem;color:#5a8a82;">{fmt_num(tt['likes'])} likes · {tt['videos']:,} videos</div>
    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
    <div style="border-top:2px solid #a855f7;border-bottom:1px solid #2e1065;padding:0.8rem 1rem;background:transparent;opacity:0.5;">
      <div style="font-family:'Orbitron',monospace;font-size:0.6rem;color:#a855f7;letter-spacing:0.15em;margin-bottom:6px;">🎵 TIKTOK</div>
      <div style="font-size:0.75rem;color:#5a8a82;margin-top:8px;">{'No handle provided' if not has_tiktok else 'Profile not found'}</div>
    </div>""", unsafe_allow_html=True)

            with p3:
                if instagram_profile:
                    ig = instagram_profile
                    st.markdown(f"""
    <div style="border-top:2px solid #ec4899;border-bottom:1px solid #831843;padding:0.8rem 1rem;background:transparent;position:relative;">
      <div style="font-family:'Orbitron',monospace;font-size:0.6rem;color:#ec4899;letter-spacing:0.15em;margin-bottom:6px;">📸 INSTAGRAM</div>
      <div style="font-family:'Share Tech Mono',monospace;font-size:1.1rem;color:#ec4899;text-shadow:0 0 10px rgba(236,72,153,0.4);white-space:nowrap;">{fmt_num(ig['followers'])} <span style="font-size:0.6rem;color:#5a8a82;">FOLLOWERS</span></div>
      <div style="margin-top:6px;font-size:0.7rem;color:#5a8a82;">{ig['posts']:,} posts{' · ✓ VERIFIED' if ig.get('verified') else ''}{' · 🏢 BIZ' if ig.get('is_business') else ''}</div>
    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
    <div style="border-top:2px solid #ec4899;border-bottom:1px solid #831843;padding:0.8rem 1rem;background:transparent;opacity:0.5;">
      <div style="font-family:'Orbitron',monospace;font-size:0.6rem;color:#ec4899;letter-spacing:0.15em;margin-bottom:6px;">📸 INSTAGRAM</div>
      <div style="font-size:0.75rem;color:#5a8a82;margin-top:8px;">{'No handle provided' if not has_instagram else 'Profile not found'}</div>
    </div>""", unsafe_allow_html=True)

            with p4:
                n_posts = len(reddit_posts)
                n_comments = len(reddit_comments)
                total_score = sum(p['score'] for p in reddit_posts)
                unique_subs = len(set(p['subreddit'] for p in reddit_posts)) if reddit_posts else 0
                st.markdown(f"""
    <div style="border-top:2px solid #ff4500;border-bottom:1px solid rgba(245,158,11,0.15);padding:0.8rem 1rem;background:transparent;position:relative;">
      <div style="font-family:'Orbitron',monospace;font-size:0.6rem;color:#ff4500;letter-spacing:0.15em;margin-bottom:6px;">🔶 REDDIT</div>
      <div style="font-family:'Share Tech Mono',monospace;font-size:1.1rem;color:#ff4500;text-shadow:0 0 10px rgba(255,69,0,0.4);white-space:nowrap;">{n_posts} <span style="font-size:0.6rem;color:#5a8a82;">POSTS</span></div>
      <div style="margin-top:6px;font-size:0.7rem;color:#5a8a82;">{n_comments} comments · {unique_subs} subs · {fmt_num(total_score)} karma</div>
    </div>""", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            # Claude cross-platform analysis
            if tiktok_profile or instagram_profile or reddit_posts:
                st.markdown("<div class='social-panel'>", unsafe_allow_html=True)
                st.markdown("<div class='section-label'>▸ CROSS-PLATFORM STRATEGY ASSESSMENT "
                            "<span class='api-badge badge-claude'>CLAUDE</span></div>", unsafe_allow_html=True)

                yt_context = {
                    'subscribers': yt_subs,
                    'total_views': yt_views,
                    'video_count': len(ch1_vids),
                    'avg_views': int(sum(v['views'] for v in ch1_vids)/max(len(ch1_vids),1)),
                    'top_tags': [t for t,_ in Counter(t for v in ch1_vids for t in v.get('tags',[])).most_common(10)],
                    'recent_titles': [v['title'] for v in ch1_vids[:10]]
                }
                reddit_summary = {
                    'posts_found': len(reddit_posts),
                    'comments_found': len(reddit_comments),
                    'unique_subreddits': list(set(p['subreddit'] for p in reddit_posts))[:10],
                    'top_posts': sorted(reddit_posts, key=lambda x: x['score'], reverse=True)[:5],
                    'avg_score': round(sum(p['score'] for p in reddit_posts)/max(len(reddit_posts),1), 1) if reddit_posts else 0,
                }

                with st.spinner("Generating cross-platform intelligence…"):
                    xp_analysis = claude_cross_platform_analysis(
                        claude_client,
                        json.dumps(yt_context, default=str),
                        json.dumps(tiktok_profile or {'status': 'not_available'}, default=str),
                        json.dumps(instagram_profile or {'status': 'not_available'}, default=str),
                        json.dumps(reddit_summary, default=str),
                        ch1_name
                    )

                if xp_analysis:
                    # Strategy grade
                    grade = xp_analysis.get('cross_platform_strategy_grade', 'N/A')
                    grade_letter = grade[0] if grade else '?'
                    grade_color = '#00d4b4' if grade_letter in ('A','S') else '#f59e0b' if grade_letter == 'B' else '#ff3a2d'

                    g1, g2, g3 = st.columns([1,2,2])
                    with g1:
                        st.markdown(f"<div style='text-align:center;padding:0.5rem'>"
                                    f"<div style='font-family:Orbitron,monospace;font-size:1.8rem;"
                                    f"color:{grade_color};text-shadow:0 0 14px {grade_color}'>"
                                    f"{grade_letter}</div>"
                                    f"<div style='font-size:0.55rem;color:#5a8a82;letter-spacing:0.12em'>CROSS-PLATFORM</div>"
                                    f"</div>", unsafe_allow_html=True)
                    with g2:
                        st.caption("CONTENT REPURPOSING")
                        st.info(xp_analysis.get('content_repurposing_score', 'N/A'))
                        st.caption("AUDIENCE MIGRATION POTENTIAL")
                        st.info(xp_analysis.get('audience_migration_potential', 'N/A'))
                    with g3:
                        st.caption("BIGGEST OPPORTUNITY")
                        st.success(xp_analysis.get('biggest_cross_platform_opportunity', 'N/A'))
                        st.caption("PLATFORM PRIORITY")
                        for rank, p in enumerate(xp_analysis.get('platform_priority_ranking', []), 1):
                            st.markdown(f"<span class='pill-purple'>{rank}. {p}</span>", unsafe_allow_html=True)

                    # Platform summaries
                    ps = xp_analysis.get('platform_summary', {})
                    if ps:
                        st.markdown("<br>", unsafe_allow_html=True)
                        col_a, col_b, col_c, col_d = st.columns(4)
                        for col, platform, color in [(col_a, 'youtube', '#00d4b4'), (col_b, 'tiktok', '#a855f7'), (col_c, 'instagram', '#ec4899'), (col_d, 'reddit', '#ff4500')]:
                            with col:
                                pd_data = ps.get(platform, {})
                                if pd_data:
                                    st.markdown(f"<div style='font-family:Orbitron,monospace;font-size:0.65rem;color:{color};letter-spacing:0.15em;'>"
                                                f"{platform.upper()}</div>", unsafe_allow_html=True)
                                    st.caption(f"Status: {pd_data.get('status', 'N/A')}")
                                    if pd_data.get('strength'):
                                        st.success(f"✓ {pd_data['strength']}")
                                    if pd_data.get('weakness'):
                                        st.warning(f"△ {pd_data['weakness']}")
                                    if pd_data.get('sentiment'):
                                        st.info(f"Sentiment: {pd_data['sentiment']}")

                    # Adaptation recommendations
                    recs = xp_analysis.get('content_adaptation_recommendations', [])
                    if recs:
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.caption("CONTENT ADAPTATION RECOMMENDATIONS")
                        for rec in recs:
                            impact = rec.get('expected_impact', 'medium')
                            icon = '🔴' if impact == 'high' else '🟡' if impact == 'medium' else '🟢'
                            st.markdown(f"<span class='pill-purple'>{icon} {rec.get('platform','')}: {rec.get('recommendation','')}</span>",
                                        unsafe_allow_html=True)

                    # Risk factors
                    risks = xp_analysis.get('risk_factors', [])
                    if risks:
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.caption("CROSS-PLATFORM RISK FACTORS")
                        for r in risks:
                            st.markdown(f"<span class='pill-red'>⚠ {r}</span>", unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='social-panel'>", unsafe_allow_html=True)
                st.info("Enter a TikTok handle, Instagram handle, and/or Reddit search terms in the sidebar to enable cross-platform analysis.")
                st.markdown("</div>", unsafe_allow_html=True)


        # ═══════════════════════════════════════════════════════
        # SOCIAL SUB-TAB 2 — TIKTOK INTELLIGENCE
        # ═══════════════════════════════════════════════════════
        with social_sub2:
            st.markdown(f"<div class='section-label'>▸ TIKTOK INTELLIGENCE // {ch1_name}</div>", unsafe_allow_html=True)

            if tiktok_profile:
                tt = tiktok_profile
                st.markdown("<div class='social-panel'>", unsafe_allow_html=True)
                st.markdown("<div class='section-label'>▸ TIKTOK PROFILE "
                            "<span class='api-badge badge-tiktok'>TIKTOK</span></div>", unsafe_allow_html=True)

                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("Followers", fmt_num(tt['followers']))
                c2.metric("Following", fmt_num(tt['following']))
                c3.metric("Total Likes", fmt_num(tt['likes']))
                c4.metric("Videos", f"{tt['videos']:,}")
                c5.metric("Avg Likes/Video", fmt_num(int(tt['likes']/max(tt['videos'],1))) if tt['videos'] else "N/A")

                if tt.get('bio'):
                    st.caption("BIO")
                    st.info(tt['bio'])

                # Follower/Sub ratio
                if yt_subs > 0 and tt['followers'] > 0:
                    ratio = tt['followers'] / yt_subs
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.caption("YOUTUBE ↔ TIKTOK COMPARISON")
                    comp_data = pd.DataFrame({
                        'Platform': ['YouTube', 'TikTok'],
                        'Audience': [yt_subs, tt['followers']],
                    })
                    fig_comp = px.bar(comp_data, x='Platform', y='Audience', color='Platform',
                                      color_discrete_map={'YouTube': '#ff0000', 'TikTok': '#a855f7'},
                                      title='Audience Size Comparison')
                    fig_comp.update_layout(**PLOT_PURPLE, height=280, showlegend=False)
                    fig_comp.update_xaxes(showgrid=False)
                    fig_comp.update_yaxes(gridcolor='#0d3530')
                    st.plotly_chart(fig_comp, use_container_width=True)

                    ratio_note = (f"TikTok followers are **{ratio:.1f}x** YouTube subscribers. " +
                                  ("TikTok audience significantly exceeds YouTube — strong native TikTok presence."
                                   if ratio > 2 else
                                   "Roughly balanced audience across platforms."
                                   if ratio > 0.5 else
                                   "YouTube-dominant — significant TikTok growth opportunity."))
                    st.info(ratio_note)

                st.markdown("</div>", unsafe_allow_html=True)

                # Claude TikTok analysis
                st.markdown("<div class='social-panel'>", unsafe_allow_html=True)
                st.markdown("<div class='section-label'>▸ TIKTOK STRATEGY ANALYSIS "
                            "<span class='api-badge badge-claude'>CLAUDE</span></div>", unsafe_allow_html=True)

                yt_ctx = {
                    'subscribers': yt_subs,
                    'avg_views': int(sum(v['views'] for v in ch1_vids)/max(len(ch1_vids),1)),
                    'video_count': len(ch1_vids),
                    'content_topics': [t for t,_ in Counter(t for v in ch1_vids for t in v.get('tags',[])).most_common(10)],
                }

                with st.spinner("Analyzing TikTok strategy…"):
                    tt_analysis = claude_tiktok_analysis(
                        claude_client,
                        json.dumps(tiktok_profile, default=str),
                        json.dumps(yt_ctx, default=str),
                        ch1_name
                    )

                if tt_analysis:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.caption("TIKTOK HEALTH")
                        st.info(tt_analysis.get('tiktok_health_assessment', 'N/A'))
                        st.caption("PLATFORM STRATEGY")
                        st.info(tt_analysis.get('platform_strategy_type', 'N/A'))
                        st.caption("GROWTH POTENTIAL")
                        pot = tt_analysis.get('tiktok_growth_potential', 'N/A')
                        if 'high' in pot.lower():
                            st.success(f"● HIGH — {pot}")
                        elif 'low' in pot.lower():
                            st.warning(f"● LOW — {pot}")
                        else:
                            st.info(f"● {pot}")
                    with c2:
                        st.caption("FOLLOWER/SUB RATIO ANALYSIS")
                        st.info(tt_analysis.get('follower_to_sub_ratio', 'N/A'))
                        st.caption("TIKTOK AUDIENCE PROFILE")
                        st.info(tt_analysis.get('tiktok_audience_profile', 'N/A'))
                        st.caption("MONETIZATION READINESS")
                        st.info(tt_analysis.get('monetization_readiness', 'N/A'))

                    st.markdown("<br>", unsafe_allow_html=True)
                    st.caption("TIKTOK CONTENT RECOMMENDATIONS")
                    for rec in tt_analysis.get('tiktok_content_recommendations', []):
                        st.success(f"▸ {rec}")

                    st.caption("CROSS-PROMOTION OPPORTUNITIES")
                    for opp in tt_analysis.get('cross_promotion_opportunities', []):
                        st.markdown(f"<span class='pill-purple'>↗ {opp}</span>", unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='social-panel'>", unsafe_allow_html=True)
                if has_tiktok:
                    st.warning(f"Could not fetch TikTok profile for **{active_tiktok}**. "
                               "TikTok may be blocking the request. For production use, integrate with "
                               "a service like socialdata.tools or ensembledata.com for reliable data.")
                else:
                    st.info("Enter a TikTok handle in the sidebar to enable TikTok intelligence.")
                st.markdown("</div>", unsafe_allow_html=True)


        # ═══════════════════════════════════════════════════════
        # SOCIAL SUB-TAB 3 — INSTAGRAM INTELLIGENCE
        # ═══════════════════════════════════════════════════════
        with social_sub3:
            st.markdown(f"<div class='section-label'>▸ INSTAGRAM INTELLIGENCE // {ch1_name}</div>", unsafe_allow_html=True)

            if instagram_profile:
                ig = instagram_profile
                st.markdown("<div class='social-panel'>", unsafe_allow_html=True)
                st.markdown("<div class='section-label'>▸ INSTAGRAM PROFILE "
                            "<span class='api-badge badge-tiktok'>INSTAGRAM</span></div>", unsafe_allow_html=True)

                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("Followers", fmt_num(ig['followers']))
                c2.metric("Following", fmt_num(ig['following']))
                c3.metric("Posts", f"{ig['posts']:,}")
                # Calculate engagement rate from recent posts if available
                recent = ig.get('recent_posts', [])
                if recent and ig['followers'] > 0:
                    total_eng = sum(p.get('likes',0) + p.get('comments',0) for p in recent)
                    ig_eng_rate = (total_eng / len(recent)) / ig['followers'] * 100
                    c4.metric("Avg Eng Rate", f"{ig_eng_rate:.2f}%")
                    avg_likes = int(sum(p.get('likes',0) for p in recent) / len(recent))
                    c5.metric("Avg Likes/Post", fmt_num(avg_likes))
                else:
                    c4.metric("Avg Eng Rate", "N/A")
                    c5.metric("Account Type", "Business" if ig.get('is_business') else "Personal")

                if ig.get('bio'):
                    st.caption("BIO")
                    st.info(ig['bio'])

                if ig.get('category'):
                    st.caption("CATEGORY")
                    st.markdown(f"<span class='pill-pink'>▸ {ig['category']}</span>", unsafe_allow_html=True)

                # Follower/Sub ratio chart
                if yt_subs > 0 and ig['followers'] > 0:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.caption("YOUTUBE ↔ INSTAGRAM COMPARISON")
                    platforms = ['YouTube', 'Instagram']
                    audiences = [yt_subs, ig['followers']]
                    if tiktok_profile:
                        platforms.append('TikTok')
                        audiences.append(tiktok_profile['followers'])
                    comp_data = pd.DataFrame({'Platform': platforms, 'Audience': audiences})
                    fig_comp = px.bar(comp_data, x='Platform', y='Audience', color='Platform',
                                      color_discrete_map={'YouTube': '#ff0000', 'Instagram': '#ec4899', 'TikTok': '#a855f7'},
                                      title='Audience Size Comparison')
                    fig_comp.update_layout(**PLOT_PURPLE, height=280, showlegend=False)
                    fig_comp.update_xaxes(showgrid=False)
                    fig_comp.update_yaxes(gridcolor='#0d3530')
                    st.plotly_chart(fig_comp, use_container_width=True)

                    ratio = ig['followers'] / yt_subs
                    ratio_note = (f"Instagram followers are **{ratio:.1f}x** YouTube subscribers. " +
                                  ("Instagram audience significantly exceeds YouTube — strong visual/community presence."
                                   if ratio > 2 else
                                   "Roughly balanced audience across platforms."
                                   if ratio > 0.5 else
                                   "YouTube-dominant — significant Instagram growth opportunity."))
                    st.info(ratio_note)

                # Recent post engagement breakdown
                if recent:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.caption(f"RECENT POST ENGAGEMENT ({len(recent)} posts)")
                    eng_data = pd.DataFrame([{
                        'Likes': p.get('likes', 0),
                        'Comments': p.get('comments', 0),
                        'Type': 'Video' if p.get('is_video') else 'Image',
                    } for p in recent])
                    fig_eng = px.bar(eng_data, y=['Likes', 'Comments'],
                                     title='Engagement per Recent Post',
                                     color_discrete_sequence=['#ec4899', '#831843'],
                                     barmode='stack')
                    fig_eng.update_layout(**PLOT_PURPLE, height=260, showlegend=True)
                    fig_eng.update_xaxes(showgrid=False, title='')
                    fig_eng.update_yaxes(gridcolor='#0d3530')
                    st.plotly_chart(fig_eng, use_container_width=True)

                    # Content type mix
                    video_pct = round(sum(1 for p in recent if p.get('is_video')) / len(recent) * 100, 1)
                    st.caption(f"CONTENT MIX: {video_pct}% video / {100-video_pct}% static")

                st.markdown("</div>", unsafe_allow_html=True)

                # Claude Instagram analysis
                st.markdown("<div class='social-panel'>", unsafe_allow_html=True)
                st.markdown("<div class='section-label'>▸ INSTAGRAM STRATEGY ANALYSIS "
                            "<span class='api-badge badge-claude'>CLAUDE</span></div>", unsafe_allow_html=True)

                yt_ctx = {
                    'subscribers': yt_subs,
                    'avg_views': int(sum(v['views'] for v in ch1_vids)/max(len(ch1_vids),1)),
                    'video_count': len(ch1_vids),
                    'content_topics': [t for t,_ in Counter(t for v in ch1_vids for t in v.get('tags',[])).most_common(10)],
                }

                with st.spinner("Analyzing Instagram strategy…"):
                    ig_analysis = claude_instagram_analysis(
                        claude_client,
                        json.dumps(instagram_profile, default=str),
                        json.dumps(yt_ctx, default=str),
                        ch1_name
                    )

                if ig_analysis:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.caption("INSTAGRAM HEALTH")
                        st.info(ig_analysis.get('ig_health_assessment', 'N/A'))
                        st.caption("PLATFORM STRATEGY")
                        st.info(ig_analysis.get('platform_strategy_type', 'N/A'))
                        st.caption("CONTENT MIX ASSESSMENT")
                        st.info(ig_analysis.get('content_type_mix', 'N/A'))
                        st.caption("GROWTH POTENTIAL")
                        pot = ig_analysis.get('ig_growth_potential', 'N/A')
                        if 'high' in pot.lower():
                            st.success(f"● HIGH — {pot}")
                        elif 'low' in pot.lower():
                            st.warning(f"● LOW — {pot}")
                        else:
                            st.info(f"● {pot}")
                    with c2:
                        st.caption("FOLLOWER/SUB RATIO ANALYSIS")
                        st.info(ig_analysis.get('follower_to_sub_ratio', 'N/A'))
                        st.caption("ENGAGEMENT RATE ASSESSMENT")
                        st.info(ig_analysis.get('engagement_rate_assessment', 'N/A'))
                        st.caption("IG AUDIENCE PROFILE")
                        st.info(ig_analysis.get('ig_audience_profile', 'N/A'))
                        st.caption("BRAND PARTNERSHIP READINESS")
                        st.info(ig_analysis.get('brand_partnership_readiness', 'N/A'))

                    st.markdown("<br>", unsafe_allow_html=True)
                    st.caption("REELS STRATEGY")
                    st.success(f"▸ {ig_analysis.get('reels_strategy', 'N/A')}")
                    st.caption("STORIES STRATEGY")
                    st.success(f"▸ {ig_analysis.get('stories_strategy', 'N/A')}")

                    st.markdown("<br>", unsafe_allow_html=True)
                    st.caption("INSTAGRAM CONTENT RECOMMENDATIONS")
                    for rec in ig_analysis.get('ig_content_recommendations', []):
                        st.success(f"▸ {rec}")

                    st.caption("CROSS-PROMOTION OPPORTUNITIES")
                    for opp in ig_analysis.get('cross_promotion_opportunities', []):
                        st.markdown(f"<span class='pill-pink'>↗ {opp}</span>", unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='social-panel'>", unsafe_allow_html=True)
                if has_instagram:
                    st.warning(f"Could not fetch Instagram profile for **{active_ig}**. "
                               "Instagram may be blocking the request. For production use, integrate with "
                               "Apify or PhantomBuster for reliable data extraction.")
                else:
                    st.info("Enter an Instagram handle in the sidebar to enable Instagram intelligence.")
                st.markdown("</div>", unsafe_allow_html=True)


        # ═══════════════════════════════════════════════════════
        # SOCIAL SUB-TAB 4 — REDDIT PRESENCE
        # ═══════════════════════════════════════════════════════
        with social_sub4:
            st.markdown(f"<div class='section-label'>▸ REDDIT PRESENCE MAP // {ch1_name}</div>", unsafe_allow_html=True)

            if reddit_posts:
                st.markdown("<div class='social-panel'>", unsafe_allow_html=True)
                st.markdown("<div class='section-label'>▸ REDDIT POST ACTIVITY "
                            "<span class='api-badge badge-reddit'>REDDIT</span></div>", unsafe_allow_html=True)

                # Summary metrics
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Posts Found", len(reddit_posts))
                c2.metric("Comments Found", len(reddit_comments))
                unique_subs = set(p['subreddit'] for p in reddit_posts)
                c3.metric("Unique Subreddits", len(unique_subs))
                avg_score = round(sum(p['score'] for p in reddit_posts)/max(len(reddit_posts),1), 1)
                c4.metric("Avg Post Score", f"{avg_score}")

                # Subreddit distribution
                sub_counts = Counter(p['subreddit'] for p in reddit_posts).most_common(15)
                if sub_counts:
                    fig_sub = px.bar(
                        pd.DataFrame(sub_counts, columns=['Subreddit', 'Posts']),
                        x='Posts', y='Subreddit', orientation='h',
                        title='Subreddit Distribution',
                        color='Posts', color_continuous_scale='Oryel'
                    )
                    fig_sub.update_layout(**PLOT_AMBER, height=max(250, len(sub_counts)*30), showlegend=False, coloraxis_showscale=False)
                    fig_sub.update_xaxes(showgrid=False)
                    fig_sub.update_yaxes(gridcolor='#0d3530')
                    st.plotly_chart(fig_sub, use_container_width=True)

                # Top posts table
                st.caption("TOP REDDIT POSTS BY SCORE")
                top_reddit = sorted(reddit_posts, key=lambda x: x['score'], reverse=True)[:15]
                df_reddit = pd.DataFrame([{
                    'Score': p['score'],
                    'Subreddit': f"r/{p['subreddit']}",
                    'Title': p['title'][:80],
                    'Comments': p['num_comments'],
                    'Link': p['url']
                } for p in top_reddit])
                st.dataframe(df_reddit, hide_index=True, use_container_width=True,
                             column_config={
                                 "Link": st.column_config.LinkColumn("▶", display_text="▶ Open")
                             })

                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='social-panel'>", unsafe_allow_html=True)
                if has_reddit or ch1_name:
                    st.warning("No Reddit posts found for this search. Try different search terms in the sidebar.")
                else:
                    st.info("Enter Reddit search terms in the sidebar to scan for brand mentions.")
                st.markdown("</div>", unsafe_allow_html=True)


    # ═══════════════════════════════════════════════════════════
    # ███ TAB 3 — SOCIAL LISTENING
    # ═══════════════════════════════════════════════════════════
with main_tab_listen:
    if not active_social:
        st.markdown("""
<div style="border-top:1px solid rgba(245,158,11,0.15);padding:2rem 0;text-align:center;">
  <div style="font-family:'Orbitron',monospace;font-size:0.7rem;color:#f59e0b;letter-spacing:0.2em;margin-bottom:12px;">
    👂 SOCIAL LISTENING — DISABLED
  </div>
  <div style="font-family:'Share Tech Mono',monospace;font-size:0.8rem;color:#5a8a82;max-width:500px;margin:0 auto;line-height:1.6;">
    Enable the <strong style="color:#f59e0b;">Social Intelligence</strong> checkbox in the sidebar
    to activate Reddit listening and sentiment analysis.
  </div>
</div>""", unsafe_allow_html=True)

    if active_social:
        listen_sub1, listen_sub2 = st.tabs([
            "🔍 Reddit Deep Listen",
            "📊 Sentiment Dashboard",
        ])

        ch1_name = list(channel_data.keys())[0]
        reddit_posts = st.session_state.get('reddit_posts', [])
        reddit_comments = st.session_state.get('reddit_comments', [])

        # ═══════════════════════════════════════════════════════
        # LISTEN SUB-TAB 1 — REDDIT DEEP LISTEN
        # ═══════════════════════════════════════════════════════
        with listen_sub1:
            st.markdown(f"<div class='section-label'>▸ SOCIAL LISTENING // REDDIT INTELLIGENCE — {ch1_name}</div>", unsafe_allow_html=True)

            if reddit_posts or reddit_comments:
                st.markdown("<div class='listen-panel'>", unsafe_allow_html=True)
                st.markdown("<div class='section-label'>▸ REDDIT SENTIMENT ANALYSIS "
                            "<span class='api-badge badge-claude'>CLAUDE</span>"
                            "<span class='api-badge badge-reddit'>REDDIT</span></div>", unsafe_allow_html=True)

                with st.spinner("Claude is performing deep social listening analysis…"):
                    listening_intel = claude_reddit_listening(
                        claude_client,
                        json.dumps(sorted(reddit_posts, key=lambda x: x['score'], reverse=True)[:30], default=str),
                        json.dumps(sorted(reddit_comments, key=lambda x: x['score'], reverse=True)[:40], default=str),
                        ch1_name
                    )

                if listening_intel:
                    # Header: sentiment score + brand safety
                    s1, s2, s3 = st.columns([1, 2, 2])
                    with s1:
                        score = listening_intel.get('sentiment_score', 5)
                        score_color = '#00d4b4' if score >= 7 else '#f59e0b' if score >= 4 else '#ff3a2d'
                        st.markdown(f"<div style='text-align:center;padding:0.5rem'>"
                                    f"<div style='font-family:Orbitron,monospace;font-size:1.8rem;"
                                    f"color:{score_color};text-shadow:0 0 14px {score_color}'>"
                                    f"{score}/10</div>"
                                    f"<div style='font-size:0.55rem;color:#5a8a82;letter-spacing:0.12em'>SENTIMENT</div>"
                                    f"</div>", unsafe_allow_html=True)
                    with s2:
                        st.caption("OVERALL SENTIMENT")
                        st.info(listening_intel.get('overall_sentiment', 'N/A'))
                        st.caption("BRAND SAFETY")
                        safety = listening_intel.get('brand_safety_score', 'N/A')
                        if 'safe' in safety.lower():
                            st.success(f"✓ {safety}")
                        elif 'risk' in safety.lower():
                            st.error(f"⚠ {safety}")
                        else:
                            st.warning(f"● {safety}")
                    with s3:
                        st.caption("PERCEPTION GAP")
                        st.info(listening_intel.get('perception_gap', 'N/A'))
                        st.caption("AUDIENCE DEMOGRAPHICS (from Reddit)")
                        st.info(listening_intel.get('audience_demographics_from_reddit', 'N/A'))

                    st.markdown("<br>", unsafe_allow_html=True)

                    # Recurring themes
                    themes = listening_intel.get('recurring_themes', [])
                    if themes:
                        st.caption("RECURRING THEMES IN DISCUSSION")
                        for theme in themes:
                            sent = theme.get('sentiment', 'mixed')
                            sent_icon = '🟢' if sent == 'positive' else '🔴' if sent == 'negative' else '🟡'
                            freq = theme.get('frequency', 'medium')
                            st.markdown(f"<span class='pill-amber'>{sent_icon} {theme.get('theme','')} "
                                        f"({freq})</span>", unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

                    # Praise + Criticism side by side
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.caption("TOP PRAISE")
                        for p in listening_intel.get('top_praise', []):
                            st.success(f"✓ {p}")
                    with col_b:
                        st.caption("TOP CRITICISMS")
                        for c in listening_intel.get('top_criticisms', []):
                            st.warning(f"△ {c}")

                    st.markdown("<br>", unsafe_allow_html=True)

                    # Content demand + controversy
                    col_c, col_d = st.columns(2)
                    with col_c:
                        st.caption("CONTENT DEMAND SIGNALS")
                        for d in listening_intel.get('content_demand_signals', []):
                            st.markdown(f"<span class='pill-amber'>💡 {d}</span>", unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.caption("COMPETITOR MENTIONS")
                        for comp in listening_intel.get('competitor_mentions', []):
                            st.markdown(f"<span class='pill'>↗ {comp}</span>", unsafe_allow_html=True)
                    with col_d:
                        st.caption("CONTROVERSY FLAGS")
                        for flag in listening_intel.get('controversy_flags', []):
                            if flag.lower() == 'none detected':
                                st.success(f"✓ {flag}")
                            else:
                                st.error(f"⚠ {flag}")
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.caption("KEY SUBREDDITS")
                        for sub in listening_intel.get('key_subreddits', []):
                            st.markdown(f"<span class='pill-amber'>▸ {sub}</span>", unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

                    # Notable quote highlights
                    quotes = listening_intel.get('quote_highlights', [])
                    if quotes:
                        st.caption("NOTABLE DISCUSSION HIGHLIGHTS")
                        for q in quotes:
                            sent = q.get('sentiment', 'neutral')
                            sent_icon = '🟢' if sent in ('pos','positive') else '🔴' if sent in ('neg','negative') else '🟡'
                            with st.expander(f"{sent_icon} {q.get('quote_summary','')}"):
                                st.markdown(f"**Context:** {q.get('context','')}")

                    st.markdown("<br>", unsafe_allow_html=True)
                    st.caption("ACTIONABLE INSIGHTS")
                    for insight in listening_intel.get('actionable_insights', []):
                        st.success(f"▸ {insight}")

                else:
                    st.warning("Social listening analysis returned no data.")
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='listen-panel'>", unsafe_allow_html=True)
                st.info("No Reddit data available for social listening. Enter search terms in the sidebar "
                        "and re-run the analysis to enable this module.")
                st.markdown("</div>", unsafe_allow_html=True)


        # ═══════════════════════════════════════════════════════
        # LISTEN SUB-TAB 2 — SENTIMENT DASHBOARD
        # ═══════════════════════════════════════════════════════
        with listen_sub2:
            st.markdown(f"<div class='section-label'>▸ SENTIMENT DASHBOARD // {ch1_name}</div>", unsafe_allow_html=True)

            if reddit_posts:
                st.markdown("<div class='listen-panel'>", unsafe_allow_html=True)
                st.markdown("<div class='section-label'>▸ REDDIT ENGAGEMENT METRICS</div>", unsafe_allow_html=True)

                # Score distribution
                scores = [p['score'] for p in reddit_posts]
                fig_score = px.histogram(scores, nbins=30, title='Post Score Distribution',
                                         labels={'value': 'Score', 'count': 'Posts'},
                                         color_discrete_sequence=['#f59e0b'])
                fig_score.update_layout(**PLOT_AMBER, height=280)
                fig_score.update_xaxes(showgrid=False)
                fig_score.update_yaxes(gridcolor='#0d3530')
                st.plotly_chart(fig_score, use_container_width=True)

                # Upvote ratio distribution
                ratios = [p['upvote_ratio'] for p in reddit_posts if p['upvote_ratio'] > 0]
                if ratios:
                    avg_ratio = round(sum(ratios)/len(ratios)*100, 1)
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Avg Upvote Ratio", f"{avg_ratio}%")
                    c2.metric("Highest Score Post", f"{max(scores):,}")
                    c3.metric("Total Engagement", f"{sum(p['num_comments'] for p in reddit_posts):,} comments")

                    fig_ratio = px.histogram(ratios, nbins=20, title='Upvote Ratio Distribution (higher = more positive)',
                                             labels={'value': 'Upvote Ratio'},
                                             color_discrete_sequence=['#00d4b4'])
                    fig_ratio.update_layout(**PLOT_AMBER, height=250)
                    fig_ratio.update_xaxes(showgrid=False)
                    fig_ratio.update_yaxes(gridcolor='#0d3530')
                    st.plotly_chart(fig_ratio, use_container_width=True)

                # Post timeline
                posts_with_dates = [p for p in reddit_posts if p.get('created_utc', 0) > 0]
                if posts_with_dates:
                    df_timeline = pd.DataFrame(posts_with_dates)
                    df_timeline['date'] = pd.to_datetime(df_timeline['created_utc'], unit='s')
                    df_timeline['month'] = df_timeline['date'].dt.to_period('M').astype(str)
                    monthly = df_timeline.groupby('month').agg(
                        posts=('score', 'count'),
                        total_score=('score', 'sum'),
                        avg_score=('score', 'mean')
                    ).reset_index()

                    fig_timeline = px.bar(monthly, x='month', y='posts',
                                          title='Reddit Mention Volume Over Time',
                                          labels={'posts': 'Posts', 'month': ''},
                                          color='avg_score', color_continuous_scale='YlOrRd')
                    fig_timeline.update_layout(**PLOT_AMBER, height=280, coloraxis_showscale=False)
                    fig_timeline.update_xaxes(showgrid=False)
                    fig_timeline.update_yaxes(gridcolor='#0d3530')
                    st.plotly_chart(fig_timeline, use_container_width=True)

                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='listen-panel'>", unsafe_allow_html=True)
                st.info("No Reddit data available for the sentiment dashboard. Enable Reddit search in the sidebar.")
                st.markdown("</div>", unsafe_allow_html=True)


    # ═══════════════════════════════════════════════════════════
    # ███ TAB 4 — STRATEGIC BRIEF
    # ═══════════════════════════════════════════════════════════
with main_tab_brief:
    brief_sub1, brief_sub2 = st.tabs([
        "📺 YouTube Strategic Brief",
        "🌐 Comprehensive Multi-Platform Brief",
    ])

    # ═══════════════════════════════════════════════════════
    # BRIEF SUB-TAB 1 — YOUTUBE BRIEF (original)
    # ═══════════════════════════════════════════════════════
    with brief_sub1:
        st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
        st.markdown("<div class='section-label'>▸ MODULE // YOUTUBE STRATEGIC INTELLIGENCE BRIEF "
                    "<span class='api-badge badge-claude'>CLAUDE</span></div>", unsafe_allow_html=True)
        st.caption("Full presentation-ready brief synthesizing all YouTube intelligence layers — performance, content DNA, sponsorships, competitive landscape")
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("⚡ Generate YouTube Strategic Brief", type="primary", key="yt_brief_btn"):
            context = {}
            for ch_name, d in channel_data.items():
                vs, stat = d['videos'], d['info'].get('statistics', {})
                subs = int(stat.get('subscriberCount', 1))

                eng_per_video = [(v['likes']+v['comments'])/max(v['views'],1) for v in vs]
                avg_e_raw     = sum(eng_per_video)/max(len(eng_per_video),1)
                eng_per_1k_subs = [(v['likes']+v['comments'])/max(subs,1)*1000 for v in vs]
                avg_eng_per_1k  = sum(eng_per_1k_subs)/max(len(eng_per_1k_subs),1)

                sorted_by_date  = sorted(vs, key=lambda x: x.get('published_at', ''))
                quintile        = max(len(sorted_by_date)//5, 1)
                early_eng       = sum((v['likes']+v['comments'])/max(v['views'],1)
                                      for v in sorted_by_date[:quintile]) / quintile
                recent_eng      = sum((v['likes']+v['comments'])/max(v['views'],1)
                                      for v in sorted_by_date[-quintile:]) / quintile
                eng_trend       = "improving" if recent_eng > early_eng * 1.05 else \
                                  "declining" if recent_eng < early_eng * 0.95 else "stable"
                eng_trend_pct   = f"{((recent_eng-early_eng)/max(early_eng,0.001))*100:+.1f}%"

                if len(sorted_by_date) >= 10:
                    old_avg  = sum(v['views'] for v in sorted_by_date[:quintile])  / quintile
                    new_avg  = sum(v['views'] for v in sorted_by_date[-quintile:]) / quintile
                    decay_ratio = new_avg / max(old_avg, 1)
                    decay_note  = (f"Recent uploads averaging {decay_ratio:.1f}x the views of "
                                   f"oldest uploads — "
                                   + ("suggests strong evergreen catalog pull"
                                      if decay_ratio < 0.5 else
                                      "suggests recent content outperforming older catalog"
                                      if decay_ratio > 1.5 else
                                      "relatively consistent view distribution across catalog age"))
                else:
                    decay_note = "Insufficient video history for decay analysis"

                sb_context = {}
                sb_raw = st.session_state.get(f'sb_{ch_name}')
                if sb_raw:
                    sb = parse_socialblade(sb_raw)
                    if sb:
                        sb_context = {
                            'grade':         sb.get('grade'),
                            'subs_30d':      sb.get('subs_30d'),
                            'subs_7d':       sb.get('subs_7d'),
                            'est_monthly_earnings_min': sb.get('earnings_min'),
                            'est_monthly_earnings_max': sb.get('earnings_max'),
                            'trajectory_note': (
                                "accelerating" if (sb.get('subs_7d',0) or 0) * 4.3 >
                                                  (sb.get('subs_30d',0) or 0) * 1.1
                                else "decelerating" if (sb.get('subs_7d',0) or 0) * 4.3 <
                                                       (sb.get('subs_30d',0) or 0) * 0.9
                                else "steady"
                            )
                        }

                now = pd.Timestamp.utcnow()
                decay_buckets = {'0_to_30d': [], '31_to_90d': [], '91_to_180d': [], 'over_180d': []}
                for v in vs:
                    try:
                        pub = pd.to_datetime(v.get('published_at'))
                        if pub.tzinfo is not None:
                            pub = pub.tz_convert('UTC').tz_localize(None)
                        age = (now.tz_localize(None) - pub).days
                    except Exception:
                        age = 999
                    if   age <= 30:  decay_buckets['0_to_30d'].append(v['views'])
                    elif age <= 90:  decay_buckets['31_to_90d'].append(v['views'])
                    elif age <= 180: decay_buckets['91_to_180d'].append(v['views'])
                    else:            decay_buckets['over_180d'].append(v['views'])
                decay_curve = {
                    k: int(sum(vals)/len(vals)) if vals else None
                    for k, vals in decay_buckets.items()
                }
                if decay_curve['0_to_30d'] and decay_curve['over_180d']:
                    retention = round(decay_curve['over_180d'] / decay_curve['0_to_30d'] * 100, 1)
                    decay_interpretation = (
                        f"Videos retain {retention}% of launch-window views after 180+ days. "
                        + ("Strong evergreen catalog — back catalog has sustained B2B/licensing value."
                           if retention >= 60 else
                           "Moderate evergreen — some catalog longevity but primarily launch-dependent."
                           if retention >= 30 else
                           "Low retention — traffic is launch-window dependent, catalog decays quickly.")
                    )
                else:
                    retention = None
                    decay_interpretation = "Insufficient age range to calculate decay curve."

                dfs_context = {}
                dfs_raw = st.session_state.get(f'dfs_results_{ch_name}', [])
                if dfs_raw:
                    dfs_context = {
                        'competitor_channels_found': list({r['channel'] for r in dfs_raw}),
                        'top_search_queries_used':   list({r.get('query','') for r in dfs_raw}),
                        'note': ('These are real YouTube search queries with actual demand. '
                                 'Use them as market-size proxies for sub-channel topic recommendations.')
                    }
                cpc_context = {}
                if has_dataforseo:
                    top_tags = [t for t, _ in Counter(
                        tag for v in vs for tag in v.get('tags', [])).most_common(8)]
                    if top_tags:
                        cpc_rows = dataforseo_keyword_cpc(dataforseo_login, dataforseo_password, tuple(top_tags))
                        if cpc_rows:
                            avg_cpc   = round(sum(r['cpc'] for r in cpc_rows if r['cpc']) /
                                              max(sum(1 for r in cpc_rows if r['cpc']), 1), 2)
                            top_cpc   = sorted(cpc_rows, key=lambda x: x['cpc'] or 0, reverse=True)[:3]
                            cpc_context = {
                                'avg_cpc_usd':   avg_cpc,
                                'top_cpc_keywords': top_cpc,
                                'sponsorship_rationale': (
                                    f"Avg CPC ${avg_cpc} for this channel's topic keywords. "
                                    f"Sponsorship rates typically 20-40x CPM for direct integrations. "
                                    f"At {int(sum(v['views'] for v in vs[:10])/10):,} avg views/video, "
                                    f"implied sponsor value: "
                                    f"${int(avg_cpc * 20 * int(sum(v['views'] for v in vs[:10])/10) / 1000):,}"
                                    f"–${int(avg_cpc * 40 * int(sum(v['views'] for v in vs[:10])/10) / 1000):,} per integration."
                                )
                            }

                avg_v = int(sum(v['views'] for v in vs) / max(len(vs),1))

                context[ch_name] = {
                    'subscribers':              subs,
                    'total_views':              stat.get('viewCount'),
                    'video_count':              stat.get('videoCount'),
                    'avg_views_per_video':      avg_v,
                    'avg_engagement_rate_pct':          f"{avg_e_raw*100:.2f}%",
                    'avg_engagement_per_1k_subs':       f"{avg_eng_per_1k:.3f}",
                    'engagement_trend':                 eng_trend,
                    'engagement_trend_vs_early_videos': eng_trend_pct,
                    'engagement_early_period':          f"{early_eng*100:.2f}%",
                    'engagement_recent_period':         f"{recent_eng*100:.2f}%",
                    'engagement_methodology_note': (
                        'engagement_rate_pct = (likes+comments)/views — use for absolute benchmarks. '
                        'engagement_per_1k_subs = interactions per 1k subscribers — '
                        'use for cross-channel scale comparisons. '
                        'NEVER compare raw engagement% between channels of different sizes without noting scale.'
                    ),
                    'content_decay_by_age':     decay_curve,
                    'decay_180d_retention_pct': retention,
                    'decay_interpretation':     decay_interpretation,
                    'socialblade':              sb_context or 'not_available',
                    'search_demand_data':       dfs_context or 'not_available',
                    'keyword_cpc_data':         cpc_context or 'not_available',
                    'recent_titles':            [v['title'] for v in vs[:25]],
                    'description_samples':      [v['description'][:300] for v in vs[:10]],
                    'top_5_videos':             sorted(vs, key=lambda x: x['views'], reverse=True)[:5],
                    'top_tags':                 list(Counter(
                        t for v in vs for t in v.get('tags',[])).most_common(20))
                }

            # ── Inject cross-platform social data into YT brief context (only when social enabled) ──
            if active_social:
                tt_data = st.session_state.get('tiktok_profile')
                ig_data = st.session_state.get('instagram_profile')
                rp_data = st.session_state.get('reddit_posts', [])
                rc_data = st.session_state.get('reddit_comments', [])

                social_context = {}
                if tt_data:
                    social_context['tiktok'] = {
                        'followers': tt_data.get('followers', 0),
                        'likes': tt_data.get('likes', 0),
                        'videos': tt_data.get('videos', 0),
                        'bio': tt_data.get('bio', ''),
                        'verified': tt_data.get('verified', False),
                    }
                if ig_data:
                    ig_recent = ig_data.get('recent_posts', [])
                    ig_eng = 0
                    if ig_recent and ig_data.get('followers', 0) > 0:
                        ig_eng = round((sum(p.get('likes',0)+p.get('comments',0) for p in ig_recent) / len(ig_recent)) / ig_data['followers'] * 100, 2)
                    social_context['instagram'] = {
                        'followers': ig_data.get('followers', 0),
                        'following': ig_data.get('following', 0),
                        'posts': ig_data.get('posts', 0),
                        'bio': ig_data.get('bio', ''),
                        'verified': ig_data.get('verified', False),
                        'is_business': ig_data.get('is_business', False),
                        'category': ig_data.get('category', ''),
                        'avg_engagement_rate_pct': f"{ig_eng}%",
                        'recent_post_count': len(ig_recent),
                    }
                if rp_data:
                    social_context['reddit'] = {
                        'posts_found': len(rp_data),
                        'comments_found': len(rc_data),
                        'unique_subreddits': list(set(p['subreddit'] for p in rp_data))[:8],
                        'avg_upvote_ratio': round(sum(p.get('upvote_ratio',0) for p in rp_data if p.get('upvote_ratio',0)>0)/max(sum(1 for p in rp_data if p.get('upvote_ratio',0)>0),1)*100, 1),
                        'top_post_titles': [p['title'] for p in sorted(rp_data, key=lambda x: x['score'], reverse=True)[:5]],
                    }

                if social_context:
                    for ch_name in context:
                        context[ch_name]['cross_platform_social_data'] = social_context
                        context[ch_name]['cross_platform_note'] = (
                            'Social platform data is available. When writing the brief, reference cross-platform '
                            'presence in the Executive Summary and Growth Opportunities where it strengthens or '
                            'qualifies a recommendation. Do NOT write a separate social section — weave it in naturally. '
                            'Example: "The channel has 1.2M YouTube subscribers but only 45K Instagram followers, '
                            'suggesting an under-exploited visual platform opportunity."'
                        )

            # ── Inject geography estimation if available ──
            for ch_name in context:
                geo_est = st.session_state.get(f'geo_{ch_name}')
                if geo_est:
                    context[ch_name]['audience_geography_estimate'] = {
                        'estimated_us_domestic_pct': geo_est.get('estimated_us_domestic_pct'),
                        'estimated_regions': geo_est.get('estimated_regions', []),
                        'english_speaking_total_pct': geo_est.get('english_speaking_total_pct'),
                        'market_classification': geo_est.get('market_classification'),
                        'confidence_level': geo_est.get('confidence_level'),
                        'advertiser_implications': geo_est.get('advertiser_implications'),
                    }
                    context[ch_name]['geography_note'] = (
                        'audience_geography_estimate is a PROXY ESTIMATE, not verified analytics. '
                        'Use it directionally: reference it in the Executive Summary for context '
                        '(e.g., "estimated ~60% US domestic audience"), in Monetization for CPM implications, '
                        'and in Risk Assessment if the confidence level is low. Always caveat as "estimated." '
                        'Do NOT present proxy estimates as facts.'
                    )

            with st.spinner("Generating strategic brief — 20-30 seconds…"):
                brief = claude_strategic_brief(claude_client, json.dumps(context, default=str))

            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='section-label'>▸ INTELLIGENCE REPORT // OUTPUT</div>", unsafe_allow_html=True)
            st.markdown(brief)
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='tac-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='section-label'>▸ EXPORT // DOWNLOAD BRIEF</div>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("⬇️ Download as .txt", data=brief,
                                   file_name="yt_strategic_brief.txt", mime="text/plain",
                                   use_container_width=True)
            with c2:
                st.download_button("⬇️ Download as .md", data=brief,
                                   file_name="yt_strategic_brief.md", mime="text/markdown",
                                   use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("</div>", unsafe_allow_html=True)


    # ═══════════════════════════════════════════════════════
    # BRIEF SUB-TAB 2 — COMPREHENSIVE MULTI-PLATFORM BRIEF
    # ═══════════════════════════════════════════════════════
    with brief_sub2:
        if not active_social:
            st.markdown("<div class='social-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='section-label'>▸ COMPREHENSIVE MULTI-PLATFORM INTELLIGENCE BRIEF</div>", unsafe_allow_html=True)
            st.info("Enable the **Social Intelligence** checkbox in the sidebar to unlock the multi-platform brief. "
                    "This brief synthesizes YouTube, TikTok, Instagram, and Reddit data into a unified strategic assessment.")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='social-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='section-label'>▸ COMPREHENSIVE MULTI-PLATFORM INTELLIGENCE BRIEF "
                        "<span class='api-badge badge-claude'>CLAUDE</span></div>", unsafe_allow_html=True)
            st.caption("Synthesizes YouTube, TikTok, Instagram, and Reddit data into a unified strategic assessment. "
                       "Run the YouTube, Social, and Listening tabs first for the richest brief.")
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("⚡ Generate Multi-Platform Brief", type="primary", key="full_brief_btn"):
                # Build comprehensive context from all sources
                full_context = {}
                for ch_name, d in channel_data.items():
                    vs, stat = d['videos'], d['info'].get('statistics', {})
                    subs = int(stat.get('subscriberCount', 1))

                    eng_per_video = [(v['likes']+v['comments'])/max(v['views'],1) for v in vs]
                    avg_e_raw = sum(eng_per_video)/max(len(eng_per_video),1)

                    full_context['youtube'] = {
                        'channel_name': ch_name,
                        'subscribers': subs,
                        'total_views': stat.get('viewCount'),
                        'video_count': stat.get('videoCount'),
                        'avg_views_per_video': int(sum(v['views'] for v in vs)/max(len(vs),1)),
                        'avg_engagement_rate_pct': f"{avg_e_raw*100:.2f}%",
                        'recent_titles': [v['title'] for v in vs[:15]],
                        'top_tags': [t for t,_ in Counter(t for v in vs for t in v.get('tags',[])).most_common(15)],
                        'socialblade': st.session_state.get(f'sb_{ch_name}', 'not_available'),
                    }

                # TikTok data
                tt = st.session_state.get('tiktok_profile')
                full_context['tiktok'] = tt if tt else 'not_available'

                # Instagram data
                ig = st.session_state.get('instagram_profile')
                if ig:
                    ig_recent = ig.get('recent_posts', [])
                    ig_eng = 0
                    if ig_recent and ig.get('followers', 0) > 0:
                        ig_eng = round((sum(p.get('likes',0)+p.get('comments',0) for p in ig_recent) / len(ig_recent)) / ig['followers'] * 100, 2)
                    full_context['instagram'] = {
                        'followers': ig.get('followers', 0),
                        'following': ig.get('following', 0),
                        'posts': ig.get('posts', 0),
                        'bio': ig.get('bio', ''),
                        'verified': ig.get('verified', False),
                        'is_business': ig.get('is_business', False),
                        'category': ig.get('category', ''),
                        'avg_engagement_rate_pct': f"{ig_eng}%",
                        'recent_post_count': len(ig_recent),
                        'video_pct_of_recent': round(sum(1 for p in ig_recent if p.get('is_video'))/max(len(ig_recent),1)*100, 1) if ig_recent else 0,
                        'avg_likes_per_post': int(sum(p.get('likes',0) for p in ig_recent)/max(len(ig_recent),1)) if ig_recent else 0,
                        'avg_comments_per_post': int(sum(p.get('comments',0) for p in ig_recent)/max(len(ig_recent),1)) if ig_recent else 0,
                    }
                else:
                    full_context['instagram'] = 'not_available'

                # Reddit data
                rp = st.session_state.get('reddit_posts', [])
                rc = st.session_state.get('reddit_comments', [])
                if rp:
                    full_context['reddit'] = {
                        'posts_found': len(rp),
                        'comments_found': len(rc),
                        'unique_subreddits': list(set(p['subreddit'] for p in rp))[:10],
                        'top_posts_by_score': sorted(rp, key=lambda x: x['score'], reverse=True)[:10],
                        'avg_upvote_ratio': round(sum(p['upvote_ratio'] for p in rp if p['upvote_ratio']>0)/max(sum(1 for p in rp if p['upvote_ratio']>0),1)*100, 1),
                        'top_comments': sorted(rc, key=lambda x: x['score'], reverse=True)[:10],
                    }
                else:
                    full_context['reddit'] = 'not_available'

                # DataForSEO data if available
                ch1_name = list(channel_data.keys())[0]
                dfs = st.session_state.get(f'dfs_results_{ch1_name}', [])
                if dfs:
                    full_context['competitor_data'] = {
                        'channels': list({r['channel'] for r in dfs})[:10],
                        'search_queries': list({r.get('query','') for r in dfs}),
                    }

                # Geography estimation if available
                geo_est = st.session_state.get(f'geo_{ch1_name}')
                if geo_est:
                    full_context['audience_geography_estimate'] = geo_est

                with st.spinner("Generating comprehensive multi-platform brief — 30-45 seconds…"):
                    full_brief = claude_comprehensive_brief(
                        claude_client,
                        json.dumps(full_context, default=str)
                    )

                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("<div class='social-panel'>", unsafe_allow_html=True)
                st.markdown("<div class='section-label'>▸ COMPREHENSIVE INTELLIGENCE REPORT // OUTPUT</div>", unsafe_allow_html=True)
                st.markdown(full_brief)
                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("<div class='social-panel'>", unsafe_allow_html=True)
                st.markdown("<div class='section-label'>▸ EXPORT // DOWNLOAD BRIEF</div>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    st.download_button("⬇️ Download as .txt", data=full_brief,
                                       file_name="multiplatform_strategic_brief.txt", mime="text/plain",
                                       use_container_width=True, key="full_brief_txt")
                with c2:
                    st.download_button("⬇️ Download as .md", data=full_brief,
                                       file_name="multiplatform_strategic_brief.md", mime="text/markdown",
                                       use_container_width=True, key="full_brief_md")
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown("</div>", unsafe_allow_html=True)
