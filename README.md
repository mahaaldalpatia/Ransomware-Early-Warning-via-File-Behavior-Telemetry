# Ransomware Early-Warning via File Behavior Telemetry

> **Minor Project:** Real-time host-level file system behavioral telemetry collection and multi-signal early-warning detection against ransomware attacks.

---

## 📌 Project Overview

Ransomware attacks inflict catastrophic damage by silently encrypting enterprise and personal files before traditional signature-based antivirus solutions can intervene. 

This project implements a **behavioral telemetry early-warning system** that continuously monitors file system dynamics in real time. By analyzing low-level file events (Creation, Modification, Renaming, and Deletion) and extracting cryptographic telemetry (Shannon Entropy and Transaction Velocity), the system intercepts ransomware activity **within seconds of initiation**, containing the attack's blast radius before mass data loss occurs.

---

## 🏗️ System Architecture

```
                      +-----------------------------+
                      |   Monitored Directory       |
                      |       (test_data/)          |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |  Watchdog Telemetry Hook    |
                      |   - CREATE, MODIFY, DELETE  |
                      |   - MOVE_FROM, MOVE_TO      |
                      +--------------+--------------+
                                     |
            +------------------------+------------------------+
            |                                                 |
            v                                                 v
  +--------------------+                             +--------------------+
  | Feature Extractor  |                             | Async Write Queue  |
  | - File Size        |                             | - WAL Mode SQLite  |
  | - SHA-256 Hash     |                             | - Indexed Schema   |
  | - Shannon Entropy  |                             +---------+----------+
  +---------+----------+                                       |
            |                                                  v
            +------------------------+             +----------------------+
                                     |             |     database/        |
                                     v             |    telemetry.db      |
                      +-----------------------------+---------+----------+
                      |    Early-Warning Engine               |
                      |  - Operation Burst Rate               v
                      |  - Rapid Modification Count  +--------------------+
                      |  - Suspicious Extension      | Visual Analytics   |
                      |  - Cryptographic Entropy     |    & Reporting     |
                      +--------------+--------------+ +--------------------+
                                     |
                                     v
                      +-----------------------------+
                      |     INCIDENT ALERT          |
                      |  [CRITICAL / HIGH / NORMAL] |
                      |  - Containment Latency (s)  |
                      |  - Protected Files Saved    |
                      +-----------------------------+
```

---

## 🔬 Multi-Signal Behavioral Heuristics

The detection engine evaluates four complementary behavioral signals to calculate a composite **Risk Score (0 to 100)**:

| Signal | Heuristic Evaluated | Threat Characteristic Detected | Max Score |
| :--- | :--- | :--- | :--- |
| **1. Operation Burst** | Operations / second ($\ge 15\text{ ops/s}$) | Automated programmatic loop vs. human interaction speed | 35 pts |
| **2. Modification Burst** | Cumulative write frequency ($\ge 25\text{ modifies}$) | Mass consecutive overwrites across diverse files | 25 pts |
| **3. Extension Churn** | Rapid extension alteration (`.locked_test`, `.crypto`, etc.) | Ransomware branding / obfuscation payload | 20 pts |
| **4. Cryptographic Entropy** | Shannon Entropy $H(X) \ge 7.0$ (0.0 to 8.0) | File payload encryption (AES/ChaCha20 vs plain text) | 20 pts |

### Shannon Entropy Formula:
$$H(X) = -\sum_{i=0}^{255} P(x_i) \log_2 P(x_i)$$
* Plain document baseline: **3.8 – 5.0**
* Ransomware ciphertext: **7.4 – 7.99**

---

## 🚀 Quick Start & Presentation Demo Guide

### 1. Unified Master Demo Suite (Recommended for Presentation)
To present the prototype seamlessly without running multiple terminal commands:
```powershell
.\.venv\Scripts\python run_demo.py
```
This launches the interactive demonstration menu:
* **Option 1:** Run Benign Baseline (Demonstrates normal office user behavior -> Result: `NORMAL`)
* **Option 2:** Run Ransomware Attack (Demonstrates live encryption, high entropy spike, and instant `CRITICAL / HIGH` early warning)
* **Option 3:** Run Post-Incident Forensic Detector (Detailed terminal scorecard)
* **Option 4:** View Visual Dashboard (Displays 4-panel graph and saves to `reports/telemetry_analysis.png`)
* **Option 5:** Generate Incident Report (Outputs Markdown/text reports to `reports/`)
* **Option 6:** Clean Up Test Directory

---

### 2. Standalone Script Usage

Each module can also be executed independently:

#### Start the Telemetry Collector:
```powershell
.\.venv\Scripts\python src/collector.py
```

#### Run the Simulator (Normal / Malicious):
```powershell
.\.venv\Scripts\python src/simulator.py
```

#### Run the Early-Warning Detector:
```powershell
.\.venv\Scripts\python src/detector.py
```

#### Generate Visual Charts:
```powershell
.\.venv\Scripts\python src/dashboard.py
```

#### Generate Formal Evaluation Report:
```powershell
.\.venv\Scripts\python src/generate_report.py
```

---

## 📊 Prototype Output Artifacts

* **Visual Analytics Dashboard:** [`reports/telemetry_analysis.png`](reports/telemetry_analysis.png)
* **Incident Reports:** [`reports/incident_report_latest.md`](reports/incident_report_latest.md)
* **Telemetry SQLite Database:** [`database/telemetry.db`](database/telemetry.db)

---

## 🛠️ Technology Stack
* **Language:** Python 3.x
* **File System Monitoring:** `watchdog`
* **Cryptographic & Telemetry Math:** `hashlib`, `math`, `numpy`
* **Data Persistence:** `sqlite3` (WAL Mode & B-Tree indexing)
* **Visualization:** `matplotlib`
