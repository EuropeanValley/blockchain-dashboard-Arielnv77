"""M3 — Difficulty History.

Fetches ~280 days of difficulty data from blockchain.info Charts API
(≈ 20 retarget epochs × 14 days each).

Each retarget epoch spans exactly 2016 blocks. The function identifies
adjustment events (points where difficulty changed ≥ 0.5%) and builds a
tidy DataFrame with one row per epoch:

  height       — estimated block height at the retarget boundary
  difficulty   — network difficulty after the adjustment
  timestamp    — Unix seconds of the adjustment
  date         — UTC datetime
  actual_time  — seconds elapsed since the previous retarget
  ratio        — actual_time / (2016 × 600)  [<1 = fast epoch, >1 = slow]
  hashrate_ehs — estimated hash rate (EH/s) = difficulty × 2³² / 600 / 1e18
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from api.blockchain_client import BlockchainClientError
from api.blockchain_client import get_difficulty_history as _fetch_chart_data

# Bitcoin genesis block Unix timestamp
_GENESIS_TS      = 1_231_006_505
# Target epoch duration: 2016 blocks × 600 s/block
_EPOCH_TARGET_S  = 2016 * 600          # 1 209 600 s ≈ 14 days
# Minimum pct-change to count as a retarget event in sampled data
_CHANGE_THRESHOLD = 0.005              # 0.5 %


# ─── Data fetching ────────────────────────────────────────────────────────────

def get_difficulty_history(n_periods: int = 20) -> pd.DataFrame:
    """Return a DataFrame with one row per retarget epoch.

    Columns: height, difficulty, timestamp, date, actual_time, ratio,
             hashrate_ehs.

    Fetches n_periods × 14 days of daily-sampled difficulty data from
    blockchain.info, then filters to retarget adjustment events.
    """
    days = n_periods * 14
    try:
        raw = _fetch_chart_data(days=days)
    except BlockchainClientError as exc:
        print(f"[M3] API error: {exc}")
        return pd.DataFrame()

    df = pd.DataFrame(raw)
    df = df.rename(columns={"x": "timestamp", "y": "difficulty"})
    df["date"]       = pd.to_datetime(df["timestamp"], unit="s", utc=True)
    df = df.sort_values("timestamp").reset_index(drop=True)

    # ── Identify retarget events (significant difficulty changes) ── #
    df["pct_change"]    = df["difficulty"].pct_change().fillna(0)
    df["is_adjustment"] = df["pct_change"].abs() >= _CHANGE_THRESHOLD

    epochs = df[df["is_adjustment"]].copy().reset_index(drop=True)

    if epochs.empty:
        # Fallback: treat every data point as an epoch if no adjustments found
        epochs = df.copy().reset_index(drop=True)

    # ── Derived columns ── #

    # actual_time: seconds elapsed since the previous retarget
    epochs["actual_time"] = (
        epochs["timestamp"].diff().fillna(_EPOCH_TARGET_S).astype(float)
    )

    # ratio: how far actual epoch time deviated from the 14-day target
    epochs["ratio"] = epochs["actual_time"] / _EPOCH_TARGET_S

    # Estimated height (round to nearest 2016-block boundary)
    epochs["height"] = (
        ((epochs["timestamp"] - _GENESIS_TS) / 600)
        .astype(int)
        .floordiv(2016)
        .mul(2016)
    )

    # Estimated hashrate in EH/s
    epochs["hashrate_ehs"] = (
        epochs["difficulty"] * (2 ** 32) / 600 / 1e18
    )

    print(f"[M3] Loaded {len(epochs)} retarget epochs ({days}-day window)")
    return epochs[[
        "date", "height", "difficulty", "timestamp",
        "actual_time", "ratio", "hashrate_ehs",
    ]].reset_index(drop=True)


# ── backward-compat alias ────────────────────────────────────────────────────
def get_difficulty_history_df(n_periods: int = 20) -> pd.DataFrame:
    return get_difficulty_history(n_periods)


# ─── Plots ────────────────────────────────────────────────────────────────────

def plot_difficulty_history(df: pd.DataFrame) -> go.Figure:
    """Line chart of difficulty over time with retarget markers.

    Color scheme (per spec):
      • line   : #6366f1 (indigo)
      • markers: #f43f5e (rose-red)
    """
    if df.empty:
        return go.Figure()

    fig = go.Figure()

    # Difficulty line (filled area)
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["difficulty"] / 1e12,
        mode="lines",
        name="Difficulty (T)",
        line=dict(color="#6366f1", width=2),
        fill="tozeroy",
        fillcolor="rgba(99,102,241,0.08)",
    ))

    # Every row is a retarget — mark all of them
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["difficulty"] / 1e12,
        mode="markers",
        name="Retarget event",
        marker=dict(color="#f43f5e", size=7, symbol="diamond",
                    line=dict(color="#fff", width=1)),
    ))

    # Ratio annotation: colour the ratio line above/below 1
    fig.add_hline(
        y=float(df["difficulty"].median() / 1e12),
        line=dict(color="rgba(0,0,0,0)"),   # invisible; just for spacing
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Space Grotesk", color="#374151", size=12),
        margin=dict(l=8, r=8, t=8, b=8),
        height=260,
        legend=dict(x=0.02, y=0.95, bgcolor="rgba(0,0,0,0)", font_size=11),
        xaxis=dict(title="Date", gridcolor="rgba(0,0,0,0.06)", zeroline=False),
        yaxis=dict(title="Difficulty (T)", gridcolor="rgba(0,0,0,0.06)", zeroline=False),
    )
    return fig


def plot_hashrate_vs_difficulty(df: pd.DataFrame) -> go.Figure:
    """Dual-axis chart: hashrate (EH/s) vs difficulty.

    Color scheme (per spec):
      • hashrate  : #6366f1 solid
      • difficulty: #a78bfa dashed
    """
    if df.empty:
        return go.Figure()

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["hashrate_ehs"],
        mode="lines",
        name="Hash rate (EH/s)",
        line=dict(color="#6366f1", width=2),
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["difficulty"] / 1e12,
        mode="lines",
        name="Difficulty (T)",
        line=dict(color="#a78bfa", width=2, dash="dash"),
    ), secondary_y=True)

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Space Grotesk", color="#374151", size=12),
        margin=dict(l=8, r=8, t=8, b=8),
        height=260,
        legend=dict(x=0.02, y=0.95, bgcolor="rgba(0,0,0,0)", font_size=11),
    )
    fig.update_yaxes(
        title_text="Hash rate (EH/s)",
        gridcolor="rgba(0,0,0,0.06)",
        zeroline=False,
        secondary_y=False,
    )
    fig.update_yaxes(
        title_text="Difficulty (T)",
        gridcolor="rgba(0,0,0,0.06)",
        zeroline=False,
        secondary_y=True,
    )
    fig.update_xaxes(title_text="Date", gridcolor="rgba(0,0,0,0.06)", zeroline=False)
    return fig


# ─── Standalone Streamlit tab (legacy) ───────────────────────────────────────

def render() -> None:
    import streamlit as st

    st.header("M3 — Difficulty History")
    st.caption("Last ~20 retarget epochs · blockchain.info Charts API")

    n_periods = st.slider("Epochs to show", 5, 30, 20, key="m3_periods")

    if st.button("Load chart", key="m3_load"):
        with st.spinner("Fetching difficulty history…"):
            df = get_difficulty_history(n_periods)
            if df.empty:
                st.error("Could not load difficulty history. Try again later.")
                return

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Latest difficulty",  f"{df['difficulty'].iloc[-1] / 1e12:.2f} T")
            c2.metric("Retarget epochs",     len(df))
            c3.metric("Mean ratio",          f"{df['ratio'].mean():.3f}")
            c4.metric(
                "Difficulty change",
                f"{(df['difficulty'].iloc[-1]/df['difficulty'].iloc[0]-1)*100:+.1f}%",
            )

            st.plotly_chart(plot_difficulty_history(df), use_container_width=True)
            st.plotly_chart(plot_hashrate_vs_difficulty(df), use_container_width=True)

            with st.expander("Raw epoch data"):
                st.dataframe(df[["date", "height", "difficulty", "actual_time", "ratio"]])
    else:
        st.info("Click 'Load chart' to display difficulty history.")
