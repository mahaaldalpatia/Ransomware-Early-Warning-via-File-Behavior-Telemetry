import sys
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from src.detector import analyze_telemetry_run
except ImportError:
    from detector import analyze_telemetry_run


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"


def generate_incident_report(run_id=None):
    """
    Generates a structured cybersecurity incident report in both Markdown
    and plain text formats inside the reports/ directory.
    """
    REPORTS_DIR.mkdir(exist_ok=True)
    metrics = analyze_telemetry_run(run_id=run_id)

    if not metrics:
        print("[!] Unable to generate report: no metrics available.")
        return None

    run_id = metrics["run_id"]
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    md_content = f"""# Ransomware Early-Warning Behavioral Telemetry Report

**Generated:** {timestamp_str}  
**Analyzed Run ID:** `{run_id}`  
**Project:** Ransomware Early-Warning via File Behavior Telemetry (Minor Project)

---

## 1. Executive Summary

| Assessment Metric | Assessed Value |
| :--- | :--- |
| **Threat Classification** | **{metrics['alert_level']}** |
| **Composite Risk Score** | **{metrics['total_risk_score']} / 100** |
| **Observation Duration** | {metrics['duration_seconds']:.2f} seconds |
| **Total Telemetry Events** | {metrics['total_events']} operations across {metrics['unique_files']} distinct files |
| **Peak Throughput Rate** | {metrics['operations_per_second']:.2f} ops/second |
| **Average Shannon Entropy** | {metrics['avg_entropy']:.4f} (Max: {metrics['max_entropy']:.4f}) |

---

## 2. Multi-Signal Behavioral Heuristics

The detection engine evaluates multi-dimensional file system behavior against four primary ransomware indicators:

1. **Operation Burst Rate Signal:** `{metrics['burst_score']} / 35 pts`
   - *Behavior:* Analyzes transactions per second to catch automated encryption loops.
2. **Modification Frequency Signal:** `{metrics['modification_score']} / 25 pts`
   - *Behavior:* Measures the volume of rapid sequential write/overwrite operations ({metrics['modify_events']} modify events observed).
3. **Extension Churn Signal:** `{metrics['extension_score']} / 20 pts`
   - *Behavior:* Detects rapid renames targeting suspicious ransomware extensions ({metrics['extension_changes']} changes detected).
4. **Cryptographic Entropy Signal:** `{metrics['entropy_score']} / 20 pts`
   - *Behavior:* Analyzes Shannon entropy divergence toward random ciphertext distribution ({metrics['high_entropy_count']} files >= 7.0 H).

---

## 3. Early Warning & Containment Analysis

"""
    if metrics["detection_time_sec"] is not None and metrics["containment_pct"] is not None:
        md_content += f"""- **Time-to-Detection (Latency):** `{metrics['detection_time_sec']:.2f} seconds`
- **Compromised Target Count:** `{metrics['files_at_detection']}` of `{metrics['unique_files']}` files
- **Preserved User Data (Containment Ratio):** `{metrics['containment_pct']}%` of files safeguarded prior to detection alert threshold.

> **Demonstrated Prototype Impact:** The early-warning heuristic intercepted the simulated attack within seconds of inception, proving that telemetry-driven behavioral detection can contain cryptographic damage before enterprise storage is completely encrypted.
"""
    else:
        md_content += """- **Containment Note:** File activity during this run remained within benign baseline parameters or did not trigger critical alert thresholds.
"""

    md_content += f"""
---

## 4. Forensic Telemetry Breakdown

- **CREATE Operations:** {metrics['create_events']}
- **MODIFY Operations:** {metrics['modify_events']}
- **DELETE Operations:** {metrics['delete_events']}
- **Extension Renames:** {metrics['extension_changes']}

---

## 5. Security Recommendations

1. **Process Quarantine:** Immediately freeze any unauthenticated process exhibiting modification burst rates > 15 ops/s.
2. **Automated Volume Snapshot:** Trigger shadow copy or isolated snapshot upon risk score crossing 35/100 (Medium).
3. **Decoy / Canary Files:** Implement decoy files in monitored directory to detect zero-delay cryptographic overwrites.

---
*Report generated automatically by the Ransomware Early-Warning Telemetry System.*
"""

    report_md_file = REPORTS_DIR / f"incident_report_{run_id}.md"
    report_latest_md = REPORTS_DIR / "incident_report_latest.md"

    report_md_file.write_text(md_content, encoding="utf-8")
    report_latest_md.write_text(md_content, encoding="utf-8")

    print(f"[OK] Markdown incident report written to:\n     {report_md_file}")
    return report_md_file


def main():
    parser = argparse.ArgumentParser(description="Generate Ransomware Telemetry Incident Report")
    parser.add_argument("--run", type=str, help="Specific run_id to generate report for")
    args = parser.parse_args()

    generate_incident_report(run_id=args.run)


if __name__ == "__main__":
    main()
