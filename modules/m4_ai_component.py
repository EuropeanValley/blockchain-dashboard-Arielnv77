"""M4 — Anomaly Detector (AI Component).

Baseline model: Bitcoin inter-block arrival times follow Exp(λ = 1/600 s).

Detection method: Z-score on log-transformed times (log-Gumbel approach).
  • If T ~ Exp(λ), then log(T) has a Gumbel-like distribution.
  • Standardising log(T) via Z-score is more sensitive than standardising T
    directly, because the raw Exp distribution is heavily right-skewed.
  • Anomaly criterion: |Z| > 3  (≈ 0.27 % of a Gaussian falls outside ±3σ).

Block classification:
  fast   — inter-arrival time < 60 s   (likely competing miner / orphan race)
  slow   — inter-arrival time > 1800 s (hashrate drop / pool outage signal)
  outlier— |Z| > 3 but 60 s ≤ t ≤ 1800 s

95 % confidence interval for Exp(λ=1/600 s):
  lower = −600 · ln(0.975) ≈  15.2 s
  upper = −600 · ln(0.025) ≈ 2212 s
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from scipy import stats


# ─── Detection ───────────────────────────────────────────────────────────────

def detect_anomalies(
    block_times: list[float],
    threshold: float = 3.0,
) -> dict[str, list]:
    """Detect anomalous inter-arrival times via Z-score on log(T).

    Returns a dict:
      indices  — list[int]   positions of anomalous intervals
      times    — list[float] actual seconds at each anomaly index
      z_scores — list[float] Z-score of log(T) at each anomaly
      labels   — list[str]   'fast' | 'slow' | 'outlier'
    """
    empty: dict[str, list] = {
        "indices": [], "times": [], "z_scores": [], "labels": [],
    }

    if len(block_times) < 10:
        print("[M4] Not enough block times for anomaly detection (need ≥ 10)")
        return empty

    arr      = np.array(block_times, dtype=float)
    log_t    = np.log(arr + 1e-9)              # avoid log(0)
    z_all    = stats.zscore(log_t, ddof=1)     # sample Z-score

    indices: list[int]   = []
    times:   list[float] = []
    z_scores: list[float]= []
    labels:  list[str]   = []

    for i in np.where(np.abs(z_all) > threshold)[0]:
        t = float(arr[i])
        if t < 60:
            label = "fast"
        elif t > 1800:
            label = "slow"
        else:
            label = "outlier"

        indices.append(int(i))
        times.append(t)
        z_scores.append(float(z_all[i]))
        labels.append(label)

    print(
        f"[M4] Detected {len(indices)} anomalies in {len(block_times)} intervals "
        f"(fast={labels.count('fast')}, slow={labels.count('slow')}, "
        f"outlier={labels.count('outlier')})"
    )
    return {"indices": indices, "times": times, "z_scores": z_scores, "labels": labels}


# ─── Evaluation ──────────────────────────────────────────────────────────────

def evaluate(
    block_times: list[float],
    anomalies: dict[str, list],
) -> dict[str, float | int]:
    """Compute evaluation metrics for the anomaly detector.

    Returns:
      anomaly_rate    — fraction of intervals flagged
      mean_interval   — observed mean (≈ 600 s under normal conditions)
      std_interval    — standard deviation
      fast_blocks     — count of intervals < 60 s
      slow_blocks     — count of intervals > 1800 s
      expected_lambda — 1/600 (the theoretical rate)
      lambda_fit      — MLE estimate = 1 / mean_interval
      ks_pvalue       — KS test p-value vs Exp(λ=1/600); high p = data consistent
      n_total         — total intervals analysed
      n_anomalies     — number flagged
    """
    n = len(block_times)
    if n == 0:
        return {
            "anomaly_rate": 0.0, "mean_interval": 0.0, "std_interval": 0.0,
            "fast_blocks": 0, "slow_blocks": 0,
            "expected_lambda": 1 / 600, "lambda_fit": 0.0,
            "ks_pvalue": 0.0, "n_total": 0, "n_anomalies": 0,
        }

    arr     = np.array(block_times, dtype=float)
    mean_t  = float(arr.mean())
    std_t   = float(arr.std(ddof=1))
    lam_fit = 1.0 / mean_t if mean_t > 0 else 0.0

    _, ks_p = stats.kstest(arr, "expon", args=(0, 600.0))

    labels = anomalies.get("labels", [])
    return {
        "anomaly_rate":    len(anomalies.get("indices", [])) / n,
        "mean_interval":   mean_t,
        "std_interval":    std_t,
        "fast_blocks":     int(sum(1 for t in arr if t < 60)),
        "slow_blocks":     int(sum(1 for t in arr if t > 1800)),
        "expected_lambda": 1 / 600,
        "lambda_fit":      lam_fit,
        "ks_pvalue":       float(ks_p),
        "n_total":         n,
        "n_anomalies":     len(anomalies.get("indices", [])),
    }


# ─── Plot ────────────────────────────────────────────────────────────────────

def plot_anomalies(
    block_times: list[float],
    anomalies: dict[str, list],
) -> go.Figure:
    """Scatter plot of inter-arrival times with anomaly classification.

    Visual encoding:
      • grey small dots  — normal intervals
      • green ▲ (up)     — fast anomaly  (t < 60 s)  colour #22c55e
      • red   ▼ (down)   — slow anomaly  (t > 1800 s) colour #ef4444
      • amber ◆          — outlier anomaly (|Z|>3, 60≤t≤1800)
      • dashed amber line — target E[T] = 600 s
      • shaded band       — 95 % confidence interval of Exp(λ=1/600)
    """
    arr = np.array(block_times, dtype=float)
    n   = len(arr)

    # 95 % CI bounds for Exp(λ = 1/600)
    ci_low  = -600.0 * np.log(0.975)   # ≈  15.2 s
    ci_high = -600.0 * np.log(0.025)   # ≈ 2212 s

    # Build index → label map
    idx_label = {
        i: lbl
        for i, lbl in zip(
            anomalies.get("indices", []),
            anomalies.get("labels",  []),
        )
    }
    anom_set = set(anomalies.get("indices", []))

    # Separate point groups
    def _xy(predicate):
        xs = [i for i in range(n) if predicate(i)]
        ys = [float(arr[i]) for i in xs]
        return xs, ys

    norm_x,    norm_y    = _xy(lambda i: i not in anom_set)
    fast_x,    fast_y    = _xy(lambda i: idx_label.get(i) == "fast")
    slow_x,    slow_y    = _xy(lambda i: idx_label.get(i) == "slow")
    other_x,   other_y   = _xy(lambda i: i in anom_set and idx_label.get(i) not in ("fast", "slow"))

    fig = go.Figure()

    # 95 % confidence band (shaded region)
    fig.add_hrect(
        y0=ci_low,
        y1=ci_high,
        fillcolor="rgba(99,102,241,0.07)",
        line_width=0,
        annotation_text="95 % CI [Exp(1/600)]",
        annotation_position="top left",
        annotation_font_size=9,
        annotation_font_color="#6366f1",
    )

    # Target line at 600 s
    fig.add_hline(
        y=600,
        line=dict(color="#f59e0b", width=1.5, dash="dash"),
        annotation_text="E[T] = 600 s",
        annotation_font_size=10,
        annotation_font_color="#f59e0b",
    )

    # Normal intervals
    fig.add_trace(go.Scatter(
        x=norm_x,
        y=norm_y,
        mode="markers",
        name="Normal",
        marker=dict(color="#94a3b8", size=4, opacity=0.65),
    ))

    # Fast anomalies — green triangle-up
    if fast_x:
        fig.add_trace(go.Scatter(
            x=fast_x,
            y=fast_y,
            mode="markers",
            name="Fast anomaly (< 60 s)",
            marker=dict(color="#22c55e", size=11, symbol="triangle-up",
                        line=dict(color="#fff", width=1)),
        ))

    # Slow anomalies — red triangle-down
    if slow_x:
        fig.add_trace(go.Scatter(
            x=slow_x,
            y=slow_y,
            mode="markers",
            name="Slow anomaly (> 1800 s)",
            marker=dict(color="#ef4444", size=11, symbol="triangle-down",
                        line=dict(color="#fff", width=1)),
        ))

    # Outlier anomalies — amber diamond
    if other_x:
        fig.add_trace(go.Scatter(
            x=other_x,
            y=other_y,
            mode="markers",
            name="Outlier (|Z| > 3)",
            marker=dict(color="#f59e0b", size=10, symbol="diamond",
                        line=dict(color="#fff", width=1)),
        ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Space Grotesk", color="#374151", size=12),
        margin=dict(l=8, r=8, t=8, b=8),
        height=260,
        legend=dict(x=0.01, y=0.97, bgcolor="rgba(0,0,0,0)", font_size=10),
        xaxis=dict(
            title="Block index",
            gridcolor="rgba(0,0,0,0.06)",
            zeroline=False,
        ),
        yaxis=dict(
            title="Inter-arrival time (s)",
            gridcolor="rgba(0,0,0,0.06)",
            zeroline=False,
        ),
    )
    return fig


# ─── Standalone Streamlit tab (legacy) ───────────────────────────────────────

def render() -> None:
    import streamlit as st
    from modules.m1_pow_monitor import get_latest_blocks, get_block_times

    st.header("M4 — Anomaly Detector")
    st.caption(
        "Z-score on log(T) · baseline Exp(λ=1/600 s) · "
        "fast < 60 s · slow > 1800 s"
    )

    @st.cache_data(ttl=60)
    def _load(n: int):
        return get_latest_blocks(n)

    n = st.slider("Blocks to analyse", 30, 200, 100, key="m4_n")

    if st.button("Run detector", key="m4_run"):
        with st.spinner("Fetching blocks and running anomaly detection…"):
            blocks    = _load(n)
            if not blocks:
                st.error("Could not fetch blocks from Blockstream API.")
                return
            times     = get_block_times(blocks)
            anomalies = detect_anomalies(times)
            metrics   = evaluate(times, anomalies)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Anomaly rate",  f"{metrics['anomaly_rate']*100:.1f}%")
            c2.metric("Mean interval", f"{metrics['mean_interval']:.0f} s")
            c3.metric("Fast blocks",   metrics["fast_blocks"])
            c4.metric("Slow blocks",   metrics["slow_blocks"])

            st.plotly_chart(plot_anomalies(times, anomalies), use_container_width=True)

            with st.expander("Full metrics"):
                st.json(metrics)
            with st.expander("Detected anomalies"):
                rows = [
                    {"index": i, "time_s": f"{t:.1f}", "z": f"{z:.2f}", "label": lbl}
                    for i, t, z, lbl in zip(
                        anomalies["indices"],
                        anomalies["times"],
                        anomalies["z_scores"],
                        anomalies["labels"],
                    )
                ]
                if rows:
                    import pandas as pd
                    st.dataframe(pd.DataFrame(rows))
                else:
                    st.success("No anomalies detected in this sample.")
    else:
        st.info("Click 'Run detector' to analyse recent block inter-arrival times.")
