"""M1 — Proof-of-Work Monitor.

All PoW mathematics follows the Bitcoin protocol specification:
  target     = mantissa × 2^(8*(exponent-3))      (compact bits encoding)
  difficulty = MAX_TARGET / target
  hashrate   ≈ difficulty × 2³² / block_time_s     (H/s)

Fetches live data directly from the Blockstream REST API; no API key required.
"""

from __future__ import annotations

import requests
import numpy as np
import plotly.graph_objects as go

# ----- constants ------------------------------------------------------------ #
BLOCKSTREAM = "https://blockstream.info/api"
DEFAULT_TIMEOUT = 10

# Genesis difficulty-1 target (bits = 0x1d00ffff)
MAX_TARGET = 0x00000000FFFF0000000000000000000000000000000000000000000000000000


# ─── PoW math ────────────────────────────────────────────────────────────────

def bits_to_target(bits: int) -> int:
    """Decode the compact 'bits' field to the full 256-bit target integer.

    Formula: target = mantissa × 2^(8 × (exponent − 3))
    This is equivalent to mantissa × 256^(exponent-3), written with bitshift
    for clarity.
    """
    exp  = bits >> 24
    mant = bits & 0x00FFFFFF
    return mant * (1 << (8 * (exp - 3)))


def get_difficulty(block: dict) -> float | None:
    """Return mining difficulty decoded from a block's 'bits' field.

    difficulty = MAX_TARGET / target
    """
    bits = block.get("bits")
    if not isinstance(bits, int) or bits == 0:
        return None
    target = bits_to_target(bits)
    return MAX_TARGET / target if target > 0 else None


def get_hashrate(difficulty: float | None, block_time_s: float = 600.0) -> float | None:
    """Estimate network hash rate in H/s.

    H/s = difficulty × 2³² / block_time_s
    Returns None when difficulty is unavailable.
    """
    if difficulty is None:
        return None
    return difficulty * (2 ** 32) / block_time_s


def get_next_retarget(height: int | None) -> int | None:
    """Blocks remaining until the next 2016-block difficulty retarget."""
    if not isinstance(height, int):
        return None
    remainder = height % 2016
    return (2016 - remainder) if remainder != 0 else 2016


def count_leading_zeros(hash_hex: str) -> int | None:
    """Count leading zero bits in a 256-bit hash hex string."""
    if not hash_hex or len(hash_hex) != 64:
        return None
    h = int(hash_hex, 16)
    return 256 if h == 0 else 256 - h.bit_length()


# ─── Data fetching ───────────────────────────────────────────────────────────

def get_latest_blocks(n: int = 100) -> list[dict]:
    """Fetch the n most recent Bitcoin blocks from Blockstream, newest first.

    Paginates the GET /blocks[/{start_height}] endpoint which returns 10
    blocks per page. Blocks include: id, height, timestamp, bits, nonce, etc.
    Returns an empty list on any API failure (never raises).
    """
    blocks: list[dict] = []
    start_height: int | None = None

    while len(blocks) < n:
        url = f"{BLOCKSTREAM}/blocks"
        if start_height is not None:
            url += f"/{start_height}"

        try:
            resp = requests.get(url, timeout=DEFAULT_TIMEOUT)
            resp.raise_for_status()
            page: list[dict] = resp.json()
        except Exception as exc:
            print(f"[M1] API error fetching blocks page: {exc}")
            break

        if not isinstance(page, list) or not page:
            break

        blocks.extend(page)
        heights = [b["height"] for b in page if isinstance(b.get("height"), int)]
        if not heights:
            break
        start_height = min(heights) - 1

    print(f"[M1] Fetched {len(blocks)} blocks (requested {n})")
    return blocks[:n]


# ─── Time series ─────────────────────────────────────────────────────────────

def get_block_times(blocks: list[dict]) -> list[float]:
    """Return positive inter-arrival times (seconds) from a block list.

    Blocks are sorted ascending by timestamp before differencing, so the
    order returned by the API (newest-first) is handled automatically.
    """
    valid = sorted(
        [b for b in blocks if isinstance(b.get("timestamp"), (int, float))],
        key=lambda b: b["timestamp"],
    )
    times: list[float] = []
    for i in range(1, len(valid)):
        delta = float(valid[i]["timestamp"] - valid[i - 1]["timestamp"])
        if delta > 0:
            times.append(delta)
    return times


# ── alias kept for app.py compatibility ─────────────────────────────────────
calc_block_times = get_block_times


# ─── Plot ────────────────────────────────────────────────────────────────────

def plot_block_time_histogram(block_times: list[float]) -> go.Figure:
    """Histogram of inter-arrival times with Exp(λ=1/600 s) theoretical overlay.

    Color scheme:
      • observed bars : #6366f1 (indigo)
      • theoretical PDF: #f43f5e dashed (rose-red)
      • observed mean  : #f59e0b dotted (amber)
    """
    arr = np.array(block_times, dtype=float)
    n   = len(arr)
    lam = 1.0 / 600.0

    max_t    = float(arr.max())
    n_bins   = min(30, max(10, n // 3))
    bin_width = max_t / n_bins

    # Theoretical PDF scaled to expected counts
    x_pdf = np.linspace(0, max_t * 1.15, 400)
    y_pdf = n * bin_width * lam * np.exp(-lam * x_pdf)

    mean_obs = float(arr.mean())

    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=arr,
        nbinsx=n_bins,
        name="Observed",
        marker_color="#6366f1",
        opacity=0.75,
    ))

    fig.add_trace(go.Scatter(
        x=x_pdf,
        y=y_pdf,
        mode="lines",
        name="Exp(λ=1/600 s) theoretical",
        line=dict(color="#f43f5e", width=2.5, dash="dash"),
    ))

    fig.add_vline(
        x=mean_obs,
        line=dict(color="#f59e0b", width=1.5, dash="dot"),
        annotation_text=f"mean = {mean_obs:.0f} s",
        annotation_font_size=10,
        annotation_font_color="#374151",
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Space Grotesk", color="#374151", size=12),
        margin=dict(l=8, r=8, t=8, b=8),
        height=260,
        legend=dict(x=0.60, y=0.95, bgcolor="rgba(0,0,0,0)", font_size=11),
        xaxis=dict(
            title="Seconds between consecutive blocks",
            gridcolor="rgba(0,0,0,0.07)",
            zeroline=False,
        ),
        yaxis=dict(
            title="Count",
            gridcolor="rgba(0,0,0,0.07)",
            zeroline=False,
        ),
        bargap=0.05,
    )
    return fig


# ─── Standalone Streamlit tab (legacy) ───────────────────────────────────────

def render() -> None:
    import streamlit as st

    st.header("M1 — Proof of Work Monitor")
    st.caption("Inter-arrival time distribution · live data from Blockstream API")

    @st.cache_data(ttl=60)
    def _load(n: int = 100):
        return get_latest_blocks(n)

    n_blocks = st.slider("Blocks to fetch", 30, 200, 100, key="m1_n")

    if st.button("Fetch & analyse", key="m1_fetch"):
        with st.spinner("Fetching blocks…"):
            blocks = _load(n_blocks)
            if not blocks:
                st.error("Could not fetch blocks from Blockstream API.")
                return

            block = blocks[0]       # latest block (page is newest-first)
            diff   = get_difficulty(block)
            hr     = get_hashrate(diff)
            lz     = count_leading_zeros(block.get("id") or block.get("hash") or "")
            nr     = get_next_retarget(block.get("height"))
            times  = get_block_times(blocks)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Block height",     f"{block.get('height', 0):,}")
            c2.metric("Leading zero bits", str(lz) if lz is not None else "—")
            c3.metric("Difficulty",        f"{diff / 1e12:.2f} T" if diff else "—")
            c4.metric("Hash rate",         f"{hr / 1e18:.2f} EH/s" if hr else "—")

            if times:
                st.plotly_chart(plot_block_time_histogram(times), use_container_width=True)
            else:
                st.warning("Not enough timestamps to compute inter-arrival times.")
    else:
        st.info("Click 'Fetch & analyse' to load live block data.")
