"""Proof-of-work overview for the most recent Bitcoin block."""

import streamlit as st

from api.blockchain_client import (
    BlockchainClientError,
    get_api_sources,
    get_difficulty_history,
    get_latest_block,
    get_network_snapshot,
    summarize_difficulty,
)


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

    st.subheader("APIs used in this dashboard")
    for source in get_api_sources():
        st.write(f"- **{source['name']}**: {source['role']} (`{source['base_url']}`)")

    if st.button("Fetch mining snapshot", key="m1_fetch"):
        with st.spinner("Fetching data..."):
            try:
                block = get_latest_block()
                network = get_network_snapshot()
                difficulty_summary = summarize_difficulty(get_difficulty_history(30))
                st.success(f"Latest block loaded: #{block.get('height')}")

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Block height", _format_number(block.get("height")))
                col2.metric("Transactions", _format_number(block.get("tx_count")))
                col3.metric("Difficulty", _format_number(block.get("difficulty")))
                col4.metric("Nonce", _format_number(block.get("nonce")))

                col5, col6, col7 = st.columns(3)
                col5.metric("Peers (BlockCypher)", _format_number(network.peer_count))
                col6.metric("Unconfirmed tx", _format_number(network.unconfirmed_count))
                col7.metric("30d difficulty change", f"{difficulty_summary.change_pct:+.2f}%")

                st.caption(f"Timestamp: {block.get('time') or 'N/A'}")
                st.code(str(block.get("hash") or "N/A"), language="text")

                with st.expander("See normalized block payload"):
                    st.json(block)
                with st.expander("See network snapshot"):
                    st.json(
                        {
                            "height": network.height,
                            "hash": network.hash,
                            "peer_count": network.peer_count,
                            "unconfirmed_count": network.unconfirmed_count,
                            "last_fork_height": network.last_fork_height,
                        }
                    )
            except BlockchainClientError as exc:
                st.error(f"Error fetching data: {exc}")
    else:
        st.info("Click the button to load data from the three APIs.")
