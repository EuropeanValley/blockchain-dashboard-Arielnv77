"""CryptoChain Analyzer — dark navy Streamlit dashboard.

Run with:  streamlit run app.py
Sidebar navigation selects which module to display.
Auto-refreshes every 60 s via streamlit-autorefresh.
"""

from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st
from streamlit_autorefresh import st_autorefresh

# ── Page config (must be the very first Streamlit call) ───────────────────────
st.set_page_config(
    page_title="CryptoChain Analyzer",
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="expanded",
)

st_autorefresh(interval=60_000, key="global_refresh")

# ─────────────────────────────────────────────────────────────────────────────
# CSS — complete dark navy theme
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Reset & global ── */
*, *::before, *::after { box-sizing: border-box; }
html, body, .stApp { font-family: 'Inter', sans-serif !important; }

/* ── Hide Streamlit chrome ── */
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { display: none !important; }
.stDeployButton, [data-testid="collapsedControl"] { display: none !important; }

/* ── Background: deep navy with subtle glow ── */
.stApp {
    background: #0a0f1e !important;
    background-image:
        radial-gradient(ellipse at 15% 25%, rgba(61,106,255,0.05) 0%, transparent 50%),
        radial-gradient(ellipse at 85% 75%, rgba(124,77,255,0.04) 0%, transparent 50%);
}

/* ── Main container ── */
.block-container { padding: 20px 24px 40px !important; max-width: 100% !important; }

/* ────────────────── SIDEBAR ────────────────── */
[data-testid="stSidebar"] {
    background: #0d1426 !important;
    border-right: 1px solid #1e2d4a !important;
    min-width: 210px !important;
    max-width: 210px !important;
}
[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }
[data-testid="stSidebar"] .block-container  { padding: 0 !important; }
[data-testid="stSidebar"] .stMarkdown       { padding: 0 !important; }

/* ── Sidebar radio → styled nav items ── */
[data-testid="stSidebar"] .stRadio > label { display: none; }
[data-testid="stSidebar"] div[role="radiogroup"] {
    display: flex; flex-direction: column; gap: 2px; padding: 0 10px;
}
[data-testid="stSidebar"] div[role="radiogroup"] label {
    display: flex; align-items: center; gap: 9px;
    padding: 9px 12px; border-radius: 9px;
    color: #8892a4; font-size: 13px; font-weight: 400;
    cursor: pointer; transition: all 0.14s ease;
    border: 1px solid transparent; width: 100%;
}
[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: rgba(61,106,255,0.08); color: #c5cdd9;
}
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
    background: rgba(61,106,255,0.14); color: #4f7bff;
    font-weight: 500; border: 1px solid rgba(61,106,255,0.22);
}
[data-testid="stSidebar"] div[role="radiogroup"] label span:first-child {
    display: none !important;
}

/* ────────────────── CARDS ────────────────── */
.crypto-card {
    background: #111827; border: 1px solid #1e2d4a;
    border-radius: 16px; padding: 20px; margin-bottom: 14px;
}
.crypto-card-blue {
    background: linear-gradient(135deg, #1a237e 0%, #0d47a1 100%);
    border: 1px solid rgba(61,106,255,0.45);
    border-radius: 16px; padding: 20px; margin-bottom: 14px;
}
.card-header {
    display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;
}
.card-title   { font-size: 13.5px; font-weight: 600; color: #fff; }
.card-subtitle{ font-size: 11px; color: #8892a4; margin-bottom: 12px; }
.card-badge   {
    font-size: 9.5px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.06em; padding: 3px 8px; border-radius: 6px;
    background: rgba(61,106,255,0.15); color: #4f7bff;
}
.card-badge-g { background: rgba(0,230,118,0.12); color: #00e676; }
.card-badge-r { background: rgba(255,68,68,0.12);  color: #ff4444; }

/* ── Metrics inside cards ── */
.metric-label {
    font-size: 9.5px; font-weight: 600; letter-spacing: 0.08em;
    text-transform: uppercase; color: #8892a4; margin-bottom: 5px;
}
.metric-value { font-size: 26px; font-weight: 700; color: #fff; letter-spacing: -0.5px; line-height: 1; }
.metric-sub   { font-size: 11px; color: #8892a4; margin-top: 4px; }

/* ── Metrics mini-grid (right panel) ── */
.metrics-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.metric-cell  {
    background: #0d1426; border: 1px solid #1e2d4a;
    border-radius: 10px; padding: 12px 14px;
}
.metric-cell-full { grid-column: 1 / -1; }

/* ── Live badge ── */
.live-dot {
    width: 8px; height: 8px; border-radius: 50%; background: #00e676;
    display: inline-block; animation: live-pulse 2s infinite;
}
@keyframes live-pulse {
    0%,100% { opacity:1; box-shadow: 0 0 0 0 rgba(0,230,118,0.5); }
    50%      { opacity:0.5; box-shadow: 0 0 0 5px rgba(0,230,118,0); }
}

/* ── Filter pills row ── */
.filter-row { display: flex; align-items: center; gap: 8px; margin-bottom: 18px; flex-wrap: wrap; }
.pill {
    background: #1a2035; border: 1px solid #2a3a5c; border-radius: 999px;
    padding: 5px 14px; color: #8892a4; font-size: 12px; display: inline-block;
}
.pill-blue {
    background: #3d6aff; border: none; border-radius: 999px;
    padding: 5px 16px; color: #fff; font-size: 12px; font-weight: 500; cursor: pointer;
}

/* ── Breadcrumb ── */
.breadcrumb { font-size: 11.5px; color: #8892a4; margin-bottom: 8px; }
.breadcrumb .bc-active { color: #4f7bff; }

/* ── Page header ── */
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 18px; }
.page-title  { font-size: 26px; font-weight: 700; color: #fff; letter-spacing: -0.5px; line-height: 1.15; }
.page-title .light { font-weight: 300; }
.page-sub    { font-size: 12.5px; color: #8892a4; margin-top: 3px; }
.header-pills { display: flex; align-items: center; gap: 8px; }
.live-status {
    display: flex; align-items: center; gap: 6px;
    background: #111827; border: 1px solid #1e2d4a; border-radius: 999px;
    padding: 6px 12px; font-size: 12px; color: #8892a4;
}
.inspect-btn {
    background: #3d6aff; border-radius: 999px; padding: 7px 16px;
    color: #fff; font-size: 12px; font-weight: 500;
}

/* ── Terminal / monospace panel ── */
.terminal {
    background: #080d1a; border: 1px solid #1e2d4a; border-radius: 12px;
    padding: 14px 16px; font-family: 'JetBrains Mono', monospace;
    font-size: 10.5px; color: #8892a4; line-height: 1.75;
}
.tk { color: #4f7bff; }   /* key   */
.tv { color: #00e676; }   /* value */
.th { color: #c084fc; }   /* hash  */
.tn { color: #ffd740; }   /* number*/

/* ── Section label ── */
.sec { font-size: 9.5px; font-weight: 700; text-transform: uppercase;
       letter-spacing: 0.09em; color: #8892a4; margin: 16px 0 10px; }

/* ── Progress bar ── */
.prog-bg { background: #1a2035; border-radius: 999px; height: 5px; overflow: hidden; margin: 6px 0 2px; }
.prog-fill { height: 5px; border-radius: 999px; background: linear-gradient(90deg, #3d6aff, #7c4dff); }

/* ── Separator ── */
.sb-sep { border: none; border-top: 1px solid #1e2d4a; margin: 10px 16px; }

/* ── Streamlit native widgets — dark override ── */
[data-testid="stMetric"] {
    background: #111827 !important; border: 1px solid #1e2d4a !important;
    border-radius: 12px !important; padding: 14px 16px !important;
}
[data-testid="stMetricLabel"] p { color: #8892a4 !important; font-size: 11px !important; }
[data-testid="stMetricValue"]   { color: #fff !important; font-size: 22px !important; font-weight: 700 !important; }

[data-testid="stTextInput"] input {
    background: #0d1426 !important; border: 1px solid #1e2d4a !important;
    color: #fff !important; border-radius: 8px !important; font-size: 13px !important;
}
[data-testid="stTextInput"] input:focus { border-color: #3d6aff !important; }

.stButton > button {
    background: #3d6aff !important; border: none !important;
    color: #fff !important; border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important; font-weight: 500 !important;
    font-size: 13px !important; transition: background 0.15s !important;
}
.stButton > button:hover { background: #4f7bff !important; }

[data-testid="stTabs"] [role="tablist"]  { border-bottom: 1px solid #1e2d4a !important; }
[data-testid="stTabs"] button           { color: #8892a4 !important; }
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #4f7bff !important; border-bottom-color: #3d6aff !important;
}

[data-testid="stAlert"] { background: #111827 !important; border-color: #1e2d4a !important; }
.stDataFrame { background: #111827 !important; }

/* ── Column gaps ── */
[data-testid="stHorizontalBlock"] { gap: 14px !important; align-items: stretch !important; }
[data-testid="column"] { min-width: 0 !important; }
[data-testid="stPlotlyChart"] > div { padding: 0 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Imports & session state
# ─────────────────────────────────────────────────────────────────────────────
import modules.m1_pow_monitor as m1
import modules.m2_block_header as m2
import modules.m3_difficulty_history as m3
import modules.m4_ai_component as m4

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

# ─────────────────────────────────────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def load_data() -> dict:
    try:
        blocks = m1.get_latest_blocks(n=100)
        if not blocks:
            return dict(ok=False, error="Blockstream returned no blocks")

        latest = blocks[0]
        latest["hash"] = latest.get("id") or latest.get("hash") or ""

        block_times   = m1.get_block_times(blocks)
        difficulty    = m1.get_difficulty(latest)
        hashrate      = m1.get_hashrate(difficulty)
        next_retarget = m1.get_next_retarget(latest.get("height"))
        leading_zeros = m1.count_leading_zeros(latest.get("hash") or "")

        diff_df   = m3.get_difficulty_history(n_periods=20)
        anomalies = m4.detect_anomalies(block_times)
        metrics   = m4.evaluate(block_times, anomalies)

        try:
            raw_hdr      = m2.get_raw_header(latest["hash"])
            header_fields = m2.parse_header(raw_hdr)
            pow_result    = m2.verify_pow(raw_hdr)
        except Exception:
            header_fields = m2.parse_header_from_block(latest)
            pow_result    = {}

        return dict(
            ok=True, latest=latest, block_times=block_times,
            difficulty=difficulty, hashrate=hashrate,
            next_retarget=next_retarget, leading_zeros=leading_zeros,
            diff_df=diff_df, anomalies=anomalies, metrics=metrics,
            header_fields=header_fields, pow_result=pow_result,
        )
    except Exception as exc:
        return dict(ok=False, error=str(exc))


D  = load_data()
ok = D.get("ok", False)

# ─────────────────────────────────────────────────────────────────────────────
# Dark chart theme helper
# ─────────────────────────────────────────────────────────────────────────────
_CREMAP = {
    "#6366f1": "#3d6aff",  "#f43f5e": "#ff4444",
    "#22c55e": "#00e676",  "#ef4444": "#ff4444",
    "#94a3b8": "#8892a4",  "#f59e0b": "#ffd740",
    "#a78bfa": "#7c4dff",  "#10b981": "#00e676",
}

def _dark(fig, h: int = 260):
    """Apply dark navy theme to any Plotly figure in-place."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#8892a4", size=11),
        margin=dict(l=8, r=8, t=8, b=8),
        height=h,
        legend=dict(bgcolor="rgba(0,0,0,0)", font_color="#8892a4", font_size=10),
    )
    axis = dict(gridcolor="#1e2d4a", linecolor="#1e2d4a",
                tickcolor="#8892a4", zeroline=False)
    try: fig.update_xaxes(**axis)
    except Exception: pass
    try: fig.update_yaxes(**axis)
    except Exception: pass

    for tr in fig.data:
        try:
            c = getattr(tr.marker, "color", None)
            if isinstance(c, str) and c in _CREMAP:
                tr.marker.color = _CREMAP[c]
        except Exception: pass
        try:
            lc = getattr(tr.line, "color", None)
            if isinstance(lc, str) and lc in _CREMAP:
                tr.line.color = _CREMAP[lc]
        except Exception: pass
    return fig


_CFG = {"displayModeBar": False}

# ─────────────────────────────────────────────────────────────────────────────
# Pre-compute display strings
# ─────────────────────────────────────────────────────────────────────────────
if ok:
    _h   = D["latest"].get("height", 0)
    _d   = D["difficulty"]
    _hr  = D["hashrate"]
    _lz  = D["leading_zeros"]
    _nr  = D["next_retarget"]
    _m   = D["metrics"]

    height_s  = f"{_h:,}"
    diff_s    = f"{_d/1e12:.2f} T"        if _d  else "—"
    hr_s      = f"{_hr/1e18:.2f} EH/s"   if _hr else "—"
    lz_s      = str(_lz)                  if _lz is not None else "—"
    nr_s      = str(_nr)                  if _nr is not None else "—"
    ar_s      = f"{_m['anomaly_rate']*100:.1f}%"
    mean_s    = f"{_m['mean_interval']:.0f} s"
    ks_s      = f"{_m['ks_pvalue']:.3f}"
    fast_n    = _m["fast_blocks"]
    slow_n    = _m["slow_blocks"]
    n_anom    = _m["n_anomalies"]
    prog_nr   = int((2016 - (_h % 2016 or 2016)) / 2016 * 100)
else:
    height_s = diff_s = hr_s = lz_s = nr_s = ar_s = mean_s = ks_s = "—"
    fast_n = slow_n = n_anom = prog_nr = 0

now_s = datetime.now(timezone.utc).strftime("%d %b %Y")
ts_s  = datetime.now(timezone.utc).strftime("%H:%M UTC")

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
NAV = {
    "Dashboard":       "⬡",
    "M1 PoW Monitor":  "📊",
    "M2 Block Header": "🔍",
    "M3 Difficulty":   "📈",
    "M4 Anomalies":    "🤖",
    "── ──":           " ",      # visual separator
    "Settings":        "⚙️",
}

with st.sidebar:
    # ── Logo ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="padding:22px 16px 18px;border-bottom:1px solid #1e2d4a;margin-bottom:10px">
      <div style="display:flex;align-items:center;gap:10px">
        <div style="width:34px;height:34px;flex-shrink:0;
             background:linear-gradient(135deg,#3d6aff,#7c4dff);
             border-radius:9px;display:flex;align-items:center;
             justify-content:center;font-size:17px">₿</div>
        <div>
          <div style="font-size:14px;font-weight:700;color:#fff;letter-spacing:-0.3px">CryptoChain</div>
          <div style="font-size:10px;color:#3d5a8a;margin-top:1px">Analyzer v2</div>
        </div>
      </div>
    </div>
    <div style="padding:4px 22px 8px;font-size:9.5px;font-weight:700;
         text-transform:uppercase;letter-spacing:0.09em;color:#3d5a8a">Menu</div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "nav",
        options=[k for k in NAV if k != "── ──"],
        format_func=lambda k: f"{NAV[k]}  {k}",
        label_visibility="collapsed",
        key="nav_radio",
    )

    # ── Bottom status ─────────────────────────────────────────────────────────
    st.markdown("<hr class='sb-sep'>", unsafe_allow_html=True)
    dot   = "#00e676" if ok else "#ff4444"
    label = "API Connected" if ok else "API Offline"
    st.markdown(f"""
    <div style="padding:0 12px 16px">
      <div style="background:#080d1a;border:1px solid #1e2d4a;border-radius:10px;
           padding:10px 12px">
        <div style="display:flex;align-items:center;gap:7px;font-size:11px;color:#8892a4">
          <div style="width:7px;height:7px;border-radius:50%;background:{dot};flex-shrink:0"></div>
          {label}
        </div>
        <div style="font-size:10px;color:#3d5a8a;margin-top:4px">{now_s} · {ts_s}</div>
        <div style="font-size:10px;color:#3d5a8a">↻ auto-refresh 60 s</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Refresh button
    if st.button("↻  Refresh data", use_container_width=True, key="sidebar_refresh"):
        st.cache_data.clear()
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# SHARED HEADER (breadcrumb + title + filter pills)
# ─────────────────────────────────────────────────────────────────────────────
def _page_header(title_bold: str, title_light: str, subtitle: str, badge: str = "") -> None:
    badge_html = f'<span class="card-badge card-badge-g">{badge}</span>' if badge else ""
    st.markdown(f"""
    <div class="breadcrumb">Home / Dashboard / <span class="bc-active">{title_bold}</span></div>
    <div class="page-header">
      <div>
        <div class="page-title">{title_bold} <span class="light">{title_light}</span></div>
        <div class="page-sub">{subtitle}</div>
      </div>
      <div class="header-pills">
        {badge_html}
        <div class="live-status">
          <span class="live-dot"></span>
          Block #{height_s}
        </div>
        <div class="inspect-btn">Inspect Block</div>
      </div>
    </div>
    <div class="filter-row">
      <span class="pill">Mainnet ▾</span>
      <span class="pill">Live ▾</span>
      <span class="pill">Last 100 blocks ▾</span>
      <span class="pill-blue">↻ Refresh</span>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE — DASHBOARD (overview)
# ─────────────────────────────────────────────────────────────────────────────
def render_dashboard() -> None:
    _page_header("Bitcoin", "Cryptographic Analytics",
                 "Live proof-of-work analysis · No financial data", "Live" if ok else "Offline")

    if not ok:
        st.error(f"⚠ API unavailable: {D.get('error')} — retrying on next refresh.")
        return

    left, right = st.columns([3, 2], gap="medium")

    # ── LEFT COLUMN ───────────────────────────────────────────────────────────
    with left:
        # M1 — Inter-arrival histogram
        st.markdown("""<div class="crypto-card">
          <div class="card-header">
            <span class="card-title">📊 M1 — Inter-arrival Distribution</span>
            <span class="card-badge">Exp(λ=1/600 s)</span>
          </div>
          <div class="card-subtitle">Last 100 blocks · theoretical overlay in red</div>
        </div>""", unsafe_allow_html=True)
        if D["block_times"]:
            st.plotly_chart(
                _dark(m1.plot_block_time_histogram(D["block_times"])),
                use_container_width=True, config=_CFG,
            )

        # M3 — Difficulty history
        st.markdown("""<div class="crypto-card">
          <div class="card-header">
            <span class="card-title">📈 M3 — Difficulty History</span>
            <span class="card-badge">20 epochs</span>
          </div>
          <div class="card-subtitle">Retarget events marked · 2016-block epochs</div>
        </div>""", unsafe_allow_html=True)
        if D["diff_df"] is not None and not D["diff_df"].empty:
            st.plotly_chart(
                _dark(m3.plot_difficulty_history(D["diff_df"])),
                use_container_width=True, config=_CFG,
            )

        # M4 — Anomaly scatter (blue gradient card)
        ar_badge = f"{ar_s} anomalous"
        st.markdown(f"""<div class="crypto-card-blue">
          <div class="card-header">
            <span class="card-title" style="color:#fff">🤖 M4 — Anomaly Detector</span>
            <span class="card-badge card-badge-r">{ar_badge}</span>
          </div>
          <div class="card-subtitle" style="color:rgba(255,255,255,0.6)">
            Z-score on log(T) · Exp(λ=1/600 s) baseline · 95 % CI band shown
          </div>
        </div>""", unsafe_allow_html=True)
        if D["block_times"]:
            st.plotly_chart(
                _dark(m4.plot_anomalies(D["block_times"], D["anomalies"])),
                use_container_width=True, config=_CFG,
            )

    # ── RIGHT COLUMN ──────────────────────────────────────────────────────────
    with right:
        # Live Metrics grid
        st.markdown('<div class="crypto-card">', unsafe_allow_html=True)
        st.markdown("""<div class="card-header">
          <span class="card-title">Live Metrics</span>
          <span class="card-badge card-badge-g">Real-time</span>
        </div>
        <div class="card-subtitle">Decoded from latest block header</div>""",
                    unsafe_allow_html=True)

        st.markdown(f"""<div class="metrics-grid">
          <div class="metric-cell">
            <div class="metric-label">Block Height</div>
            <div class="metric-value" style="font-size:20px">{height_s}</div>
            <div class="metric-sub">mainnet tip</div>
          </div>
          <div class="metric-cell">
            <div class="metric-label">Leading Zero Bits</div>
            <div class="metric-value" style="font-size:20px">{lz_s}</div>
            <div class="metric-sub">256-bit target</div>
          </div>
          <div class="metric-cell">
            <div class="metric-label">Difficulty</div>
            <div class="metric-value" style="font-size:17px">{diff_s}</div>
            <div class="metric-sub">compact bits</div>
          </div>
          <div class="metric-cell">
            <div class="metric-label">Hash Rate</div>
            <div class="metric-value" style="font-size:17px">{hr_s}</div>
            <div class="metric-sub">D × 2³² / 600</div>
          </div>
          <div class="metric-cell metric-cell-full">
            <div class="metric-label">Next Retarget</div>
            <div style="display:flex;align-items:center;justify-content:space-between">
              <div class="metric-value" style="font-size:17px">{nr_s} blocks</div>
              <div style="font-size:10px;color:#8892a4">{2016 - (prog_nr*2016//100)} / 2016</div>
            </div>
            <div class="prog-bg">
              <div class="prog-fill" style="width:{100-prog_nr}%"></div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Block Header terminal
        hf = D["header_fields"]
        pr = D["pow_result"]
        valid_icon = "✓" if pr.get("valid") else "·"
        valid_color = "#00e676" if pr.get("valid") else "#8892a4"

        def _row(k, v, cls="tv"):
            v_str = str(v)[:38] + ("…" if len(str(v)) > 38 else "")
            return f'<span class="tk">{k}</span> <span class="ts">=</span> <span class="{cls}">{v_str}</span><br>'

        rows = "".join([
            _row("version",     hf.get("version", "—"), "tn"),
            _row("timestamp",   hf.get("timestamp", "—"), "ts"),
            _row("bits",        hf.get("bits", "—"), "tn"),
            _row("nonce",       hf.get("nonce", "—"), "tn"),
            _row("merkle_root", hf.get("merkle_root", "—")[:24] + "…", "th"),
            _row("prev_hash",   hf.get("prev_hash",   "—")[:24] + "…", "th"),
        ])
        pow_badge = f'<span style="color:{valid_color}">SHA-256d {valid_icon} {pr.get("leading_zeros","—")} leading zero bits</span>'

        st.markdown(f"""<div class="crypto-card">
          <div class="card-header">
            <span class="card-title">🔍 M2 — Block Header</span>
            <span class="card-badge">80 bytes · LE</span>
          </div>
          <div class="card-subtitle">6 protocol fields + PoW verification</div>
          <div class="terminal">{rows}<br>{pow_badge}</div>
        </div>""", unsafe_allow_html=True)

        # M4 stats card
        st.markdown(f"""<div class="crypto-card">
          <div class="card-header">
            <span class="card-title">Anomaly Stats</span>
            <span class="card-badge card-badge-r">{n_anom} flagged</span>
          </div>
          <div class="card-subtitle">Z-score · log(T) · KS test</div>
          <div class="terminal">
            <span class="tk">model</span>      = <span class="tv">Exp(λ=1/600 s)</span><br>
            <span class="tk">method</span>     = <span class="tv">Z-score(log T)</span><br>
            <span class="tk">threshold</span>  = <span class="tn">|Z| &gt; 3</span><br>
            <br>
            <span class="tk">mean_interval</span> = <span class="tn">{mean_s}</span><br>
            <span class="tk">fast_blocks</span>   = <span class="tv">{fast_n}</span>  <span class="ts">(&lt; 60 s)</span><br>
            <span class="tk">slow_blocks</span>   = <span class="tn">{slow_n}</span>  <span class="ts">(&gt; 1800 s)</span><br>
            <span class="tk">ks_pvalue</span>     = <span class="tn">{ks_s}</span><br>
          </div>
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE — M1 PoW Monitor
# ─────────────────────────────────────────────────────────────────────────────
def render_m1() -> None:
    _page_header("M1", "PoW Monitor",
                 "Inter-arrival time distribution · Difficulty · Hash rate estimation")

    if not ok:
        st.error(f"⚠ {D.get('error')}"); return

    c1, c2, c3, c4 = st.columns(4)
    for col, label, val, sub in [
        (c1, "Block Height",     height_s, "mainnet tip"),
        (c2, "Difficulty",       diff_s,   "from bits field"),
        (c3, "Hash Rate",        hr_s,     "D × 2³² / 600"),
        (c4, "Next Retarget",    nr_s + " blk", "2016-block epoch"),
    ]:
        col.metric(label, val, sub)

    st.markdown('<div class="sec">Inter-arrival Time Distribution — last 100 blocks</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="crypto-card">', unsafe_allow_html=True)
    st.markdown("""<div class="card-header">
      <span class="card-title">Histogram vs Exp(λ=1/600 s)</span>
      <span class="card-badge">Kolmogorov-Smirnov tested</span>
    </div>
    <div class="card-subtitle">
      Bars = observed · Red dashed = theoretical PDF · Amber = observed mean
    </div>""", unsafe_allow_html=True)
    if D["block_times"]:
        st.plotly_chart(
            _dark(m1.plot_block_time_histogram(D["block_times"]), h=320),
            use_container_width=True, config=_CFG,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="sec">Leading Zero Bits</div>', unsafe_allow_html=True)
    st.markdown(f"""<div class="crypto-card">
      <div class="terminal">
        <span class="tk">bits_field</span> = <span class="tn">0x{D["latest"].get("bits",0):08x}</span><br>
        <span class="tk">target</span>     = MAX_TARGET / difficulty<br>
        <span class="tk">leading_zeros</span> = <span class="tv">{lz_s}</span> bits
        <span class="ts">&nbsp;→ prob ≈ 2⁻{lz_s} per attempt</span><br>
        <span class="tk">hashrate_est</span>  = <span class="tn">{hr_s}</span>
        <span class="ts">&nbsp;= D × 2³² / 600</span>
      </div>
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE — M2 Block Header
# ─────────────────────────────────────────────────────────────────────────────
def render_m2() -> None:
    _page_header("M2", "Block Header Analyzer",
                 "Raw 80-byte header · 6 fields (little-endian) · SHA-256d manual verification")

    tab_live, tab_custom = st.tabs(["Latest Block", "Custom Hash"])

    with tab_live:
        if not ok:
            st.error(f"⚠ {D.get('error')}"); return

        hf = D["header_fields"]
        pr = D["pow_result"]

        c1, c2, c3 = st.columns(3)
        c1.metric("Leading Zero Bits", pr.get("leading_zeros", "—"), "SHA-256d verified")
        c2.metric("bits field",        hf.get("bits", "—"), "compact target")
        c3.metric("nonce",             f"{hf.get('nonce', 0):,}", "32-bit LE")

        valid_c = "#00e676" if pr.get("valid") else "#ff4444"
        valid_t = "✓  VALID — hash meets target" if pr.get("valid") else "✗  INVALID"

        st.markdown(f"""<div class="crypto-card">
          <div class="card-header">
            <span class="card-title">6 Header Fields</span>
            <span class="card-badge">80 bytes · little-endian</span>
          </div>
          <div class="card-subtitle">All multi-byte fields stored in LE; hashes reversed for display</div>
          <div class="terminal">
            <span class="tk">version</span>     = <span class="tn">{hf.get("version","—")}</span><br>
            <span class="tk">timestamp</span>   = <span class="tv">{hf.get("timestamp","—")}</span><br>
            <span class="tk">bits</span>        = <span class="tn">{hf.get("bits","—")}</span><br>
            <span class="tk">nonce</span>       = <span class="tn">{hf.get("nonce","—"):,}</span><br>
            <span class="tk">prev_hash</span>   = <span class="th">{hf.get("prev_hash","—")[:48]}…</span><br>
            <span class="tk">merkle_root</span> = <span class="th">{hf.get("merkle_root","—")[:48]}…</span>
          </div>
        </div>""", unsafe_allow_html=True)

        computed_hash = pr.get("hash", "—")
        st.markdown(f"""<div class="crypto-card">
          <div class="card-header">
            <span class="card-title">SHA-256d Verification</span>
            <span style="color:{valid_c};font-size:13px;font-weight:600">{valid_t}</span>
          </div>
          <div class="card-subtitle">double_sha256(header_bytes)[::-1].hex() — only hashlib, no external libs</div>
          <div class="terminal">
            <span class="tk">computed</span> = <span class="th">{computed_hash[:32]}</span><br>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            <span class="th">{computed_hash[32:] if computed_hash != "—" else ""}</span><br>
            <span class="tk">target</span>   = <span class="ts">{str(pr.get("target_hex","—"))[:48]}…</span><br>
            <span class="tk">valid</span>    = <span style="color:{valid_c}">{pr.get("valid","—")}</span>
          </div>
        </div>""", unsafe_allow_html=True)

    with tab_custom:
        st.markdown('<div class="crypto-card">', unsafe_allow_html=True)
        st.markdown("""<div class="card-header">
          <span class="card-title">Verify any block</span>
          <span class="card-badge">Blockstream API</span>
        </div>
        <div class="card-subtitle">Enter any 64-char block hash to fetch, parse and verify its header</div>""",
                    unsafe_allow_html=True)

        block_hash = st.text_input(
            "Block hash (64 hex chars)",
            placeholder="0000000000000000000322e71c…",
            key="m2_custom_hash",
        )
        if st.button("Parse & Verify", key="m2_verify_btn") and block_hash:
            with st.spinner("Fetching header…"):
                try:
                    raw    = m2.get_raw_header(block_hash.strip())
                    fields = m2.parse_header(raw)
                    result = m2.verify_pow(raw)
                    vc     = "#00e676" if result["valid"] else "#ff4444"
                    vt     = "✓  VALID" if result["valid"] else "✗  INVALID"
                    ch     = result["hash"]
                    st.markdown(f"""<div class="terminal" style="margin-top:12px">
                      <span class="tk">version</span>     = <span class="tn">{fields["version"]}</span><br>
                      <span class="tk">timestamp</span>   = <span class="tv">{fields["timestamp"]}</span><br>
                      <span class="tk">bits</span>        = <span class="tn">{fields["bits"]}</span><br>
                      <span class="tk">nonce</span>       = <span class="tn">{fields["nonce"]:,}</span><br>
                      <span class="tk">prev_hash</span>   = <span class="th">{fields["prev_hash"][:48]}…</span><br>
                      <span class="tk">merkle_root</span> = <span class="th">{fields["merkle_root"][:48]}…</span><br>
                      <br>
                      <span class="tk">SHA-256d</span>    = <span class="th">{ch[:32]}</span><br>
                      &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                      <span class="th">{ch[32:]}</span><br>
                      <span class="tk">leading_zeros</span> = <span class="tv">{result["leading_zeros"]}</span> bits<br>
                      <span class="tk">valid</span>       = <span style="color:{vc}">{vt}</span>
                    </div>""", unsafe_allow_html=True)
                except Exception as exc:
                    st.error(f"Error: {exc}")
        elif not block_hash:
            st.info("Enter a block hash above.")
        st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE — M3 Difficulty History
# ─────────────────────────────────────────────────────────────────────────────
def render_m3() -> None:
    _page_header("M3", "Difficulty History",
                 "~20 retarget epochs · actual_time/ratio per epoch · dual-axis hashrate chart")

    if not ok or D["diff_df"] is None or D["diff_df"].empty:
        st.error(f"⚠ {D.get('error','No difficulty data')}"); return

    df = D["diff_df"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Latest Difficulty",  f"{df['difficulty'].iloc[-1]/1e12:.2f} T")
    c2.metric("Epochs loaded",      len(df))
    c3.metric("Mean ratio",         f"{df['ratio'].mean():.3f}",
              "1.000 = perfect 14-day epoch")
    c4.metric("Difficulty change",
              f"{(df['difficulty'].iloc[-1]/df['difficulty'].iloc[0]-1)*100:+.1f}%")

    st.markdown('<div class="sec">Difficulty over Retarget Epochs</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="crypto-card">', unsafe_allow_html=True)
    st.markdown("""<div class="card-header">
      <span class="card-title">Difficulty (T) per Epoch</span>
      <span class="card-badge">Retarget events marked ◆</span>
    </div>
    <div class="card-subtitle">
      Each marker = one retarget · ratio = actual_time / (2016 × 600 s)
    </div>""", unsafe_allow_html=True)
    st.plotly_chart(
        _dark(m3.plot_difficulty_history(df), h=300),
        use_container_width=True, config=_CFG,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="sec">Hash Rate vs Difficulty</div>', unsafe_allow_html=True)
    st.markdown('<div class="crypto-card">', unsafe_allow_html=True)
    st.markdown("""<div class="card-header">
      <span class="card-title">Dual-axis: EH/s (solid) · Difficulty T (dashed)</span>
    </div>""", unsafe_allow_html=True)
    st.plotly_chart(
        _dark(m3.plot_hashrate_vs_difficulty(df), h=280),
        use_container_width=True, config=_CFG,
    )
    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE — M4 Anomaly Detector
# ─────────────────────────────────────────────────────────────────────────────
def render_m4() -> None:
    _page_header("M4", "Anomaly Detector",
                 "Z-score on log(T) · Exp(λ=1/600 s) baseline · fast / slow classification",
                 f"{n_anom} anomalies")

    if not ok:
        st.error(f"⚠ {D.get('error')}"); return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Anomaly Rate",  ar_s,    "Z-score |Z|>3")
    c2.metric("Fast blocks",   fast_n,  "< 60 s")
    c3.metric("Slow blocks",   slow_n,  "> 1800 s")
    c4.metric("KS p-value",    ks_s,    "vs Exp(λ=1/600)")

    st.markdown('<div class="sec">Scatter: Inter-arrival Times</div>', unsafe_allow_html=True)
    st.markdown('<div class="crypto-card-blue">', unsafe_allow_html=True)
    st.markdown("""<div class="card-header">
      <span class="card-title" style="color:#fff">Anomaly Detection Scatter</span>
    </div>
    <div class="card-subtitle" style="color:rgba(255,255,255,0.6)">
      ▲ green = fast (&lt;60s) · ▼ red = slow (&gt;1800s) · shaded = 95% CI of Exp(λ=1/600)
    </div>""", unsafe_allow_html=True)
    st.plotly_chart(
        _dark(m4.plot_anomalies(D["block_times"], D["anomalies"]), h=320),
        use_container_width=True, config=_CFG,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # Comparison histogram
    st.markdown('<div class="sec">Distribution vs Theoretical</div>', unsafe_allow_html=True)
    st.markdown('<div class="crypto-card">', unsafe_allow_html=True)
    st.markdown("""<div class="card-header">
      <span class="card-title">Inter-arrival Histogram</span>
      <span class="card-badge">Exp(λ=1/600 s) overlay</span>
    </div>""", unsafe_allow_html=True)
    st.plotly_chart(
        _dark(m1.plot_block_time_histogram(D["block_times"]), h=260),
        use_container_width=True, config=_CFG,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # Anomaly table
    if D["anomalies"]["indices"]:
        import pandas as pd
        st.markdown('<div class="sec">Flagged Intervals</div>', unsafe_allow_html=True)
        adf = pd.DataFrame({
            "index":   D["anomalies"]["indices"],
            "time (s)": [f"{t:.1f}" for t in D["anomalies"]["times"]],
            "Z-score":  [f"{z:.2f}"  for z in D["anomalies"]["z_scores"]],
            "label":    D["anomalies"]["labels"],
        })
        st.dataframe(adf, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE — Settings
# ─────────────────────────────────────────────────────────────────────────────
def render_settings() -> None:
    _page_header("Settings", "& About",
                 "Project info · API sources · checkpoint status")

    st.markdown("""<div class="crypto-card">
      <div class="card-header">
        <span class="card-title">Project Info</span>
        <span class="card-badge">UAX · Criptografía</span>
      </div>
      <div class="terminal">
        <span class="tk">student</span>    = <span class="tv">Ariel</span><br>
        <span class="tk">github</span>     = <span class="tv">Arielnv77</span><br>
        <span class="tk">professor</span>  = <span class="tv">Jorge Calvo</span><br>
        <span class="tk">course</span>     = <span class="tv">Criptografía · UAX 2025-26</span><br>
        <span class="tk">deadline</span>   = <span class="tn">14 May 2026</span><br>
        <span class="tk">checkpoint</span> = <span class="tv">29 Apr 2026 · M1+M2+M3+M4 done</span>
      </div>
    </div>""", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""<div class="crypto-card">
          <div class="card-title" style="margin-bottom:12px">Module Status</div>
          <div class="terminal">
            <span class="tv">✓</span> M1 PoW Monitor<br>
            <span class="tv">✓</span> M2 Block Header (SHA-256d)<br>
            <span class="tv">✓</span> M3 Difficulty History<br>
            <span class="tv">✓</span> M4 Anomaly Detector (AI)<br>
            <span class="ts">·</span> M5 Merkle Proof (optional)<br>
            <span class="ts">·</span> M6 Security Score (optional)
          </div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class="crypto-card">
          <div class="card-title" style="margin-bottom:12px">API Sources</div>
          <div class="terminal">
            <span class="tk">primary</span>  = <span class="tv">blockstream.info/api</span><br>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="ts">no API key required</span><br>
            <span class="tk">charts</span>   = <span class="tv">api.blockchain.info/charts</span><br>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="ts">difficulty time series</span><br>
            <span class="tk">refresh</span>  = <span class="tn">60 s</span> auto
          </div>
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────────────────────────────────
_ROUTES = {
    "Dashboard":       render_dashboard,
    "M1 PoW Monitor":  render_m1,
    "M2 Block Header": render_m2,
    "M3 Difficulty":   render_m3,
    "M4 Anomalies":    render_m4,
    "Settings":        render_settings,
}

_ROUTES.get(page, render_dashboard)()
