"""M6 — Security Score (51 % Attack Cost).

This module estimates the economic cost of mounting a 51 % attack on the
Bitcoin network and derives a "security ratio" that contextualises that cost
against the block reward revenue an attacker could earn.

─── Theory ───────────────────────────────────────────────────────────────────

A 51 % attack requires the attacker to control more than half of the total
network hashrate.  If the honest network hashes at H (EH/s), the attacker
needs H_attack > H so that H_attack / (H + H_attack) > 50 %.

Two cost paths are modelled:

  1. RENTAL (NiceHash / cloud mining)
     cost_1h = H_needed_TH/s × nicehash_rate_USD/(TH/s·h)
     Source: NiceHash SHA-256 market prices (parameterised).

  2. PURCHASE (own hardware)
     units   = H_needed_TH/s / asic_ths_per_unit
     capex   = units × asic_price_usd
     opex_1h = units × asic_power_kw × electricity_usd_per_kwh

Security ratio = revenue from double-spend in 1 h / cost of attack for 1 h
  • Honest revenue: 6 blocks/h × block_subsidy × BTC_price_USD
  • Higher ratio → attack less likely (cost far exceeds reward).

─── API ──────────────────────────────────────────────────────────────────────

BTC price is fetched from the Blockchain.com ticker (no API key required):
  GET https://blockchain.info/ticker  → {"USD": {"last": 67500.0, ...}, ...}
"""

from __future__ import annotations

import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots

TICKER_URL      = "https://blockchain.info/ticker"
DEFAULT_TIMEOUT = 10

# ── Hardware assumptions (Bitmain Antminer S21 Pro, 2024 flagship) ── #
ASIC_MODEL          = "Antminer S21 Pro"
ASIC_THS_PER_UNIT   = 234.0        # TH/s per unit
ASIC_POWER_KW       = 3.51         # kW per unit
ASIC_PRICE_USD      = 5_000.0      # approximate market price (USD)

# ── Rental assumption (NiceHash SHA-256 average) ── #
NICEHASH_RATE       = 0.05         # USD per TH/s per hour (conservative estimate)

# ── Electricity ── #
ELECTRICITY_USD_KWH = 0.06         # USD per kWh (data-center average)

# ── Bitcoin protocol ── #
BLOCKS_PER_HOUR  = 6
BLOCK_SUBSIDY    = 3.125           # BTC (post-4th halving, April 2024)


# ─── Price fetching ───────────────────────────────────────────────────────────

def get_btc_price_usd() -> float | None:
    """Fetch the current BTC/USD price from the Blockchain.com ticker.

    Returns None on any network failure so callers can degrade gracefully.
    """
    try:
        resp = requests.get(TICKER_URL, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        price = data.get("USD", {}).get("last")
        if isinstance(price, (int, float)) and price > 0:
            print(f"[M6] BTC price: ${price:,.0f}")
            return float(price)
    except Exception as exc:
        print(f"[M6] Could not fetch BTC price: {exc}")
    return None


# ─── Attack cost calculation ─────────────────────────────────────────────────

def compute_attack_cost(hashrate_ehs: float) -> dict[str, float | int | str]:
    """Estimate the cost of a 51 % attack on a network at hashrate_ehs (EH/s).

    Returns a dict with rental path, purchase path, and model parameters.
    All monetary values in USD.
    """
    # Attacker needs H_attack ≥ current honest total hashrate
    needed_ehs = hashrate_ehs
    needed_ths = needed_ehs * 1e6          # 1 EH = 10^6 TH

    # ── Rental path ────────────────────────────────────────────────────────── #
    rental_1h   = needed_ths * NICEHASH_RATE
    rental_24h  = rental_1h  * 24
    rental_week = rental_24h * 7

    # ── Purchase path ──────────────────────────────────────────────────────── #
    units_needed   = needed_ths / ASIC_THS_PER_UNIT
    hardware_cost  = units_needed * ASIC_PRICE_USD
    electricity_1h = units_needed * ASIC_POWER_KW * ELECTRICITY_USD_KWH
    # After buying hardware, the marginal cost per hour is only electricity
    # But for a total cost estimate we amortise capex over 1 year (8760 h)
    amortised_1h   = hardware_cost / 8_760 + electricity_1h

    return {
        # Basics
        "needed_hashrate_ehs":       round(needed_ehs, 3),
        "needed_hashrate_ths":       round(needed_ths, 0),
        # Rental
        "rental_cost_1h_usd":        round(rental_1h,   2),
        "rental_cost_24h_usd":       round(rental_24h,  2),
        "rental_cost_week_usd":      round(rental_week, 2),
        # Purchase (capital expenditure)
        "asic_units_needed":         int(units_needed),
        "hardware_cost_usd":         round(hardware_cost,  0),
        "electricity_cost_1h_usd":   round(electricity_1h, 2),
        "amortised_cost_1h_usd":     round(amortised_1h,   2),
        # Parameters (for transparency)
        "asic_model":                ASIC_MODEL,
        "asic_ths_per_unit":         ASIC_THS_PER_UNIT,
        "asic_power_kw":             ASIC_POWER_KW,
        "asic_price_usd":            ASIC_PRICE_USD,
        "nicehash_rate_usd_per_ths": NICEHASH_RATE,
        "electricity_usd_kwh":       ELECTRICITY_USD_KWH,
    }


def compute_security_metrics(
    attack_cost: dict,
    btc_price_usd: float | None,
) -> dict[str, float | str]:
    """Derive high-level security metrics from the attack cost dict.

    Returns:
      revenue_1h_usd      — honest miner revenue in 1 h (6 blocks × subsidy × price)
      security_ratio      — revenue / rental_cost_1h  (higher = safer)
      security_label      — "Extremely Strong" / "Strong" / "Moderate" / "At Risk"
      attack_pct_of_day   — rental cost for 24 h as % of daily block rewards
      btc_price_usd       — price used (or None)
    """
    rental_1h = attack_cost.get("rental_cost_1h_usd", 0.0)

    if btc_price_usd and btc_price_usd > 0:
        revenue_1h = BLOCKS_PER_HOUR * BLOCK_SUBSIDY * btc_price_usd
    else:
        # Fallback: assume $60,000 per BTC
        btc_price_usd = 60_000.0
        revenue_1h    = BLOCKS_PER_HOUR * BLOCK_SUBSIDY * btc_price_usd

    ratio = revenue_1h / rental_1h if rental_1h > 0 else 0.0

    if ratio >= 0.5:
        label = "Extremely Strong"
    elif ratio >= 0.1:
        label = "Strong"
    elif ratio >= 0.02:
        label = "Moderate"
    else:
        label = "At Risk"

    rental_24h   = attack_cost.get("rental_cost_24h_usd", 0.0)
    revenue_24h  = revenue_1h * 24
    pct_of_day   = (rental_24h / revenue_24h * 100) if revenue_24h > 0 else 0.0

    return {
        "btc_price_usd":       round(btc_price_usd, 2),
        "revenue_1h_usd":      round(revenue_1h, 2),
        "security_ratio":      round(ratio, 4),
        "security_label":      label,
        "attack_pct_of_day":   round(pct_of_day, 2),
    }


# ─── Plots ────────────────────────────────────────────────────────────────────

def plot_cost_comparison(attack_cost: dict) -> go.Figure:
    """Bar chart: rental vs amortised-purchase cost at 1 h, 24 h, 1 week.

    Colors: #3d6aff rental, #7c4dff purchase.
    """
    labels = ["1 hour", "24 hours", "1 week"]

    rental_vals = [
        attack_cost["rental_cost_1h_usd"],
        attack_cost["rental_cost_24h_usd"],
        attack_cost["rental_cost_week_usd"],
    ]
    purchase_vals = [
        attack_cost["amortised_cost_1h_usd"],
        attack_cost["amortised_cost_1h_usd"] * 24,
        attack_cost["amortised_cost_1h_usd"] * 24 * 7,
    ]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Rental (NiceHash)",
        x=labels,
        y=rental_vals,
        marker_color="#3d6aff",
        text=[f"${v/1e6:.1f}M" for v in rental_vals],
        textposition="outside",
        textfont=dict(size=10),
    ))

    fig.add_trace(go.Bar(
        name="Purchase + electricity (amortised)",
        x=labels,
        y=purchase_vals,
        marker_color="#7c4dff",
        text=[f"${v/1e6:.1f}M" for v in purchase_vals],
        textposition="outside",
        textfont=dict(size=10),
    ))

    fig.update_layout(
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#8892a4", size=11),
        margin=dict(l=8, r=8, t=8, b=8),
        height=280,
        legend=dict(x=0.02, y=0.95, bgcolor="rgba(0,0,0,0)", font_size=10),
        xaxis=dict(gridcolor="#1e2d4a", zeroline=False),
        yaxis=dict(
            title="Attack cost (USD)",
            gridcolor="#1e2d4a",
            zeroline=False,
            tickformat="$,.0f",
        ),
    )
    return fig


def plot_security_gauge(security_ratio: float) -> go.Figure:
    """Gauge chart showing security_ratio capped at 1.0 for display.

    Colour bands:
      0.00 – 0.02 → red    (At Risk)
      0.02 – 0.10 → amber  (Moderate)
      0.10 – 0.50 → blue   (Strong)
      0.50 – 1.00 → green  (Extremely Strong)
    """
    display_ratio = min(security_ratio, 1.0)

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=display_ratio * 100,
        number=dict(suffix=" %", font=dict(color="#fff", size=28)),
        delta=dict(reference=10, valueformat=".1f"),
        gauge=dict(
            axis=dict(
                range=[0, 100],
                tickwidth=1,
                tickcolor="#1e2d4a",
                tickfont=dict(color="#8892a4", size=10),
            ),
            bar=dict(color="#3d6aff", thickness=0.25),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            steps=[
                dict(range=[0,   2],  color="rgba(255, 68, 68, 0.18)"),
                dict(range=[2,  10],  color="rgba(255,215, 64, 0.14)"),
                dict(range=[10, 50],  color="rgba(61, 106,255, 0.12)"),
                dict(range=[50, 100], color="rgba(0, 230,118, 0.12)"),
            ],
            threshold=dict(
                line=dict(color="#ffd740", width=3),
                thickness=0.75,
                value=display_ratio * 100,
            ),
        ),
        title=dict(text="Security Ratio (revenue / rental cost)", font=dict(color="#8892a4", size=11)),
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#8892a4", size=11),
        margin=dict(l=16, r=16, t=24, b=8),
        height=220,
    )
    return fig


# ─── Standalone Streamlit tab (legacy) ───────────────────────────────────────

def render() -> None:
    import streamlit as st

    st.header("M6 — Security Score (51 % Attack Cost)")
    st.caption(
        "Economic cost of a 51 % attack · rental vs purchase · security ratio"
    )

    st.info(
        "Requires hashrate from M1. Enter a hashrate below or use the cached value."
    )

    hashrate_ehs = st.number_input(
        "Network hashrate (EH/s)", min_value=1.0, value=700.0, step=10.0, key="m6_hr"
    )

    if st.button("Compute security score", key="m6_run"):
        with st.spinner("Fetching BTC price…"):
            price = get_btc_price_usd()
        cost    = compute_attack_cost(hashrate_ehs)
        metrics = compute_security_metrics(cost, price)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("1h rental cost",    f"${cost['rental_cost_1h_usd']/1e6:.1f}M")
        c2.metric("Hardware needed",   f"{cost['asic_units_needed']:,} ASICs")
        c3.metric("Security ratio",    f"{metrics['security_ratio']:.3f}")
        c4.metric("Security label",    metrics["security_label"])

        col_l, col_r = st.columns([3, 2])
        with col_l:
            st.plotly_chart(plot_cost_comparison(cost), use_container_width=True)
        with col_r:
            st.plotly_chart(plot_security_gauge(metrics["security_ratio"]), use_container_width=True)

        with st.expander("Full cost breakdown"):
            st.json(cost)
        with st.expander("Security metrics"):
            st.json(metrics)
