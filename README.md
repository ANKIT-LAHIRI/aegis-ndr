# Aegis — Hybrid Network Detection & Response Platform

### A cybersecurity + machine-learning project: real-time intrusion detection on a virtualized attack lab

> **Status: 🚧 In active development.** Lab infrastructure complete; attack + reconnaissance capture done; full data pipeline (capture → flow extraction → merge → analysis) verified across 5 traffic categories; a working rate-limiting defense (fail2ban) deployed and tested, including a documented race-condition finding; class imbalance addressed; a first rule-based baseline detector built and evaluated. ML model, FastAPI service, and dashboard in progress. Commits landing regularly.

A self-hosted **cybersecurity** platform for **Network Detection & Response (NDR)** — it watches live network traffic on an isolated lab, detects cyber attacks using both signature rules and machine learning, explains each alert, and can contain the threat. Built to learn **detection engineering, network security, threat detection, and applied ML/data science** end-to-end — on data I generate myself rather than a public benchmark.

**Domains:** Cybersecurity · Intrusion Detection & Prevention · Machine Learning · Data Science · Networking · MLOps

**Keywords:** cybersecurity, network security, intrusion detection system (IDS), intrusion prevention system (IPS), threat detection, SOC, SIEM concepts, anomaly detection, baseline detection, rule-based classification, MITRE ATT&CK, Suricata, packet analysis, packet capture, brute-force detection, dictionary attack, credential stuffing, port-scan detection, reconnaissance detection, rate limiting, fail2ban, SSH hardening, race condition, denial-of-service reaction time, machine learning, feature engineering, class imbalance, stratified sampling, XGBoost, Isolation Forest, FastAPI, Docker, Scapy, tcpdump, nmap, hydra, TCP/IP, virtualization, VirtualBox.

---

## The idea

Most student IDS projects train a classifier on an old public dataset (NSL-KDD, CIC-IDS), report 99% accuracy, and stop. Aegis is built differently:

- **Its own data.** A virtualized attack lab (attacker + victim VMs on an isolated network) generates real, labelled attack traffic — port scans, SSH brute-force — captured firsthand.
- **Hybrid detection.** A signature layer (Suricata) runs alongside an ML layer, so the project can answer the question every interviewer asks: *why not just use rules?*
- **Honest evaluation.** Per-class precision / recall / F1 and false-positive rate — not a single misleading accuracy number.
- **Adversarial testing.** Attempting to evade the detector, then hardening it.

---

## Architecture

```
Attack Lab (Attacker VM  →  Victim VM, isolated host-only network)
        │  mirrored traffic
        ▼
   Sensor: packet capture → flow feature extraction
        │
        ├─────────────┬───────────────────────────┐
        ▼             ▼                           ▼
   Suricata      ML engine                  Correlation
   (signatures)  • supervised classifier    → group into incidents
                 • anomaly detection         → map to MITRE ATT&CK
                 • SHAP explanations
        │
        ▼
   FastAPI service + storage  →  React dashboard (live alerts, contain action)
```

---

## Tech stack

| Layer | Tool |
|---|---|
| Traffic capture / flows | Python, Scapy, tcpdump |
| Attack simulation | nmap (reconnaissance), Hydra (dictionary attack) |
| Rate-limiting defense | fail2ban (SSH jail, log-based IP banning) |
| Signature IDS | Suricata |
| ML | XGBoost (classifier), Isolation Forest (anomaly), SHAP, MLflow |
| Backend | FastAPI |
| Storage | PostgreSQL / TimescaleDB |
| Frontend | React |
| Lab | VirtualBox, Ubuntu Server, netplan (static networking) |
| Ops | Docker Compose, GitHub Actions |

---

## Lab setup

- **Victim** (`192.168.56.10`) — Ubuntu Server running SSH and a web service; deliberately weak credentials to allow the brute-force demo.
- **Attacker** (`192.168.56.20`) — Ubuntu Server with `nmap`, `hydra`, and scanning tools.
- **Isolated host-only network** — no route to the internet or any real network, so all attack traffic stays contained.

All attacks are run only against machines I own, on an isolated network, for research and learning.

---

## Current data

Five labelled traffic categories, generated on the lab and processed through a self-built pipeline (`flows.py` → `merge.py` → `analyze.py`):

| Label | Flows | Avg packets | Avg bytes | Avg duration | Avg SYN | What it is |
|---|---|---|---|---|---|---|
| `attack` | 6 | 24.7 | 4,607 | 2.59s | 1.0 | SSH dictionary attack (Hydra), undefended, succeeds |
| `normal` | 2 | 2,696.0 | 285,844 | 100.28s | 1.0 | Legitimate SSH sessions |
| `portscan` | 1,002 | 2.0 | 128.2 | 0.00s | 1.0 | nmap reconnaissance scan |
| `background` | 1 | 3.0 | 537 | 6.00s | 0.0 | Incidental UDP broadcast (SSDP), kept separate from real traffic |
| `attack_blocked` | 4 | 39.5 | 6,438 | 57.58s | 1.0 | The same dictionary attack, this time defended by fail2ban mid-attempt |

**The categories are cleanly separable by eye** — normal sessions carry ~100x the packets and bytes of an attack flow and last ~40x longer; a port scan is the opposite extreme, with thousands of near-empty, sub-millisecond flows. `attack_blocked` is its own distinct shape again: more packets and ~22x the duration of a successful attack, because a firewall *drop* (vs. a clean rejection) causes the sender to retry and time out slowly rather than fail fast. This separation is the basis the first baseline detector will be built on before any ML is introduced.

**Known limitation, noted honestly:** the categories are imbalanced (1,002 portscan flows vs. single digits elsewhere), because a single scan naturally produces far more flows than a handful of login sessions. This will be addressed explicitly (subsampling / class weighting) before any model training, rather than treated as a hidden problem.

**Pipeline scripts** (`flows.py`, `merge.py`, `analyze.py`) are in this repo and reusable — feeding a new `.pcap` and a label through `flows.py` extends the dataset with no changes needed elsewhere.

---

## Defense in action: fail2ban and a race-condition finding

Detection is only half the story — Aegis also tests a real, working prevention control against its own attack traffic, and documents where that control's assumptions break down.

**Setup.** [fail2ban](https://github.com/fail2ban/fail2ban) watches the victim's SSH auth log (`/var/log/auth.log`) and bans a source IP after a configurable number of failed logins within a time window (`maxretry`, `findtime`), for a set duration (`bantime`). This is a standard, real-world SSH-hardening tool, configured here with an intentionally low `maxretry` (2–3) to make the effect observable within a short lab session.

**First result — the defense was bypassed.** Running the exact same Hydra dictionary attack from before (`hydra -l analyst -P password.txt ssh://192.168.56.10`), the attacker's IP *was* banned (`fail2ban-client status sshd` confirmed it) — but the attack still succeeded and returned the correct password. Hydra's default behaviour opens several login attempts in parallel (`~5 tasks`); fail2ban's ban decision (read log → count → issue a firewall rule) takes real time to execute, and the correct password happened to be reached before the ban was fully in place. **A threshold-based defense has a reaction time, and a sufficiently parallel attacker can race past it** — a known, real limitation of connection-counting defenses, reproduced here directly.

**Second result — controlled comparison.** Re-running the identical attack with Hydra forced to single-threaded (`-t 1`) removed the parallelism: fail2ban banned the attacker after 2 failed attempts, and the attack returned **`0 valid password found`** — fully blocked. Captured with `tcpdump`, this blocked run shows a distinct flow signature: attempts made after the ban carry ~1.8x the packets and ~22x the duration of a normal attempt, because the firewall *silently drops* packets rather than rejecting the connection, so the client hangs and retries before finally timing out. That difference is now the `attack_blocked` row in the dataset above — captured as data, not just observed.

**Why this matters for the project:** it's a controlled, reproducible demonstration that (a) prevention and detection are different problems with different failure modes, (b) a defense's effectiveness depends on the attacker's behaviour, not just the defender's threshold, and (c) that dependency is itself visible in network traffic — which is exactly the kind of signal a detection model should learn to use.

---

## Class imbalance and a first baseline detector

**Balancing the dataset.** `balance.py` reads `combined_flows.csv` and caps every label at 20 rows, randomly subsampling any category above that (only `portscan`, 1,002 → 20) while keeping every row of the rare categories intact. This produces `balanced_flows.csv` (33 rows) — a proportioned dataset for evaluation and future training — while `combined_flows.csv` stays untouched as the full, honest record described above.

**A rule-based baseline, before any ML.** `baseline.py` applies two hand-written thresholds — small-packet/near-zero-duration flows flagged as scan-like, moderate-packet/short-duration/low-byte flows flagged as bruteforce-like — and checks each prediction against the true label.

**Result: 90.9% overall accuracy (30/33)** — but the per-class breakdown is the real finding, not the headline number:

| Label | Correct | Accuracy |
|---|---|---|
| `attack` | 6/6 | 100% |
| `normal` | 2/2 | 100% |
| `portscan` | 20/20 | 100% |
| `background` | 0/1 | **0%** |
| `attack_blocked` | 2/4 | **50%** |

The two simple thresholds perfectly separate the "textbook" categories they were designed around, but fail exactly where nuance appears: they cannot distinguish a tiny background broadcast from a low-volume attack (both are small and brief), and they miss the half of `attack_blocked` flows that hang for 50+ seconds after the firewall drop — far outside either rule's duration window. **This baseline, and its two documented failure modes, is the number and the gap any future ML model needs to beat and close.**

---

## Roadmap

- [x] Build isolated attack lab (attacker + victim VMs with static IPs)
- [x] Generate and capture labeled traffic (port scans, SSH brute-force)
- [x] Extract flow-level features (packets, bytes, duration, SYN count)
- [x] Exploratory analysis across attack, normal, and reconnaissance traffic
- [x] Deploy a working rate-limiting defense (fail2ban) and test it against real attack traffic
- [x] Document a defense-evasion finding (parallel attack vs. threshold-based ban) with reproducible before/after data
- [x] Address class imbalance before model training
- [x] Implement a rule-based baseline detector and evaluate per-class (90.9% overall; documented failure modes)
- [ ] Implement signature detection using Suricata and compare with baseline/fail2ban
- [ ] Train ML models (XGBoost classifier + Isolation Forest for anomaly detection) and beat the 90.9% baseline honestly
- [ ] Build FastAPI service for real-time traffic analysis and alert generation
- [ ] Develop React dashboard for visualization and live alerts
- [ ] Perform adversarial testing (evasion techniques) and improve detection robustness
- [ ] Dockerize the system and provide documentation + demo

---

## What this is and isn't

This is a **student-scale** learning project that uses production-relevant tools and honest methodology — not commercial production software. It runs on a two-VM lab, not a live enterprise network. The goal is to demonstrate real detection-engineering and applied-ML skills end-to-end, and to be able to explain every part of it.

---

*Author: Ankit Lahiri · built while learning, one honest commit at a time.*
