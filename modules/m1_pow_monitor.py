"""Proof-of-work overview for the most recent Bitcoin block."""

import streamlit as st

from api.blockchain_client import BlockchainClientError, get_latest_block


def _format_number(value: object) -> str:
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return "N/A"


def render() -> None:
    """Render the M1 panel."""
    st.header("M1 - Proof of Work Monitor")
    st.write("Live summary of the latest Bitcoin block and its proof-of-work fields.")

    if st.button("Fetch latest block", key="m1_fetch"):
        with st.spinner("Fetching data..."):
            try:
                block = get_latest_block()
                st.success(f"Latest block loaded: #{block.get('height')}")

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Block height", _format_number(block.get("height")))
                col2.metric("Transactions", _format_number(block.get("tx_count")))
                col3.metric("Difficulty", _format_number(block.get("difficulty")))
                col4.metric("Nonce", _format_number(block.get("nonce")))

                st.caption(f"Timestamp: {block.get('time') or 'N/A'}")
                st.code(str(block.get("hash") or "N/A"), language="text")

                with st.expander("See normalized block payload"):
                    st.json(block)
            except BlockchainClientError as exc:
                st.error(f"Error fetching data: {exc}")
    else:
        st.info("Click the button to load the latest block from the API.")
