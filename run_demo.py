import sys
import os
import time
import subprocess
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.detector import analyze_telemetry_run, display_report
from src.dashboard import generate_dashboard
from src.generate_report import generate_incident_report
from src.simulator import cleanup, normal_activity, suspicious_activity, populate_real_world_files, DEFAULT_TARGET_DIR


def print_banner():
    print("\n" + "=" * 70)
    print("      REAL-WORLD RANSOMWARE EARLY-WARNING TELEMETRY SYSTEM")
    print("        ENTERPRISE MULTI-FORMAT TEST & DEMONSTRATION SUITE")
    print("=" * 70)


def run_with_collector(simulation_func, sim_name, watch_dir=None, sim_args=None):
    """
    Spawns the real-world collector targeting watch_dir, executes the simulation,
    waits for telemetry to flush, and displays the detector report.
    """
    python_exe = sys.executable
    target_path = Path(watch_dir) if watch_dir else DEFAULT_TARGET_DIR
    target_path.mkdir(parents=True, exist_ok=True)

    collector_cmd = [python_exe, str(BASE_DIR / "src" / "collector.py"), "--watch", str(target_path)]

    print(f"\n[+] Starting Real-World Telemetry Collector on: {target_path}...")
    collector_process = subprocess.Popen(
        collector_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Allow watchdog observer to initialize
    time.sleep(1.5)
    print(f"[+] Sensor active. Launching {sim_name}...")

    try:
        if sim_args:
            simulation_func(*sim_args)
        else:
            simulation_func(target_dir=target_path)
    finally:
        time.sleep(2.0)
        print("\n[+] Flushing telemetry queue and stopping collector...")
        collector_process.terminate()
        try:
            collector_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            collector_process.kill()

    print("[+] Telemetry capture complete.")
    print("\n[+] Running Real-World Behavioral Detector on captured run...")
    time.sleep(0.5)
    metrics = analyze_telemetry_run()
    display_report(metrics)


def demo_normal_activity(target_dir=None):
    target = Path(target_dir) if target_dir else DEFAULT_TARGET_DIR
    print("\n" + "#" * 70)
    print(" DEMO 1: BENIGN / NORMAL OFFICE WORKLOAD BASELINE")
    print(f" Target: {target.resolve()}")
    print(" Simulates human office work: editing CSV ledgers, saving memos, archiving.")
    print("#" * 70)
    cleanup(target)
    populate_real_world_files(target)
    time.sleep(1.0)
    run_with_collector(normal_activity, "Normal Office Workload", watch_dir=target)


def demo_ransomware_attack(target_dir=None):
    target = Path(target_dir) if target_dir else DEFAULT_TARGET_DIR
    print("\n" + "#" * 70)
    print(" DEMO 2: REAL-WORLD RANSOMWARE ENCRYPTION ATTACK SIMULATION")
    print(f" Target: {target.resolve()}")
    print(" Target Formats: .pdf, .docx, .csv, .png, .json, .sql, .txt")
    print(" Simulates high-speed cryptographic overwrite + .locked extension churn.")
    print("#" * 70)
    cleanup(target)
    populate_real_world_files(target)
    time.sleep(1.0)
    run_with_collector(suspicious_activity, "Ransomware Attack Simulation", watch_dir=target, sim_args=(target, ".locked", 0.04))


def demo_custom_folder():
    print("\n" + "-" * 70)
    print(" MONITOR A CUSTOM REAL-WORLD DIRECTORY ON THIS COMPUTER")
    print("-" * 70)
    print(" You can point the sensor to ANY folder on your PC (e.g. Documents/TestFolder).")
    custom_path = input(" Enter full folder path to monitor: ").strip().strip('"')

    if not custom_path:
        print("[!] No path provided. Returning to menu.")
        return

    folder = Path(custom_path)
    if not folder.exists():
        create_it = input(f" [?] Folder {folder} does not exist. Create it? [Y/n]: ").strip().lower()
        if create_it != 'n':
            folder.mkdir(parents=True, exist_ok=True)
        else:
            return

    print(f"\n[OK] Attached to target: {folder.resolve()}")
    print(" 1. Run Normal Office Workload on this folder")
    print(" 2. Run Ransomware Attack Simulation on this folder")
    print(" 3. Start Live Monitor only (you modify files manually in Windows Explorer)")
    print(" 4. Back to Main Menu")

    choice = input("\n Select option [1-4]: ").strip()
    if choice == "1":
        demo_normal_activity(target_dir=folder)
    elif choice == "2":
        demo_ransomware_attack(target_dir=folder)
    elif choice == "3":
        print(f"\n[+] Starting live collector on {folder.resolve()} for 30 seconds.")
        print("    Open this folder in Windows Explorer and create, edit, or rename files.")
        print("    Press CTRL+C anytime to stop.\n")
        subprocess.run([sys.executable, str(BASE_DIR / "src" / "collector.py"), "--watch", str(folder)])
        metrics = analyze_telemetry_run()
        display_report(metrics)


def demo_dashboard():
    print("\n[+] Generating Visual Telemetry Analytics Dashboard...")
    generate_dashboard(show_gui=True)


def demo_report():
    print("\n[+] Generating Project Evaluation & Incident Report...")
    generate_incident_report()


def main_menu():
    while True:
        print_banner()
        print("  1. Run Real-World Normal Baseline (Multi-Format: PDF, DOCX, CSV, PNG, TXT)")
        print("  2. Run Real-World Ransomware Attack (High-Entropy Overwrite across Real Files)")
        print("  3. Monitor a Custom Real Folder on this PC (e.g. Documents / Desktop)")
        print("  4. Run Post-Incident Forensic Detector (Detailed Scorecard & File Breakdown)")
        print("  5. View Visual Telemetry Dashboard (4-Panel Chart & PNG Export)")
        print("  6. Generate Incident Report (Markdown/Text in reports/)")
        print("  7. Clean Up Test Directory")
        print("  8. Exit")
        print("=" * 70)

        choice = input(" Select option [1-8]: ").strip()

        if choice == "1":
            demo_normal_activity()
        elif choice == "2":
            demo_ransomware_attack()
        elif choice == "3":
            demo_custom_folder()
        elif choice == "4":
            metrics = analyze_telemetry_run()
            display_report(metrics)
        elif choice == "5":
            demo_dashboard()
        elif choice == "6":
            demo_report()
        elif choice == "7":
            cleanup()
        elif choice == "8":
            print("\nExiting Demonstration Suite. Good luck with your presentation!")
            break
        else:
            print("\n[!] Invalid selection. Please enter a number between 1 and 8.")

        input("\nPress ENTER to return to menu...")


if __name__ == "__main__":
    main_menu()
