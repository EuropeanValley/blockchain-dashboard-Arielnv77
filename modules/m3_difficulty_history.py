"""Difficulty history visualization module."""

import pandas as pd
import plotly.express as px
import streamlit as st

from api.blockchain_client import BlockchainClientError, get_difficulty_history, summarize_difficulty


def render() -> None:
    """Render the M3 panel."""
    st.header("M3 - Difficulty History")
    st.write("Plot recent Bitcoin mining difficulty and summarize the trend.")

    days = st.slider("History window (days)", min_value=30, max_value=365, value=90, key="m3_days")

    if st.button("Load difficulty chart", key="m3_load"):
        with st.spinner("Fetching data..."):
            try:
                values = get_difficulty_history(days)
                df = pd.DataFrame(values)
                df["x"] = pd.to_datetime(df["x"], unit="s")
                df = df.rename(columns={"x": "Date", "y": "Difficulty"})
                summary = summarize_difficulty(values)

                col1, col2, col3 = st.columns(3)
                col1.metric("Latest difficulty", f"{summary.latest:,.2f}")
                col2.metric("Average difficulty", f"{summary.average:,.2f}")
                col3.metric("Change", f"{summary.change_pct:+.2f}%")

                fig = px.line(df, x="Date", y="Difficulty", title="Bitcoin Mining Difficulty")
                st.plotly_chart(fig, use_container_width=True)
            except BlockchainClientError as exc:
                st.error(f"Error loading chart: {exc}")
    else:
        st.info("Click Load difficulty chart to display the chart.")
