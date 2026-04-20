"""Heuristic AI-style analysis based on blockchain indicators."""

import streamlit as st

from api.blockchain_client import (
    BlockchainClientError,
    get_difficulty_history,
    get_latest_block,
    summarize_difficulty,
)


def _generate_insights(block: dict[str, object], change_pct: float) -> list[str]:
    insights = []

    tx_count = block.get("tx_count")
    if isinstance(tx_count, int):
        if tx_count > 3000:
            insights.append("The latest block carries a high transaction count, which may indicate elevated network demand.")
        else:
            insights.append("The latest block carries a moderate transaction count, suggesting normal short-term network activity.")

    difficulty = block.get("difficulty")
    if isinstance(difficulty, (int, float)):
        if change_pct > 5:
            insights.append("Difficulty has risen over the selected history window, so mining conditions appear to be getting tougher.")
        elif change_pct < -5:
            insights.append("Difficulty has fallen over the selected history window, which may reflect a temporary easing in mining pressure.")
        else:
            insights.append("Difficulty is relatively stable across the selected history window, with no strong structural shift.")

    nonce = block.get("nonce")
    if isinstance(nonce, int):
        insights.append(f"The latest block nonce is {nonce:,}, a reminder of the repeated trial-and-error process behind proof of work.")

    if not insights:
        insights.append("Not enough data was available to generate heuristic observations.")
    return insights


def render() -> None:
    """Render the M4 panel."""
    st.header("M4 - AI Component")
    st.write("Rule-based insight generator that explains recent blockchain conditions in plain language.")

    days = st.selectbox("Context window", options=[30, 60, 90, 180], index=2, key="m4_days")

    if st.button("Generate AI insight", key="m4_generate"):
        with st.spinner("Analyzing blockchain signals..."):
            try:
                block = get_latest_block()
                history = get_difficulty_history(days)
                summary = summarize_difficulty(history)
                insights = _generate_insights(block, summary.change_pct)

                st.subheader("Generated insights")
                for insight in insights:
                    st.write(f"- {insight}")

                st.subheader("Why this counts as AI")
                st.write(
                    "This module uses a simple expert-system approach: it converts numeric blockchain signals "
                    "into human-readable conclusions using explicit decision rules."
                )
            except BlockchainClientError as exc:
                st.error(f"Error generating insights: {exc}")
