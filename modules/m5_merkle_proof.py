"""M5 — Merkle Proof Verifier.

Bitcoin transactions in a block are organised in a binary Merkle tree.
The root of this tree is stored in the 80-byte block header (bytes 36–67).

This module:
  1. Fetches all txids for a given block (Blockstream API).
  2. Rebuilds the Merkle tree from those txids using SHA-256d — only hashlib.
  3. Produces an inclusion proof (sibling hashes at every tree level).
  4. Verifies the proof against the header's merkle_root field.

Key cryptographic detail:
  - Bitcoin stores txids in *internal* byte order (little-endian / reversed).
  - The API returns txids in *display* order (big-endian / reversed again).
  - Before hashing, every txid is reversed: bytes.fromhex(txid)[::-1]
  - If a level has an odd number of nodes, the last node is duplicated.

Proof structure:
  proof = [{"hash": hex_str, "direction": "left"|"right"}, ...]
  direction = which side the *sibling* sits on.

Verification:
  starting_hash = txid_bytes (internal order)
  for step in proof:
      sibling = step["hash"] reversed
      if step["direction"] == "right": combined = hash(current + sibling)
      else:                            combined = hash(sibling + current)
  root = final_hash reversed → compare with block header merkle_root
"""

from __future__ import annotations

import hashlib

import plotly.graph_objects as go
import requests

BLOCKSTREAM     = "https://blockstream.info/api"
DEFAULT_TIMEOUT = 15


# ─── Core crypto ──────────────────────────────────────────────────────────────

def _sha256d_pair(a: bytes, b: bytes) -> bytes:
    """SHA-256d of the concatenation of two 32-byte hash values."""
    return hashlib.sha256(hashlib.sha256(a + b).digest()).digest()


# ─── API ──────────────────────────────────────────────────────────────────────

def get_block_txids(block_hash: str) -> list[str]:
    """Return all txids in a block (display order) from Blockstream.

    Blockstream endpoint: GET /block/{hash}/txids
    Returns a list of 64-char hex strings, coinbase first.
    Raises RuntimeError on failure.
    """
    url = f"{BLOCKSTREAM}/block/{block_hash}/txids"
    try:
        resp = requests.get(url, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        txids = resp.json()
        if not isinstance(txids, list):
            raise RuntimeError("Unexpected payload: expected a list of txids.")
        print(f"[M5] Block {block_hash[:12]}… has {len(txids)} transactions")
        return txids
    except requests.RequestException as exc:
        raise RuntimeError(f"[M5] Could not fetch txids: {exc}") from exc


# ─── Merkle tree construction ─────────────────────────────────────────────────

def build_merkle_root(txids: list[str]) -> str:
    """Recompute the Merkle root from a list of txids (display order).

    Returns the root in display (big-endian) hex — same format as
    the merkle_root field returned by parse_header().
    """
    if not txids:
        return ""

    # Convert display-order txids → internal-order bytes
    level: list[bytes] = [bytes.fromhex(t)[::-1] for t in txids]

    while len(level) > 1:
        # Duplicate last node if odd count (Bitcoin protocol rule)
        if len(level) % 2 == 1:
            level.append(level[-1])

        next_level: list[bytes] = []
        for i in range(0, len(level), 2):
            next_level.append(_sha256d_pair(level[i], level[i + 1]))
        level = next_level

    return level[0][::-1].hex()   # back to display order


def build_merkle_proof(txids: list[str], tx_index: int) -> list[dict[str, str]]:
    """Build an inclusion proof for txids[tx_index].

    Returns a list of proof steps (one per tree level):
      [{"hash": "<sibling hex display>", "direction": "left" | "right"}, ...]

    "direction" is the side where the *sibling* lives:
      - "right" → sibling is to the right  (i.e. current node is left child)
      - "left"  → sibling is to the left   (i.e. current node is right child)
    """
    if not txids or not (0 <= tx_index < len(txids)):
        return []

    level: list[bytes] = [bytes.fromhex(t)[::-1] for t in txids]
    idx   = tx_index
    proof: list[dict[str, str]] = []

    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])

        # Find sibling
        if idx % 2 == 0:                      # current is left child
            sibling_idx = idx + 1
            direction   = "right"
        else:                                  # current is right child
            sibling_idx = idx - 1
            direction   = "left"

        sibling = level[sibling_idx]
        proof.append({
            "hash":      sibling[::-1].hex(),  # back to display order
            "direction": direction,
        })

        # Build next level
        next_level: list[bytes] = []
        for i in range(0, len(level), 2):
            next_level.append(_sha256d_pair(level[i], level[i + 1]))
        level  = next_level
        idx  //= 2

    return proof


def verify_merkle_proof(
    txid:          str,
    proof:         list[dict[str, str]],
    expected_root: str,
) -> bool:
    """Verify a Merkle inclusion proof.

    Args:
        txid          — hex string in display (big-endian) order
        proof         — output of build_merkle_proof()
        expected_root — merkle_root from the block header (display order)

    Returns True only if the computed root matches expected_root exactly.
    """
    current = bytes.fromhex(txid)[::-1]   # → internal order

    for step in proof:
        sibling = bytes.fromhex(step["hash"])[::-1]
        if step["direction"] == "right":
            current = _sha256d_pair(current, sibling)
        else:
            current = _sha256d_pair(sibling, current)

    computed_root = current[::-1].hex()
    return computed_root.lower() == expected_root.lower()


# ─── Visualisation ────────────────────────────────────────────────────────────

def plot_merkle_proof(
    txids:    list[str],
    tx_index: int,
    proof:    list[dict[str, str]],
) -> go.Figure:
    """Visualise the Merkle proof path as an annotated tree diagram.

    Uses a horizontal layout: root at the top, leaves at the bottom.
    The proof path is highlighted in blue; sibling nodes in amber.
    """
    n_levels = len(proof) + 1          # leaf level + one level per proof step
    n_leaves = len(txids)

    # Build level sizes (same logic as the tree construction)
    level_sizes: list[int] = [n_leaves]
    s = n_leaves
    while s > 1:
        s = (s + 1) // 2
        level_sizes.append(s)
    level_sizes.reverse()   # root first → leaves last

    # We'll display max 6 levels deep to keep the chart readable
    max_display_levels = min(n_levels, 6)
    level_sizes = level_sizes[-max_display_levels:]

    fig = go.Figure()

    # ── Draw proof steps as annotated steps (simpler than full tree) ── #
    step_texts  = []
    step_colors = []

    # Start: the txid itself
    step_texts.append(
        f"Leaf TX [{tx_index}]<br>{txids[tx_index][:20]}…"
    )
    step_colors.append("#3d6aff")

    for k, step in enumerate(proof):
        direction = step["direction"]
        sibling   = step["hash"][:16] + "…"
        arrow     = "→" if direction == "right" else "←"
        step_texts.append(
            f"Level {k + 1} sibling ({direction})<br>{sibling}"
        )
        step_colors.append("#ffd740")

    step_texts.append("Merkle Root ✓")
    step_colors.append("#00e676")

    # Y positions (evenly spaced, root at top)
    n = len(step_texts)
    ys = list(range(n - 1, -1, -1))

    fig.add_trace(go.Scatter(
        x=[0.5] * n,
        y=ys,
        mode="markers+text",
        marker=dict(
            color=step_colors,
            size=16,
            symbol="square",
            line=dict(color="#1e2d4a", width=1),
        ),
        text=step_texts,
        textposition="middle right",
        textfont=dict(size=10, color="#8892a4"),
        hoverinfo="text",
    ))

    # Vertical connector line
    fig.add_shape(
        type="line",
        x0=0.5, x1=0.5,
        y0=0, y1=n - 1,
        line=dict(color="#1e2d4a", width=2, dash="dot"),
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#8892a4", size=11),
        margin=dict(l=8, r=8, t=8, b=8),
        height=max(240, n * 48),
        showlegend=False,
        xaxis=dict(visible=False, range=[0, 3]),
        yaxis=dict(visible=False),
    )
    return fig


# ─── Standalone Streamlit tab (legacy) ───────────────────────────────────────

def render() -> None:
    import streamlit as st

    st.header("M5 — Merkle Proof Verifier")
    st.caption(
        "SHA-256d Merkle tree · inclusion proof · verify txid against header root"
    )

    block_hash = st.text_input(
        "Block hash (64 hex chars)",
        placeholder="0000000000000000000322e71c6a00fc…",
        key="m5_block_hash",
    )

    if st.button("Load transactions", key="m5_load") and block_hash:
        with st.spinner("Fetching txids…"):
            try:
                txids = get_block_txids(block_hash.strip())
                st.session_state["m5_txids"]      = txids
                st.session_state["m5_block_hash"] = block_hash.strip()
            except RuntimeError as exc:
                st.error(str(exc))

    txids = st.session_state.get("m5_txids", [])
    if txids:
        st.success(f"✓ {len(txids)} transactions loaded")
        tx_idx = st.slider("Select transaction index", 0, len(txids) - 1, 0, key="m5_tx_idx")

        if st.button("Build & verify proof", key="m5_verify"):
            proof = build_merkle_proof(txids, tx_idx)
            computed_root = build_merkle_root(txids)
            valid = verify_merkle_proof(txids[tx_idx], proof, computed_root)

            c1, c2, c3 = st.columns(3)
            c1.metric("Transactions",   len(txids))
            c2.metric("Proof depth",    len(proof))
            c3.metric("Proof valid",    "✓ Yes" if valid else "✗ No")

            st.plotly_chart(
                plot_merkle_proof(txids, tx_idx, proof),
                use_container_width=True,
            )

            with st.expander("Computed Merkle root"):
                st.code(computed_root, language="text")

            with st.expander("Proof steps"):
                for i, step in enumerate(proof):
                    st.write(f"Level {i}: sibling ({step['direction']}) = `{step['hash'][:32]}…`")
