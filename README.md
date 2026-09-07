# Aegis — Hybrid Network Detection & Response Platform

### A cybersecurity + machine-learning project: real-time intrusion detection on a virtualized attack lab

> **Status: 🚧 In active development.** Lab infrastructure complete; attack capture done; flow-extraction pipeline working on real captures; detection engine and dashboard in progress. Commits landing regularly.

A self-hosted **cybersecurity** platform for **Network Detection & Response (NDR)** — it watches live network traffic on an isolated lab, detects cyber attacks using both signature rules and machine learning, explains each alert, and can contain the threat. Built to learn **detection engineering, network security, threat detection, and applied ML/data science** end-to-end — on data I generate myself rather than a public benchmark.

**Domains:** Cybersecurity · Intrusion Detection · Machine Learning · Data Science · Networking · MLOps

**Keywords:** cybersecurity, network security, intrusion detection system (IDS), threat detection, SOC, SIEM concepts, anomaly detection, MITRE ATT&CK, Suricata, packet analysis, brute-force detection, port-scan detection, machine learning, feature engineering, XGBoost, FastAPI, Docker.

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
| Traffic capture / flows | Python, Scapy |
| Signature IDS | Suricata |
| ML | XGBoost (classifier), Isolation Forest (anomaly), SHAP, MLflow |
| Backend | FastAPI |
| Storage | PostgreSQL / TimescaleDB |
| Frontend | React |
| Lab | VirtualBox, Ubuntu Server |
| Ops | Docker Compose, GitHub Actions |

---

## Lab setup

- **Victim** (`192.168.56.10`) — Ubuntu Server running SSH and a web service; deliberately weak credentials to allow the brute-force demo.
- **Attacker** (`192.168.56.20`) — Ubuntu Server with `nmap`, `hydra`, and scanning tools.
- **Isolated host-only network** — no route to the internet or any real network, so all attack traffic stays contained.

All attacks are run only against machines I own, on an isolated network, for research and learning.

---

## Current data

Two labelled captures processed through the flow pipeline (`flows.py`) so far:

| Capture | Packets | Flows | Notes |
|---|---|---|---|
| `attack1.pcap` | 148 | 6 | SSH dictionary attack (hydra) — each flow short, ~25 packets, single SYN, <5s duration |
| `normal1.pcap` | 1,472 | 2 | Legitimate SSH session — one flow with 1,463 packets over 70s (plus incidental UDP broadcast traffic) |

The attack and normal SSH flows are clearly separable on packet count and duration alone, which will anchor the first baseline detector before any ML is introduced.

---

## Roadmap

- [x] Build isolated attack lab (attacker + victim VMs with static IPs)
- [x] Generate and capture labeled traffic (port scans, SSH brute-force)
- [x] Extract flow-level features (packets, bytes, duration, SYN count)
- [ ] Exploratory analysis across attack vs. normal traffic
- [ ] Implement baseline detection using Suricata and compare with custom logic
- [ ] Train ML models (XGBoost classifier + Isolation Forest for anomaly detection)
- [ ] Build FastAPI service for real-time traffic analysis and alert generation
- [ ] Develop React dashboard for visualization and live alerts
- [ ] Perform adversarial testing (evasion techniques) and improve detection robustness
- [ ] Dockerize the system and provide documentation + demo

---

## What this is and isn't

This is a **student-scale** learning project that uses production-relevant tools and honest methodology — not commercial production software. It runs on a two-VM lab, not a live enterprise network. The goal is to demonstrate real detection-engineering and applied-ML skills end-to-end, and to be able to explain every part of it.

---

*Author: Ankit Lahiri · built while learning, one honest commit at a time.*
