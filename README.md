[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/N3kLi3ZO)
[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=23640545&assignment_repo_type=AssignmentRepo)
# Blockchain Dashboard Project

Use this repository to build your blockchain dashboard project.
Update this README every week.

## Student Information

| Field | Value |
|---|---|
| Student Name | Ariel |
| GitHub Username | Arielnv77 |
| Project Title | CryptoChain Analyzer Dashboard |
| Chosen AI Approach | Anomaly Detector â€” inter-block time statistical analysis |

## Module Tracking

| Module | What it should include | Status |
|---|---|---|
| M1 | Proof of Work Monitor | In progress |
| M2 | Block Header Analyzer | Not started |
| M3 | Difficulty History | Not started |
| M4 | AI Component | Not started |

## Current Progress

- Accepted GitHub Classroom assignment and cloned repository
- Connected to Blockstream API and retrieved live Bitcoin block data
- Printed height, hash, bits, nonce and tx_count for latest block
- Confirmed leading zeros visible in block hash (PoW verification)
- Pushed the first session work to the private GitHub Classroom repository
- Expanded the dashboard client to combine Blockstream, Blockchain.com Charts and BlockCypher

## Next Step

- Keep building the Streamlit dashboard and connect the three APIs to the four modules.

## Main Problem or Blocker

- None at this point

## How to Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Project Structure

```text
template-blockchain-dashboard/
|-- README.md
|-- requirements.txt
|-- .gitignore
|-- app.py
|-- api/
|   `-- blockchain_client.py
`-- modules/
    |-- m1_pow_monitor.py
    |-- m2_block_header.py
    |-- m3_difficulty_history.py
    `-- m4_ai_component.py
```

<!-- student-repo-auditor:teacher-feedback:start -->
## Teacher Feedback

### Kick-off Review

Review time: 2026-04-21 09:19 CEST
Status: Green

Strength:
- Your repository keeps the expected classroom structure.

Improve now:
- The code should connect the API output to theory, especially leading zeros and bits or target.

Next step:
- Add two short code comments that explain leading zeros and the meaning of bits or target.
<!-- student-repo-auditor:teacher-feedback:end -->
