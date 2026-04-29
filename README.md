[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/N3kLi3ZO)
[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=23640545&assignment_repo_type=AssignmentRepo)
# Blockchain Dashboard Project

Use this repository to build your blockchain dashboard project.
Update this README every week.

## Student Information

| Field | Value |
|---|---|
| Student Name | Ariel Nuñez Valencia |
| GitHub Username | Arielnv77 |
| Project Title | CryptoChain Analyzer Dashboard |
| Chosen AI Approach | Anomaly Detector â€” inter-block time statistical analysis |

## Module Tracking

| Module | What it does | Key functions | Status |
|---|---|---|---|
| M1 — PoW Monitor | Fetches last 100 blocks, computes inter-arrival times, estimates difficulty and hash rate | `get_latest_blocks`, `get_difficulty`, `get_hashrate`, `get_next_retarget`, `plot_block_time_histogram` | ✅ Complete |
| M2 — Block Header Analyzer | Fetches raw 80-byte header, parses 6 fields (LE), verifies SHA-256d manually with `hashlib` | `get_raw_header`, `parse_header`, `verify_pow`, `bits_to_target` | ✅ Complete |
| M3 — Difficulty History | Fetches ~20 retarget epochs, builds DataFrame with `actual_time` and `ratio`, dual-axis chart | `get_difficulty_history`, `plot_difficulty_history`, `plot_hashrate_vs_difficulty` | ✅ Complete |
| M4 — Anomaly Detector (AI) | Z-score on log(T) vs Exp(λ=1/600 s) baseline; classifies fast/slow blocks; KS test evaluation | `detect_anomalies`, `evaluate`, `plot_anomalies` | ✅ Complete |
| M5 — Merkle Proof Verifier | — | — | ⬜ Optional |
| M6 — Security Score (51% cost) | — | — | ⬜ Optional |

## Cryptographic Concepts Implemented

### Leading zeros and the `bits` field (teacher feedback addressed)

The **`bits` field** in each block header is a compact 4-byte encoding of the 256-bit PoW target threshold.
It is decoded in `m1_pow_monitor.py` and `m2_block_header.py` as:

```python
# bits = 0x17034219  →  exponent = 0x17 = 23,  mantissa = 0x034219
target = mantissa * (1 << (8 * (exponent - 3)))   # full 256-bit integer

# Difficulty is the ratio of the genesis target to the current target:
difficulty = MAX_TARGET / target
# MAX_TARGET = 0x00000000FFFF0000...0000  (bits = 0x1d00ffff, genesis block)
```

**Leading zero bits** measure how hard the puzzle was: a valid block hash must be a 256-bit integer
smaller than `target`. The more leading zeros, the smaller the hash, the harder the proof:

```python
leading_zeros = 256 - int(hash_hex, 16).bit_length()
# Current mainnet: ~76 leading zero bits  →  probability ≈ 2⁻⁷⁶ per hash attempt
```

SHA-256d verification is computed **manually** in `m2_block_header.py` using only `hashlib`:

```python
def double_sha256(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

# Reversed byte order gives the display hash (Bitcoin convention):
hash_display = double_sha256(header_bytes)[::-1].hex()
valid = int(hash_display, 16) <= target          # PoW check
```

### M4 — Anomaly Detector (AI Component)

Bitcoin inter-block times follow **Exp(λ = 1/600 s)** under normal network conditions.
Anomalies are detected by Z-scoring `log(T)`, which is more sensitive than Z-scoring `T` directly
because the raw exponential distribution is heavily right-skewed:

```python
log_t  = np.log(block_times)
z      = scipy.stats.zscore(log_t, ddof=1)
# flag |z| > 3  →  anomaly rate ≈ 0.27 % for a Gaussian
```

Evaluation uses the **Kolmogorov–Smirnov test** against `Exp(λ=1/600)`:
high p-value = data consistent with the theoretical baseline.

## Session Log

| Date | Session | What was done |
|---|---|---|
| 2026-04-21 | Session 1 | Cloned repo, connected Blockstream + Blockchain.info + BlockCypher APIs, retrieved live block data |
| 2026-04-29 | Session 2 | Built all 4 modules (M1–M4) + full custom CSS Streamlit dashboard with auto-refresh every 60 s |
| 2026-04-29 | Session 3 | Complete UI redesign: dark navy theme, sidebar navigation, per-module pages, Plotly dark charts |

## Current Progress (Session 3 — 2026-04-29)

- **M1**: `get_latest_blocks(n=100)` paginates Blockstream; histogram shows Exp(λ=1/600 s) overlay
- **M2**: raw 80-byte header fetched; 6 fields parsed (little-endian `struct`); SHA-256d verified manually
- **M3**: ~20 retarget epochs with `height`, `actual_time`, `ratio` columns; dual-axis chart
- **M4**: Z-score on log(T) returns `{indices, times, z_scores, labels}`; fast/slow/outlier classification; 95 % CI band on scatter plot; KS test metric
- **Dashboard (v2)**: full dark navy redesign (`#0a0f1e` bg), sidebar navigation with per-module pages, `Inter` + `JetBrains Mono` fonts, Plotly charts with dark overlay (`#1e2d4a` grid), live-pulse indicator, 60 s auto-refresh
- **Addressed teacher feedback**: `bits` → target formula and leading-zero semantics documented in code comments and in this README

## Next Step

- Consider M5 (Merkle Proof) or M6 (51% attack cost) for top grade

## Main Problem or Blocker

- None at this point

## How to Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

Abre en `http://localhost:8501`. Se actualiza automáticamente cada 60 s.

## Project Structure

```text
blockchain-dashboard-Arielnv77/
├── README.md
├── requirements.txt
├── app.py                          ← dashboard principal (CSS + layout + auto-refresh)
├── api/
│   └── blockchain_client.py        ← helpers HTTP (Blockstream + blockchain.info)
└── modules/
    ├── m1_pow_monitor.py           ← dificultad, hashrate, histograma inter-arrival
    ├── m2_block_header.py          ← SHA-256d manual, parse header, verify PoW
    ├── m3_difficulty_history.py    ← historial epochs, ratio, dual-axis chart
    └── m4_ai_component.py          ← anomaly detector Z-score + KS test
```

<!-- student-repo-auditor:teacher-feedback:start -->
## Teacher Feedback

### Kick-off Review

Review time: 2026-04-29 20:31 CEST
Status: Green

Strength:
- I can see the dashboard structure integrating the checkpoint modules.

Improve now:
- The checkpoint evidence is strong: the dashboard and core modules are visibly progressing.

Next step:
- Keep building on this checkpoint and prepare the final AI integration.
<!-- student-repo-auditor:teacher-feedback:end -->
