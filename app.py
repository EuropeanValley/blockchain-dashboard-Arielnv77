"""Simple Streamlit entry point for the student project."""

import streamlit as st

from api.blockchain_client import get_api_sources
from modules.m1_pow_monitor import render as render_m1
from modules.m2_block_header import render as render_m2
from modules.m3_difficulty_history import render as render_m3
from modules.m4_ai_component import render as render_m4

st.set_page_config(page_title="CryptoChain Analyzer Dashboard", layout="wide")

st.title("CryptoChain Analyzer Dashboard")
st.caption("Streamlit dashboard fed by three Bitcoin data APIs.")

with st.expander("Current data sources", expanded=False):
    for source in get_api_sources():
        st.write(f"- **{source['name']}**: {source['role']}")

tab1, tab2, tab3, tab4 = st.tabs(
    ["M1 - PoW Monitor", "M2 - Block Header", "M3 - Difficulty History", "M4 - AI Component"]
)

with tab1:
    render_m1()

with tab2:
    render_m2()

with tab3:
    render_m3()

with tab4:
    render_m4()
