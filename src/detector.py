import sys
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime


# --------------------------------------------------
# CONFIGURATION & THRESHOLDS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "telemetry.db"

# Calibrated behavioral thresholds for early-warning detection
OPERATION_RATE_THRESHOLD = 15.0       # ops/second
MODIFICATION_THRESHOLD = 25          # total modify events
EXTENSION_CHANGE_THRESHOLD = 5       # suspicious extension renames
ENTROPY_THRESHOLD = 7.0              # high entropy indicating encryption (0-8 scale)

SUSPICIOUS_EXTENSIONS = (
    ".locked_test", ".locked", ".crypto", ".enc",
    ".crypted", ".ransom", ".wncry", ".dark"
)

# ANSI terminal formatting (compatible with Windows PowerShell/Terminal)
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"


# --------------------------------------------------
# DETECTION ENGINE
# --------------------------------------------------

def analyze_telemetry_run(run_id=None):
    """
    Analyzes telemetry records for a given run_id (or latest run).
    Computes multi-signal behavioral scores and early-warning containment metrics.
    """
    if not DATABASE_PATH.exists():
        print("[!] Telemetry database does not exist.")
        return None

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    # Determine run to analyze
    if not run_id:
        cursor.execute("SELECT run_id FROM file_events ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        if not result:
            print("[!] No telemetry data found in database.")
            connection.close()
            return None
        run_id = result[0]

    # Fetch total events
    cursor.execute("SELECT COUNT(*) FROM file_events WHERE run_id = ?", (run_id,))
    total_events = cursor.fetchone()[0]

    if total_events == 0:
        print(f"[!] No events recorded for run {run_id}.")
        connection.close()
        return None

    # Fetch event breakdown
    cursor.execute("SELECT COUNT(*) FROM file_events WHERE run_id = ? AND event_type = 'CREATE'", (run_id,))
    create_events = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM file_events WHERE run_id = ? AND event_type = 'MODIFY'", (run_id,))
    modify_events = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM file_events WHERE run_id = ? AND event_type = 'DELETE'", (run_id,))
    delete_events = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT file_path) FROM file_events WHERE run_id = ?", (run_id,))
    unique_files = cursor.fetchone()[0]

    # Extension churn detection
    cursor.execute("SELECT file_path FROM file_events WHERE run_id = ? AND event_type = 'MOVE_TO'", (run_id,))
    move_to_paths = [row[0] for row in cursor.fetchall()]
    extension_changes = sum(1 for p in move_to_paths if any(p.endswith(ext) for ext in SUSPICIOUS_EXTENSIONS))

    # Time range and Operations per second
    cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM file_events WHERE run_id = ?", (run_id,))
    start_time, end_time = cursor.fetchone()

    duration_seconds = 0.0
    operations_per_second = 0.0
    if start_time and end_time:
        try:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
            duration_seconds = max((end_dt - start_dt).total_seconds(), 0.05)
            operations_per_second = total_events / duration_seconds
        except ValueError:
            pass

    # Shannon Entropy metrics
    cursor.execute("""
        SELECT AVG(entropy), MAX(entropy), COUNT(CASE WHEN entropy >= ? THEN 1 END)
        FROM file_events
        WHERE run_id = ? AND entropy IS NOT NULL
    """, (ENTROPY_THRESHOLD, run_id))
    avg_entropy, max_entropy, high_entropy_count = cursor.fetchone()
    avg_entropy = avg_entropy or 0.0
    max_entropy = max_entropy or 0.0

    # --------------------------------------------------
    # MULTI-SIGNAL RISK SCORING (0 to 100)
    # --------------------------------------------------

    # Signal 1: Operation Burst Rate (Max 35 pts)
    if operations_per_second >= OPERATION_RATE_THRESHOLD:
        burst_score = 35
    elif operations_per_second >= (OPERATION_RATE_THRESHOLD * 0.5):
        burst_score = 18
    elif operations_per_second >= 5.0:
        burst_score = 8
    else:
        burst_score = 0

    # Signal 2: Modification Burst (Max 25 pts)
    if modify_events >= MODIFICATION_THRESHOLD:
        modification_score = 25
    elif modify_events >= (MODIFICATION_THRESHOLD * 0.4):
        modification_score = 12
    else:
        modification_score = 0

    # Signal 3: Extension Churn (Max 20 pts)
    if extension_changes >= EXTENSION_CHANGE_THRESHOLD:
        extension_score = 20
    elif extension_changes >= 1:
        extension_score = 10
    else:
        extension_score = 0

    # Signal 4: Cryptographic Entropy Anomaly (Max 20 pts)
    if high_entropy_count >= 5 or avg_entropy >= ENTROPY_THRESHOLD:
        entropy_score = 20
    elif high_entropy_count >= 1 or avg_entropy >= 6.0:
        entropy_score = 10
    else:
        entropy_score = 0

    total_risk_score = min(burst_score + modification_score + extension_score + entropy_score, 100)

    # Determine alert level
    if total_risk_score >= 65:
        alert_level = "CRITICAL / HIGH"
        alert_color = RED
    elif total_risk_score >= 35:
        alert_level = "ELEVATED / MEDIUM"
        alert_color = YELLOW
    elif total_risk_score >= 15:
        alert_level = "LOW ANOMALY"
        alert_color = CYAN
    else:
        alert_level = "NORMAL BASELINE"
        alert_color = GREEN

    # --------------------------------------------------
    # EARLY WARNING CONTAINMENT ESTIMATE
    # --------------------------------------------------
    # If suspicious, find the timestamp/event where cumulative score breached threshold
    detection_time_sec = None
    files_at_detection = None
    containment_pct = None

    if total_risk_score >= 35:
        cursor.execute("""
            SELECT id, timestamp, event_type, entropy
            FROM file_events
            WHERE run_id = ?
            ORDER BY id ASC
        """, (run_id,))
        rows = cursor.fetchall()

        mod_count = 0
        ext_count = 0
        hi_ent_count = 0
        detection_ts = None

        for r_id, r_ts, r_type, r_entropy in rows:
            if r_type == "MODIFY":
                mod_count += 1
            if r_type == "MOVE_TO":
                ext_count += 1
            if r_entropy and r_entropy >= ENTROPY_THRESHOLD:
                hi_ent_count += 1

            # Early warning condition triggered
            if (mod_count >= 10 and hi_ent_count >= 3) or (ext_count >= 5 and mod_count >= 5):
                detection_ts = r_ts
                files_at_detection = mod_count
                break

        if detection_ts and start_time:
            try:
                t0 = datetime.fromisoformat(start_time)
                td = datetime.fromisoformat(detection_ts)
                detection_time_sec = max((td - t0).total_seconds(), 0.05)
                if unique_files > 0:
                    containment_pct = round(max(0, (unique_files - files_at_detection) / unique_files * 100), 1)
            except ValueError:
                pass

    connection.close()

    metrics = {
        "run_id": run_id,
        "total_events": total_events,
        "unique_files": unique_files,
        "create_events": create_events,
        "modify_events": modify_events,
        "delete_events": delete_events,
        "extension_changes": extension_changes,
        "duration_seconds": duration_seconds,
        "operations_per_second": operations_per_second,
        "avg_entropy": avg_entropy,
        "max_entropy": max_entropy,
        "high_entropy_count": high_entropy_count,
        "burst_score": burst_score,
        "modification_score": modification_score,
        "extension_score": extension_score,
        "entropy_score": entropy_score,
        "total_risk_score": total_risk_score,
        "alert_level": alert_level,
        "alert_color": alert_color,
        "detection_time_sec": detection_time_sec,
        "files_at_detection": files_at_detection,
        "containment_pct": containment_pct
    }

    return metrics


def display_report(metrics):
    """
    Renders a formatted, presentation-grade cybersecurity assessment.
    """
    if not metrics:
        return

    color = metrics["alert_color"]

    print()
    print("=" * 68)
    print(f" {BOLD}RANSOMWARE EARLY-WARNING TELEMETRY DETECTOR{RESET}")
    print("=" * 68)
    print(f" Analyzed Run ID      : {metrics['run_id']}")
    print(f" Monitoring Duration  : {metrics['duration_seconds']:.2f} seconds")
    print(f" Total Events Logged  : {metrics['total_events']} ({metrics['unique_files']} distinct files)")

    print("\n" + "-" * 68)
    print(f" {BOLD}BEHAVIORAL TELEMETRY FEATURES{RESET}")
    print("-" * 68)
    print(f"  Throughput Rate     : {metrics['operations_per_second']:.2f} operations/sec")
    print(f"  Modify Operations   : {metrics['modify_events']}")
    print(f"  Extension Changes   : {metrics['extension_changes']} (suspicious targets)")
    print(f"  Average Entropy     : {metrics['avg_entropy']:.4f} (Max: {metrics['max_entropy']:.4f})")
    print(f"  High-Entropy Files  : {metrics['high_entropy_count']} (H >= {ENTROPY_THRESHOLD})")

    print("\n" + "-" * 68)
    print(f" {BOLD}MULTI-SIGNAL HEURISTIC SCORECARD{RESET}")
    print("-" * 68)
    print(f"  [1] Operation Burst Signal   : {metrics['burst_score']:>2} / 35")
    print(f"  [2] Modification Burst Signal: {metrics['modification_score']:>2} / 25")
    print(f"  [3] Extension Churn Signal   : {metrics['extension_score']:>2} / 20")
    print(f"  [4] Cryptographic Entropy    : {metrics['entropy_score']:>2} / 20")
    print("-" * 68)
    print(f"  TOTAL RISK SCORE             : {color}{BOLD}{metrics['total_risk_score']} / 100{RESET}")
    print(f"  THREAT CLASSIFICATION        : {color}{BOLD}[ {metrics['alert_level']} ]{RESET}")
    print("=" * 68)

    # Early Warning & Blast Radius Analysis
    if metrics["detection_time_sec"] is not None and metrics["containment_pct"] is not None:
        print(f"\n{BOLD}EARLY WARNING & CONTAINMENT METRICS (INCIDENT RESPONSE):{RESET}")
        print(f"  [+] Early Warning Trigger Time : {metrics['detection_time_sec']:.2f}s into attack")
        print(f"  [+] Files Affected at Alert    : {metrics['files_at_detection']} of {metrics['unique_files']} files")
        print(f"  [+] Potential Blast Containment: {metrics['containment_pct']}% of user files preserved!")
        print("-" * 68)

    # Explanation and forensic insights
    print(f"\n{BOLD}FORENSIC EXPLANATION & INSIGHTS:{RESET}")
    if metrics["burst_score"] > 0:
        print("  [!] High file transaction frequency indicates automated script or malicious process.")
    if metrics["modification_score"] > 0:
        print("  [!] Dense burst of file modifications detected in short window.")
    if metrics["extension_score"] > 0:
        print("  [!] Files renamed to suspicious extensions typical of ransomware families.")
    if metrics["entropy_score"] > 0:
        print("  [!] Shannon entropy >= 7.0 detected, strongly indicating cryptographic encryption payload.")
    if metrics["total_risk_score"] < 15:
        print("  [OK] File operations remain within benign operational thresholds. No anomalies detected.")
    print()


def main():
    parser = argparse.ArgumentParser(description="Ransomware Early-Warning Behavioral Detector")
    parser.add_argument("--run", type=str, help="Specific run_id to analyze (defaults to latest)")
    args = parser.parse_args()

    metrics = analyze_telemetry_run(run_id=args.run)
    display_report(metrics)


if __name__ == "__main__":
    main()