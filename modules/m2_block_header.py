"""M2 — Block Header Analyzer.

Fetches the raw 80-byte header from Blockstream, parses all 6 protocol fields
(respecting little-endian byte order), and verifies Proof-of-Work by computing
SHA-256d MANUALLY with hashlib — no external cryptography libraries used.

Bitcoin block header layout (80 bytes, all multi-byte fields little-endian):
  [0 : 4]  version    — uint32-LE
  [4 :36]  prev_hash  — 32 bytes reversed for display
  [36:68]  merkle_root— 32 bytes reversed for display
  [68:72]  timestamp  — uint32-LE (Unix epoch seconds)
  [72:76]  bits       — uint32-LE (compact target)
  [76:80]  nonce      — uint32-LE
"""

from __future__ import annotations

import hashlib
import struct
from datetime import UTC, datetime

import requests

BLOCKSTREAM   = "https://blockstream.info/api"
DEFAULT_TIMEOUT = 10


# ─── SHA-256d ─────────────────────────────────────────────────────────────────

def double_sha256(data: bytes) -> bytes:
    """SHA-256(SHA-256(data)) — only hashlib, no external libraries."""
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


# ─── Target math ──────────────────────────────────────────────────────────────

def bits_to_target(bits: int) -> int:
    """Decode the compact 'bits' field into the full 256-bit target integer.

    Protocol formula:  target = mantissa × 2^(8 × (exponent − 3))
    """
    exp  = bits >> 24
    mant = bits & 0x00FFFFFF
    return mant * (1 << (8 * (exp - 3)))


# ─── API fetch ────────────────────────────────────────────────────────────────

def get_raw_header(block_hash: str) -> bytes:
    """Fetch the raw 80-byte block header from Blockstream.

    Returns the header as a bytes object (not hex string).
    Raises RuntimeError on network/API failure.
    """
    url = f"{BLOCKSTREAM}/block/{block_hash}/header"
    try:
        resp = requests.get(url, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        raw_hex = resp.text.strip()
        raw = bytes.fromhex(raw_hex)
        print(f"[M2] Fetched {len(raw)}-byte header for block {block_hash[:12]}…")
        return raw
    except requests.RequestException as exc:
        raise RuntimeError(f"[M2] Could not fetch header for {block_hash}: {exc}") from exc
    except ValueError as exc:
        raise RuntimeError(f"[M2] Invalid hex in header response: {exc}") from exc


# ─── Header parsing ───────────────────────────────────────────────────────────

def parse_header(raw: bytes) -> dict[str, object]:
    """Parse raw 80-byte header bytes into the 6 protocol fields.

    Multi-byte hash fields (prev_hash, merkle_root) are byte-reversed to match
    Bitcoin's display convention (big-endian / human-readable order).
    """
    if len(raw) != 80:
        raise ValueError(f"Expected 80 header bytes, got {len(raw)}")

    version      = struct.unpack_from("<I", raw,  0)[0]
    prev_hash    = raw[4:36][::-1].hex()          # LE → display BE
    merkle_root  = raw[36:68][::-1].hex()
    ts_raw       = struct.unpack_from("<I", raw, 68)[0]
    bits_raw     = struct.unpack_from("<I", raw, 72)[0]
    nonce        = struct.unpack_from("<I", raw, 76)[0]

    ts_str = datetime.fromtimestamp(ts_raw, tz=UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    return {
        "version":    version,
        "prev_hash":  prev_hash,
        "merkle_root": merkle_root,
        "timestamp":  ts_str,
        "bits":       hex(bits_raw),
        "nonce":      nonce,
    }


# ─── PoW verification ─────────────────────────────────────────────────────────

def verify_pow(raw: bytes) -> dict[str, object]:
    """Verify Proof-of-Work for a raw 80-byte header.

    Steps (all arithmetic in Python, no external libs):
      1. hash_bytes = SHA256(SHA256(raw_header))      ← two rounds, per spec
      2. hash_display = hash_bytes[::-1].hex()        ← reverse → display order
      3. target = bits_to_target(bits_field)          ← decode compact target
      4. valid = int(hash_display, 16) ≤ target       ← PoW check
      5. leading_zeros = 256 − hash_int.bit_length()  ← prefix depth

    Returns a dict with: hash, target_hex, valid, leading_zeros.
    """
    if len(raw) != 80:
        raise ValueError(f"Expected 80 header bytes, got {len(raw)}")

    # Step 1 & 2 — manual SHA256d
    digest       = double_sha256(raw)
    hash_display = digest[::-1].hex()           # reversed bytes → display hash
    hash_int     = int(hash_display, 16)

    # Step 3 — decode bits from header bytes 72–75 (little-endian)
    bits_int = struct.unpack_from("<I", raw, 72)[0]
    target   = bits_to_target(bits_int)

    # Step 4 — PoW validity
    valid = hash_int <= target

    # Step 5 — count leading zero bits in 256-bit hash
    leading_zeros = (256 - hash_int.bit_length()) if hash_int > 0 else 256

    return {
        "hash":          hash_display,
        "target_hex":    f"{target:#066x}",
        "valid":         valid,
        "leading_zeros": leading_zeros,
    }


# ─── Fallback (no raw header) ─────────────────────────────────────────────────

def parse_header_from_block(block: dict) -> dict[str, object]:
    """Build the 6-field dict from a normalized block dict (API JSON).

    Used as a fallback when the raw-header endpoint is unavailable.
    Does NOT verify the hash (raw bytes are not available here).
    """
    bits_val = block.get("bits")
    return {
        "version":    block.get("version", "—"),
        "prev_hash":  _trunc(block.get("previous_block") or block.get("previousblockhash")),
        "merkle_root": _trunc(block.get("merkle_root")),
        "timestamp":  block.get("time", "—"),
        "bits":       hex(bits_val) if isinstance(bits_val, int) else "—",
        "nonce":      block.get("nonce", "—"),
    }


def _trunc(value: object, n: int = 20) -> str:
    s = str(value) if value else "—"
    return (s[:n] + "…") if len(s) > n else s


# ─── Standalone Streamlit tab (legacy) ───────────────────────────────────────

def render() -> None:
    import streamlit as st

    st.header("M2 — Block Header Analyzer")
    st.caption("Fetches raw 80-byte header · parses 6 fields (LE) · verifies SHA-256d manually")

    block_hash = st.text_input(
        "Block hash (64 hex chars)",
        placeholder="0000000000000000000322e71c6a00fc…",
        key="m2_hash_input",
    )

    if st.button("Parse & verify", key="m2_verify") and block_hash:
        with st.spinner("Fetching header from Blockstream…"):
            try:
                raw    = get_raw_header(block_hash.strip())
                fields = parse_header(raw)
                result = verify_pow(raw)

                if result["valid"]:
                    st.success("✓  SHA-256d hash meets the target — PoW is VALID")
                else:
                    st.error("✗  Hash does NOT meet the target — PoW INVALID")

                c1, c2, c3 = st.columns(3)
                c1.metric("Leading zero bits", result["leading_zeros"])
                c2.metric("bits field", fields["bits"])
                c3.metric("Computed hash matches?", "Yes" if result["valid"] else "No")

                st.subheader("6 header fields (80-byte little-endian header)")
                for k, v in fields.items():
                    st.write(f"**{k}:** `{v}`")

                with st.expander("SHA-256d result"):
                    st.code(result["hash"], language="text")
                    st.caption(f"target = {result['target_hex'][:30]}…")

            except (RuntimeError, ValueError) as exc:
                st.error(f"Error: {exc}")
    elif not block_hash:
        st.info("Enter a block hash to parse its header and verify PoW.")
