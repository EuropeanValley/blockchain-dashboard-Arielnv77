"""CryptoChain Analyzer Dashboard — entry point.

Run with:  streamlit run app.py
Auto-refreshes every 60 s via streamlit-autorefresh.
All data is cached with ttl=60 so a page reload never fires more than one
batch of API requests per minute.
"""

from __future__ import annotations

import streamlit as st
from streamlit_autorefresh import st_autorefresh

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="CryptoChain Analyzer",
    page_icon="⛓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Auto-refresh every 60 s
st_autorefresh(interval=60_000, key="global_refresh")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Hide Streamlit chrome ── */
#MainMenu, header[data-testid="stHeader"], footer,
[data-testid="stSidebar"], [data-testid="collapsedControl"],
[data-testid="stDecoration"], .stDeployButton { display: none !important; }

/* ── Global ── */
*, *::before, *::after { box-sizing: border-box; }
html, body, .stApp { font-family: 'Space Grotesk', sans-serif; }

.stApp {
    background-color: #f0ebe5 !important;
    background-image:
        radial-gradient(ellipse at 18% 55%, rgba(192,132,252,0.10) 0%, transparent 55%),
        radial-gradient(ellipse at 82% 15%, rgba(99,102,241,0.07) 0%, transparent 50%);
    min-height: 100vh;
}

/* ── Main container ── */
.block-container {
    padding: 28px 36px 48px !important;
    max-width: 1440px !important;
}

/* ── Glass card (white) ── */
.gc {
    background: rgba(255,255,255,0.55);
    border: 1px solid rgba(255,255,255,0.78);
    border-radius: 20px;
    padding: 20px 22px;
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    box-shadow: 0 4px 24px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04);
    transition: box-shadow 0.2s ease, transform 0.2s ease;
}
.gc:hover {
    box-shadow: 0 8px 36px rgba(0,0,0,0.10), 0 2px 8px rgba(0,0,0,0.05);
    transform: translateY(-1px);
}

/* ── Dark card ── */
.dc {
    background: #1e1e2e;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 20px;
    padding: 20px 22px;
    box-shadow: 0 4px 28px rgba(0,0,0,0.20);
}

/* ── Topbar ── */
.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 0 20px 0;
}
.topbar-logo { font-size: 17px; font-weight: 700; color: #1a1a2e; letter-spacing: -0.3px; }
.topbar-logo span { color: #c084fc; }
.pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(255,255,255,0.72);
    border: 1px solid rgba(255,255,255,0.9);
    border-radius: 50px;
    padding: 5px 14px;
    font-size: 13px;
    font-weight: 500;
    color: #374151;
    backdrop-filter: blur(8px);
    margin-left: 8px;
}
.dot { width: 8px; height: 8px; border-radius: 50%; background: #22c55e;
       animation: pulse 2s infinite; display: inline-block; }
.dot-off { background: #ef4444; animation: none; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.35} }

/* ── Hero ── */
.hero { padding: 4px 0 28px 0; }
.hero h1 {
    font-size: 52px; font-weight: 700; color: #1a1a2e;
    margin: 0 0 6px 0; letter-spacing: -2px; line-height: 1.08;
}
.hero-sub { font-size: 18px; font-style: italic; color: #c084fc; font-weight: 400; margin: 0; }

/* ── Section label ── */
.sec {
    font-size: 10.5px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 1.1px; color: #9ca3af; margin: 20px 0 10px 2px;
}

/* ── Metric inside glass card ── */
.mlabel {
    font-size: 10.5px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.7px; color: #9ca3af; margin-bottom: 7px;
}
.mvalue { font-size: 30px; font-weight: 700; color: #1a1a2e; letter-spacing: -0.8px; line-height: 1; }
.msub { font-size: 11.5px; color: #6b7280; margin-top: 5px; }
.badge {
    display: inline-block; border-radius: 7px; padding: 2px 9px;
    font-size: 10.5px; font-weight: 600; margin-top: 8px;
    background: rgba(192,132,252,0.14); color: #7c3aed;
}
.badge-g { background: rgba(34,197,94,0.14); color: #15803d; }
.badge-o { background: rgba(249,115,22,0.14); color: #c2410c; }
.badge-r { background: rgba(239,68,68,0.14); color: #b91c1c; }

/* ── Chart card header ── */
.ctitle { font-size: 13.5px; font-weight: 600; color: #374151; margin-bottom: 2px; }
.csub { font-size: 10.5px; color: #9ca3af; margin-bottom: 10px; }

/* ── Mono / code inside dark cards ── */
.mono {
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
    color: #94a3b8; word-break: break-all; line-height: 1.7;
}
.kw  { color: #c084fc; }
.val { color: #86efac; }
.key { color: #7dd3fc; }
.ok  { color: #86efac; font-size: 20px; font-weight: 700; }
.bad { color: #f87171; font-size: 20px; font-weight: 700; }

/* ── Block header table ── */
.htable { width: 100%; border-collapse: collapse; margin-top: 8px; }
.htable td { padding: 5px 6px; font-size: 11.5px; vertical-align: top; }
.htable td:first-child { color: #9ca3af; white-space: nowrap; padding-right: 12px; }
.htable td:last-child {
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
    color: #374151; word-break: break-all;
}

/* ── Columns gap ── */
[data-testid="stHorizontalBlock"] { gap: 14px !important; align-items: stretch !important; }
[data-testid="column"] { min-width: 0 !important; }

/* ── Plotly charts: remove default padding ── */
[data-testid="stPlotlyChart"] > div { padding: 0 !important; }
iframe { border: none !important; }
</style>
""", unsafe_allow_html=True)

# ── Imports ───────────────────────────────────────────────────────────────────
import modules.m1_pow_monitor as m1
import modules.m2_block_header as m2
import modules.m3_difficulty_history as m3
import modules.m4_ai_component as m4


# ── Data loading (cached 60 s) ────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def load_data() -> dict:
    try:
        # M1: fetch 100 most recent blocks directly via m1
        blocks = m1.get_latest_blocks(n=100)
        if not blocks:
            return dict(ok=False, error="Blockstream API returned no blocks")

        # Normalise latest block for metrics
        latest_block = blocks[0]
        latest_block["hash"] = latest_block.get("id") or latest_block.get("hash") or ""

        # Derived metrics
        block_times   = m1.get_block_times(blocks)
        difficulty    = m1.get_difficulty(latest_block)
        hashrate      = m1.get_hashrate(difficulty)
        next_retarget = m1.get_next_retarget(latest_block.get("height"))
        leading_zeros = m1.count_leading_zeros(latest_block.get("hash") or "")

        # M3: difficulty history DataFrame
        diff_df = m3.get_difficulty_history(n_periods=20)

        # M4: anomaly detection (returns dict) then evaluate
        anomalies = m4.detect_anomalies(block_times)
        metrics   = m4.evaluate(block_times, anomalies)      # note arg order

        return dict(
            ok=True,
            latest_block=latest_block,
            diff_df=diff_df,
            block_times=block_times,
            difficulty=difficulty,
            hashrate=hashrate,
            next_retarget=next_retarget,
            leading_zeros=leading_zeros,
            anomalies=anomalies,      # dict with indices/times/z_scores/labels
            metrics=metrics,
        )
    except Exception as exc:  # noqa: BLE001
        return dict(ok=False, error=str(exc))


with st.spinner("Loading live Bitcoin data…"):
    D = load_data()

ok = D.get("ok", False)

# ── Topbar ────────────────────────────────────────────────────────────────────
height_str = f"{D['latest_block']['height']:,}" if ok else "—"
dot_cls = "dot" if ok else "dot dot-off"

st.markdown(f"""
<div class="topbar">
  <div class="topbar-logo">Crypto<span>Chain</span> Analyzer</div>
  <div>
    <span class="pill"><span class="{dot_cls}"></span>{'Mainnet · Live' if ok else 'API Offline'}</span>
    <span class="pill">Block #{height_str}</span>
    <span class="pill">&#8635; 60 s</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>Bitcoin PoW<br>Analytics</h1>
  <p class="hero-sub">Cryptographic analysis &middot; No financial data</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ROW 1 — 5 Metric Cards
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec">Live Metrics</div>', unsafe_allow_html=True)

if ok:
    hr_str   = f"{D['hashrate']/1e18:.2f} EH/s" if D["hashrate"] else "—"
    diff_str = f"{D['difficulty']/1e12:.2f} T"   if D["difficulty"] else "—"
    lz_str   = str(D["leading_zeros"])             if D["leading_zeros"] is not None else "—"
    nr_str   = str(D["next_retarget"])             if D["next_retarget"] is not None else "—"
    ar_str   = f"{D['metrics']['anomaly_rate']*100:.1f}%"
    # separate fast / slow counts for the anomaly card
    fast_n   = D["metrics"]["fast_blocks"]
    slow_n   = D["metrics"]["slow_blocks"]
else:
    hr_str = diff_str = lz_str = nr_str = ar_str = "—"
    fast_n = slow_n = 0

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown(f"""<div class="gc">
      <div class="mlabel">Block Height</div>
      <div class="mvalue">{height_str}</div>
      <div class="msub">Bitcoin mainnet</div>
      <div class="badge badge-g">Live</div>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""<div class="gc">
      <div class="mlabel">Est. Hash Rate</div>
      <div class="mvalue" style="font-size:22px">{hr_str}</div>
      <div class="msub">Network-wide estimate</div>
      <div class="badge">D &times; 2&sup3;&sup2; / 600</div>
    </div>""", unsafe_allow_html=True)

with c3:
    st.markdown(f"""<div class="gc">
      <div class="mlabel">Difficulty</div>
      <div class="mvalue" style="font-size:22px">{diff_str}</div>
      <div class="msub">Current epoch</div>
      <div class="badge badge-o">compact bits</div>
    </div>""", unsafe_allow_html=True)

with c4:
    st.markdown(f"""<div class="gc">
      <div class="mlabel">Leading Zero Bits</div>
      <div class="mvalue">{lz_str}</div>
      <div class="msub">Hash prefix depth</div>
      <div class="badge">256-bit target</div>
    </div>""", unsafe_allow_html=True)

with c5:
    st.markdown(f"""<div class="gc">
      <div class="mlabel">Next Retarget</div>
      <div class="mvalue">{nr_str}</div>
      <div class="msub">Blocks remaining</div>
      <div class="badge">2016-block epoch</div>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ROW 2 — 3 Chart Cards
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec">Cryptographic Analysis</div>', unsafe_allow_html=True)

ch1, ch2, ch3 = st.columns(3)

with ch1:
    st.markdown("""<div class="gc">
      <div class="ctitle">Inter-arrival Time Distribution</div>
      <div class="csub">Exp(&lambda;=1/600 s) overlay &middot; last 100 blocks</div>
    </div>""", unsafe_allow_html=True)
    if ok and D["block_times"]:
        st.plotly_chart(
            m1.plot_block_time_histogram(D["block_times"]),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    else:
        st.info("No block time data available.")

with ch2:
    st.markdown("""<div class="gc">
      <div class="ctitle">Difficulty History</div>
      <div class="csub">Last 20 retarget epochs &middot; adjustments marked</div>
    </div>""", unsafe_allow_html=True)
    if ok and D["diff_df"] is not None and not D["diff_df"].empty:
        st.plotly_chart(
            m3.plot_difficulty_history(D["diff_df"]),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    else:
        st.info("No difficulty history available.")

with ch3:
    st.markdown(f"""<div class="gc">
      <div class="ctitle">Anomaly Detection &middot; M4</div>
      <div class="csub">Z-score on log-times &middot; &sigma; threshold = 3 &middot;
        <span class="badge badge-r" style="margin:0 0 0 4px">{ar_str} anomalous</span>
      </div>
    </div>""", unsafe_allow_html=True)
    if ok and D["block_times"]:
        st.plotly_chart(
            m4.plot_anomalies(D["block_times"], D["anomalies"]),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    else:
        st.info("No anomaly data available.")

# ─────────────────────────────────────────────────────────────────────────────
# ROW 3 — 2 Dark Code Cards + 1 Block Header Card
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec">Block Inspection</div>', unsafe_allow_html=True)

d1, d2, d3 = st.columns(3)

# ── Dark card 1: SHA-256d verification ───────────────────────────────────────
with d1:
    if ok:
        bh       = D["latest_block"].get("hash") or ""
        bits_val = D["latest_block"].get("bits") or 0
        ver_cls = ver_txt = hash_top = hash_bot = lz_disp = bits_hex = ""
        try:
            # m2.get_raw_header returns bytes; m2.verify_pow accepts bytes → dict
            raw_bytes = m2.get_raw_header(bh)
            result    = m2.verify_pow(raw_bytes)
            computed  = result["hash"]
            ver_cls   = "ok" if result["valid"] else "bad"
            ver_txt   = "&#10003; VALID" if result["valid"] else "&#10007; INVALID"
            hash_top  = computed[:32]
            hash_bot  = computed[32:]
            lz_disp   = str(result["leading_zeros"])
            bits_hex  = hex(bits_val)
        except Exception:
            ver_cls, ver_txt = "val", "&#8212;"
            hash_top  = bh[:32] if bh else "—"
            hash_bot  = bh[32:] if bh else ""
            lz_disp   = str(D["leading_zeros"]) if D["leading_zeros"] is not None else "—"
            bits_hex  = hex(bits_val) if bits_val else "—"
    else:
        ver_cls, ver_txt = "val", "&#8212;"
        hash_top = hash_bot = "—"
        lz_disp = bits_hex = "—"

    st.markdown(f"""<div class="dc">
      <div class="mlabel" style="color:#6b7280">SHA-256d Verification</div>
      <div class="{ver_cls}" style="margin:8px 0 12px">{ver_txt}</div>
      <div class="mono">
        <span class="key">double_sha256</span>(<span class="val">header_bytes</span>)<br>
        = <span class="val">{hash_top}</span><br>
        &nbsp;&nbsp;<span class="val">{hash_bot}</span><br><br>
        <span class="key">leading_zeros</span> = <span class="kw">{lz_disp}</span> bits<br>
        <span class="key">bits_field</span>&nbsp;&nbsp; = <span class="kw">{bits_hex}</span>
      </div>
    </div>""", unsafe_allow_html=True)

# ── Dark card 2: Anomaly stats ────────────────────────────────────────────────
with d2:
    if ok:
        m     = D["metrics"]
        ar_d  = f"{m['anomaly_rate']*100:.2f}%"
        mi_d  = f"{m['mean_interval']:.1f} s"
        si_d  = f"{m['std_interval']:.1f} s"
        ksp_d = f"{m['ks_pvalue']:.4f}"
        lam_v = m["lambda_fit"]
        lam_d = f"1/{1/lam_v:.0f}s" if lam_v > 0 else "—"
        n_a   = m["n_anomalies"]
        fb_d  = m["fast_blocks"]
        sb_d  = m["slow_blocks"]
    else:
        ar_d = mi_d = si_d = ksp_d = lam_d = "—"
        n_a = fb_d = sb_d = 0

    st.markdown(f"""<div class="dc">
      <div class="mlabel" style="color:#6b7280">Anomaly Detector &mdash; M4 AI</div>
      <div class="mono" style="margin-top:10px">
        <span class="key">model</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; = <span class="kw">Exp(&lambda;=1/600 s)</span><br>
        <span class="key">method</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; = <span class="val">Z-score(log T)</span><br>
        <span class="key">threshold</span>&nbsp;&nbsp; = <span class="kw">|Z| &gt; 3</span><br><br>
        <span class="key">anomaly_rate</span>&nbsp;&nbsp; = <span class="val">{ar_d}</span><br>
        <span class="key">mean_interval</span>&nbsp; = <span class="val">{mi_d}</span><br>
        <span class="key">std_interval</span>&nbsp;&nbsp; = <span class="val">{si_d}</span><br>
        <span class="key">ks_pvalue</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; = <span class="val">{ksp_d}</span><br>
        <span class="key">lambda_fit</span>&nbsp;&nbsp;&nbsp;&nbsp; = <span class="kw">{lam_d}</span><br>
        <span class="key">fast_blocks</span>&nbsp;&nbsp;&nbsp; = <span class="kw">{fb_d}</span> (&lt; 60 s)<br>
        <span class="key">slow_blocks</span>&nbsp;&nbsp;&nbsp; = <span class="kw">{sb_d}</span> (&gt; 1800 s)<br>
        <span class="key">n_anomalies</span>&nbsp;&nbsp;&nbsp; = <span class="kw">{n_a}</span>
      </div>
    </div>""", unsafe_allow_html=True)

# ── Glass card 3: Block Header fields ─────────────────────────────────────────
with d3:
    if ok:
        lb = D["latest_block"]
        try:
            # m2.get_raw_header → bytes; m2.parse_header(bytes) → dict
            raw_hdr       = m2.get_raw_header(lb.get("hash") or "")
            header_fields = m2.parse_header(raw_hdr)
        except Exception:
            header_fields = m2.parse_header_from_block(lb)
    else:
        header_fields = {}

    rows_html = "".join(
        f"<tr><td>{k}</td><td>{v}</td></tr>"
        for k, v in header_fields.items()
    )
    st.markdown(f"""<div class="gc">
      <div class="ctitle">Block Header &mdash; 6 Fields</div>
      <div class="csub">80 bytes &middot; little-endian &middot; latest block</div>
      <table class="htable">{rows_html}</table>
    </div>""", unsafe_allow_html=True)

# ── Error banner ──────────────────────────────────────────────────────────────
if not ok:
    st.error(
        f"&#9888; API unavailable: {D.get('error', 'unknown error')}  —  "
        "dashboard will retry automatically on next refresh."
    )
