import sys
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

import matplotlib
import matplotlib.pyplot as plt
import numpy as np


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "telemetry.db"
REPORTS_DIR = BASE_DIR / "reports"
OUTPUT_IMAGE = REPORTS_DIR / "telemetry_analysis.png"

ENTROPY_THRESHOLD = 7.0


def generate_dashboard(run_id=None, show_gui=True):
    """
    Generates a 4-panel visual analytics dashboard for telemetry
    and saves high-resolution plot to reports/.
    """
    REPORTS_DIR.mkdir(exist_ok=True)

    if not DATABASE_PATH.exists():
        print("[!] Database not found at", DATABASE_PATH)
        return False

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    if not run_id:
        cursor.execute("SELECT run_id FROM file_events ORDER BY id DESC LIMIT 1")
        res = cursor.fetchone()
        if not res:
            print("[!] No telemetry events in database.")
            connection.close()
            return False
        run_id = res[0]

    # Fetch event data
    cursor.execute("""
        SELECT timestamp, event_type, entropy, file_path
        FROM file_events
        WHERE run_id = ?
        ORDER BY id ASC
    """, (run_id,))
    rows = cursor.fetchall()
    connection.close()

    if not rows:
        print(f"[!] No rows found for run: {run_id}")
        return False

    timestamps = [r[0] for r in rows]
    event_types = [r[1] for r in rows]
    entropies = [r[2] for r in rows if r[2] is not None]

    # Calculate time deltas in seconds from start
    try:
        t0 = datetime.fromisoformat(timestamps[0])
        time_offsets = [(datetime.fromisoformat(t) - t0).total_seconds() for t in timestamps]
    except Exception:
        time_offsets = list(range(len(timestamps)))

    # Set up matplotlib style
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig, axs = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle(f"Ransomware Early-Warning Telemetry Dashboard\nRun ID: {run_id}", fontsize=15, fontweight='bold', y=0.98)

    # --------------------------------------------------
    # Panel 1: Event Type Breakdown (Bar Chart)
    # --------------------------------------------------
    ax1 = axs[0, 0]
    types_order = ["CREATE", "MODIFY", "DELETE", "MOVE_FROM", "MOVE_TO"]
    type_counts = {t: event_types.count(t) for t in types_order}
    # Also include any other type
    for t in set(event_types):
        if t not in type_counts:
            type_counts[t] = event_types.count(t)

    labels = list(type_counts.keys())
    counts = list(type_counts.values())
    colors = ['#2b5c8f', '#d9534f', '#f0ad4e', '#5bc0de', '#5cb85c'][:len(labels)]

    bars = ax1.bar(labels, counts, color=colors, edgecolor='black', alpha=0.85)
    ax1.set_title("1. Filesystem Event Distribution", fontsize=11, fontweight='bold')
    ax1.set_ylabel("Count of Events")
    ax1.grid(axis='y', linestyle='--', alpha=0.7)

    # Label bars with numbers
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax1.annotate(f'{height}',
                         xy=(bar.get_x() + bar.get_width() / 2, height),
                         xytext=(0, 3),  # 3 points vertical offset
                         textcoords="offset points",
                         ha='center', va='bottom', fontsize=9, fontweight='bold')

    # --------------------------------------------------
    # Panel 2: Telemetry Operations Timeline (Burst Detection)
    # --------------------------------------------------
    ax2 = axs[0, 1]
    cumulative_events = list(range(1, len(time_offsets) + 1))
    ax2.plot(time_offsets, cumulative_events, color='#d9534f', lw=2.2, label='Cumulative Events')
    ax2.scatter(time_offsets[::max(1, len(time_offsets)//20)], 
                cumulative_events[::max(1, len(cumulative_events)//20)], 
                color='#900C3F', s=30, zorder=3)

    ax2.set_title("2. Activity Timeline (Burst Rate Curve)", fontsize=11, fontweight='bold')
    ax2.set_xlabel("Elapsed Time (Seconds)")
    ax2.set_ylabel("Total Cumulative Operations")
    ax2.grid(True, linestyle='--', alpha=0.7)
    
    # Calculate average OPS/s
    total_sec = max(time_offsets[-1] if time_offsets else 1, 0.1)
    ops_rate = len(rows) / total_sec
    ax2.text(0.05, 0.85, f"Total Events: {len(rows)}\nThroughput: {ops_rate:.1f} ops/s",
             transform=ax2.transAxes, fontsize=10,
             bbox=dict(boxstyle="round,pad=0.4", facecolor='wheat', alpha=0.5))

    # --------------------------------------------------
    # Panel 3: Shannon Entropy Distribution (Encryption Detector)
    # --------------------------------------------------
    ax3 = axs[1, 0]
    if entropies:
        ax3.hist(entropies, bins=15, range=(0, 8), color='#337ab7', edgecolor='black', alpha=0.75)
        ax3.axvline(ENTROPY_THRESHOLD, color='red', linestyle='--', linewidth=2, label=f'Encryption Threshold ({ENTROPY_THRESHOLD})')
        ax3.set_title("3. File Shannon Entropy Analysis", fontsize=11, fontweight='bold')
        ax3.set_xlabel("Shannon Entropy (0.0 = Plain, 8.0 = Ciphertext/Random)")
        ax3.set_ylabel("Number of File Measurements")
        ax3.set_xlim(0, 8.2)
        ax3.legend(loc='upper left', fontsize=9)
        ax3.grid(axis='y', linestyle='--', alpha=0.7)
        
        avg_h = np.mean(entropies)
        high_h_count = sum(1 for h in entropies if h >= ENTROPY_THRESHOLD)
        ax3.text(0.55, 0.75, f"Avg Entropy: {avg_h:.2f}\nEncrypted (H>=7): {high_h_count}",
                 transform=ax3.transAxes, fontsize=9,
                 bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue', alpha=0.5))
    else:
        ax3.text(0.5, 0.5, "No Entropy Telemetry Collected", ha='center', va='center')
        ax3.set_title("3. File Shannon Entropy Analysis", fontsize=11, fontweight='bold')

    # --------------------------------------------------
    # Panel 4: Heuristic Risk Score & Signal Breakdown
    # --------------------------------------------------
    ax4 = axs[1, 1]
    
    # Calculate signals
    modify_cnt = type_counts.get("MODIFY", 0)
    move_to_cnt = sum(1 for r in rows if r[1] == "MOVE_TO" and any(r[3].endswith(ext) for ext in [".locked", ".locked_test", ".crypto", ".enc"]))
    high_ent_cnt = sum(1 for h in entropies if h >= ENTROPY_THRESHOLD)
    
    s_burst = 35 if ops_rate >= 15.0 else (18 if ops_rate >= 7.5 else 0)
    s_mod = 25 if modify_cnt >= 25 else (12 if modify_cnt >= 10 else 0)
    s_ext = 20 if move_to_cnt >= 5 else (10 if move_to_cnt >= 1 else 0)
    s_ent = 20 if high_ent_cnt >= 5 or (entropies and np.mean(entropies) >= 7.0) else (10 if high_ent_cnt >= 1 else 0)
    
    total_score = min(s_burst + s_mod + s_ext + s_ent, 100)
    
    signals = ["Entropy Anomaly", "Extension Churn", "Modification Burst", "Operation Burst"]
    scores = [s_ent, s_ext, s_mod, s_burst]
    max_scores = [20, 20, 25, 35]
    
    y_pos = np.arange(len(signals))
    ax4.barh(y_pos, max_scores, color='#e0e0e0', edgecolor='gray', height=0.55, label='Max Score')
    ax4.barh(y_pos, scores, color=['#d9534f' if sc > 0 else '#5cb85c' for sc in scores], edgecolor='black', height=0.55, label='Assessed Score')
    ax4.set_yticks(y_pos)
    ax4.set_yticklabels(signals, fontsize=9, fontweight='bold')
    ax4.set_xlabel("Signal Weight (Points)")
    ax4.set_title(f"4. Early-Warning Risk Score: {total_score}/100", fontsize=11, fontweight='bold')
    ax4.set_xlim(0, 40)
    ax4.grid(axis='x', linestyle='--', alpha=0.7)

    # Color code badge
    if total_score >= 65:
        badge_color, alert_text = '#d9534f', "CRITICAL THREAT (HIGH)"
    elif total_score >= 35:
        badge_color, alert_text = '#f0ad4e', "SUSPICIOUS (MEDIUM)"
    elif total_score >= 15:
        badge_color, alert_text = '#5bc0de', "ANOMALOUS (LOW)"
    else:
        badge_color, alert_text = '#5cb85c', "BENIGN / NORMAL"

    ax4.text(0.5, -0.25, f"DETECTION RESULT: {alert_text}",
             ha='center', va='center', transform=ax4.transAxes,
             fontsize=11, fontweight='bold', color='white',
             bbox=dict(boxstyle="round,pad=0.5", facecolor=badge_color, edgecolor='black'))

    plt.tight_layout(rect=[0, 0.04, 1, 0.95])
    
    # Save high-res plot
    plt.savefig(OUTPUT_IMAGE, dpi=200, bbox_inches='tight')
    print(f"\n[OK] Visual analytics dashboard successfully saved to:\n     {OUTPUT_IMAGE}")

    if show_gui:
        try:
            print("[+] Opening interactive chart window...")
            plt.show()
        except Exception as e:
            print(f"[!] Could not open GUI window ({e}). Image is preserved in reports/.")

    plt.close()
    return True


def main():
    parser = argparse.ArgumentParser(description="Ransomware Telemetry Visual Dashboard")
    parser.add_argument("--run", type=str, help="Specific run_id to visualize")
    parser.add_argument("--no-gui", action="store_true", help="Save figure without opening GUI window")
    args = parser.parse_args()

    generate_dashboard(run_id=args.run, show_gui=not args.no_gui)


if __name__ == "__main__":
    main()
