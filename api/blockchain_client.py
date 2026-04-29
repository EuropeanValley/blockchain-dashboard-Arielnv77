"""Helpers for fetching and normalizing blockchain data for the dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from statistics import mean

import requests

BLOCKSTREAM_API = "https://blockstream.info/api"
BLOCKCHAIN_CHARTS_API = "https://api.blockchain.info/charts/difficulty"
BLOCKCYPHER_API = "https://api.blockcypher.com/v1/btc/main"
DEFAULT_TIMEOUT = 10


class BlockchainClientError(RuntimeError):
    """Raised when an upstream blockchain API cannot be reached or parsed."""


@dataclass(frozen=True)
class DifficultySnapshot:
    """Small summary used by the AI module."""

    latest: float
    average: float
    minimum: float
    maximum: float
    change_pct: float


@dataclass(frozen=True)
class NetworkSnapshot:
    """Compact network status from a secondary API."""

    height: int | None
    hash: str | None
    peer_count: int | None
    unconfirmed_count: int | None
    last_fork_height: int | None


def _get_json(url: str, *, params: dict[str, object] | None = None) -> object:
    try:
        response = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise BlockchainClientError(f"Request failed for {url}: {exc}") from exc
    except ValueError as exc:
        raise BlockchainClientError(f"Invalid JSON received from {url}") from exc


def _get_text(url: str) -> str:
    try:
        response = requests.get(url, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        return response.text.strip()
    except requests.RequestException as exc:
        raise BlockchainClientError(f"Request failed for {url}: {exc}") from exc


def _normalize_block(block: dict[str, object]) -> dict[str, object]:
    difficulty = block.get("difficulty")
    if difficulty is None and block.get("bits") is not None:
        difficulty = block.get("bits")

    timestamp = block.get("timestamp") or block.get("time")
    readable_time = None
    if isinstance(timestamp, (int, float)):
        readable_time = datetime.fromtimestamp(timestamp, tz=UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    return {
        "hash": block.get("id") or block.get("hash"),
        "height": block.get("height"),
        "timestamp": timestamp,
        "time": readable_time,
        "difficulty": difficulty,
        "bits": block.get("bits"),
        "nonce": block.get("nonce"),
        "tx_count": block.get("tx_count"),
        "size": block.get("size"),
        "weight": block.get("weight"),
        "merkle_root": block.get("merkle_root") or block.get("merkle_root_hex"),
        "previous_block": block.get("previousblockhash") or block.get("prev_block"),
    }


def get_api_sources() -> list[dict[str, str]]:
    """Return the three APIs used by the dashboard."""

    return [
        {
            "name": "Blockstream",
            "role": "Latest block and block header lookups",
            "base_url": BLOCKSTREAM_API,
        },
        {
            "name": "Blockchain.com Charts",
            "role": "Difficulty history time series",
            "base_url": BLOCKCHAIN_CHARTS_API,
        },
        {
            "name": "BlockCypher",
            "role": "General Bitcoin network snapshot",
            "base_url": BLOCKCYPHER_API,
        },
    ]


def get_latest_block() -> dict[str, object]:
    """Return normalized data for the current Bitcoin tip block."""

    tip_hash = _get_text(f"{BLOCKSTREAM_API}/blocks/tip/hash")
    return get_block(tip_hash)


def get_block(block_hash: str) -> dict[str, object]:
    """Return normalized data for a block hash."""

    payload = _get_json(f"{BLOCKSTREAM_API}/block/{block_hash}")
    if not isinstance(payload, dict):
        raise BlockchainClientError("Unexpected block payload format.")
    return _normalize_block(payload)


def get_block_header_raw(block_hash: str) -> str:
    """Return the 80-byte block header as a 160-char hex string."""
    return _get_text(f"{BLOCKSTREAM_API}/block/{block_hash}/header")


def _get_blocks_page(start_height: int | None = None) -> list[dict[str, object]]:
    url = f"{BLOCKSTREAM_API}/blocks"
    if start_height is not None:
        url += f"/{start_height}"
    payload = _get_json(url)
    if not isinstance(payload, list):
        raise BlockchainClientError("Unexpected blocks-page payload format.")
    return [_normalize_block(b) for b in payload if isinstance(b, dict)]


def get_recent_blocks(n: int = 50) -> list[dict[str, object]]:
    """Return the n most recent normalized blocks, newest first.

    Makes ceil(n/10) sequential Blockstream requests; each page returns 10 blocks.
    """
    blocks: list[dict[str, object]] = []
    start_height: int | None = None

    while len(blocks) < n:
        page = _get_blocks_page(start_height)
        if not page:
            break
        blocks.extend(page)
        heights = [b["height"] for b in page if isinstance(b.get("height"), int)]
        if not heights:
            break
        start_height = min(heights) - 1

    return blocks[:n]


def get_difficulty_history(days: int = 90) -> list[dict[str, float]]:
    """Return chart-ready Bitcoin difficulty history points."""

    payload = _get_json(
        BLOCKCHAIN_CHARTS_API,
        params={
            "timespan": f"{days}days",
            "sampled": "true",
            "metadata": "false",
            "cors": "true",
            "format": "json",
        },
    )
    if not isinstance(payload, dict) or not isinstance(payload.get("values"), list):
        raise BlockchainClientError("Unexpected difficulty history payload format.")

    values = []
    for point in payload["values"]:
        if not isinstance(point, dict):
            continue
        x = point.get("x")
        y = point.get("y")
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            values.append({"x": float(x), "y": float(y)})

    if not values:
        raise BlockchainClientError("Difficulty history response was empty.")
    return values


def get_network_snapshot() -> NetworkSnapshot:
    """Return a simple Bitcoin network snapshot from a third API."""

    payload = _get_json(BLOCKCYPHER_API)
    if not isinstance(payload, dict):
        raise BlockchainClientError("Unexpected network snapshot payload format.")

    return NetworkSnapshot(
        height=payload.get("height") if isinstance(payload.get("height"), int) else None,
        hash=payload.get("hash") if isinstance(payload.get("hash"), str) else None,
        peer_count=payload.get("peer_count") if isinstance(payload.get("peer_count"), int) else None,
        unconfirmed_count=payload.get("unconfirmed_count")
        if isinstance(payload.get("unconfirmed_count"), int)
        else None,
        last_fork_height=payload.get("last_fork_height")
        if isinstance(payload.get("last_fork_height"), int)
        else None,
    )


def summarize_difficulty(points: list[dict[str, float]]) -> DifficultySnapshot:
    """Compute a compact summary from chart points."""

    series = [point["y"] for point in points if "y" in point]
    if not series:
        raise BlockchainClientError("No difficulty values available for summary.")

    first = series[0]
    latest = series[-1]
    change_pct = 0.0 if first == 0 else ((latest - first) / first) * 100
    return DifficultySnapshot(
        latest=latest,
        average=mean(series),
        minimum=min(series),
        maximum=max(series),
        change_pct=change_pct,
    )
