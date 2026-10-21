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
from src.simulator import cleanup, normal_activity, suspicious_activity


def print_banner():
    print("\n" + "=" * 70)
    print("      RANSOMWARE EARLY-WARNING VIA FILE BEHAVIOR TELEMETRY")
    print("            PROTOTYPE DEMONSTRATION & EVALUATION SUITE")
    print("=" * 70)


def run_with_collector(simulation_func, sim_name, sim_args=None):
    """
    Spawns the collector in a background subprocess, executes the simulation,
    waits for writes to flush, cleanly terminates the collector, and runs the detector.
    """
    python_exe = sys.executable

    print(f"\n[+] Starting Telemetry Collector in background...")
    collector_process = subprocess.Popen(
        [python_exe, str(BASE_DIR / "src" / "collector.py")],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Allow watchdog observer to initialize
    time.sleep(1.5)
    print(f"[+] Collector active. Starting {sim_name}...")

    try:
        if sim_args:
            simulation_func(*sim_args)
        else:
            simulation_func()
    finally:
        # Give collector a moment to capture final rename/delete events
        time.sleep(2.0)
        print("\n[+] Stopping Telemetry Collector and flushing database queue...")
        collector_process.terminate()
        try:
            collector_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            collector_process.kill()

    print("[+] Telemetry capture complete.")
    print("\n[+] Running Early-Warning Detector on newly captured run...")
    time.sleep(0.5)
    metrics = analyze_telemetry_run()
    display_report(metrics)


def demo_normal_activity():
    print("\n" + "#" * 70)
    print(" DEMO 1: BENIGN / NORMAL USER ACTIVITY BASELINE")
    print(" Simulates standard office file creation, periodic edits, and renames.")
    print("#" * 70)
    cleanup()
    run_with_collector(normal_activity, "Normal User Activity")


def demo_ransomware_attack():
    print("\n" + "#" * 70)
    print(" DEMO 2: SIMULATED RANSOMWARE ENCRYPTION & EXTENSION CHURN ATTACK")
    print(" Simulates high-speed cryptographic overwrite (entropy ~7.9) & .locked_test churn.")
    print("#" * 70)
    cleanup()
    run_with_collector(suspicious_activity, "Ransomware Simulation", sim_args=(".locked_test", 0.04))


def demo_dashboard():
    print("\n[+] Generating Visual Telemetry Analytics Dashboard...")
    generate_dashboard(show_gui=True)


def demo_report():
    print("\n[+] Generating Project Evaluation & Incident Report...")
    generate_incident_report()


def demo_pdf():
    print("\n[+] Generating Project Guide & Viva Prep PDF...")
    try:
        from generate_pdf_report import create_project_pdf
        create_project_pdf()
    except Exception as e:
        print(f"[!] Error generating PDF: {e}")


def main_menu():
    while True:
        print_banner()
        print("  1. Run Benign Activity Baseline (Demonstrate Normal Status)")
        print("  2. Run Ransomware Attack Simulation (Demonstrate Live Early-Warning)")
        print("  3. Run Post-Incident Forensic Detector (Detailed Scorecard)")
        print("  4. View Visual Telemetry Dashboard (4-Panel Chart & PNG Export)")
        print("  5. Generate Comprehensive Incident Report (Markdown/Text in reports/)")
        print("  6. Export Project Guide & Viva Prep PDF (5-Page Document)")
        print("  7. Clean Up Test Directory")
        print("  8. Exit")
        print("=" * 70)

        choice = input(" Select option [1-8]: ").strip()

        if choice == "1":
            demo_normal_activity()
        elif choice == "2":
            demo_ransomware_attack()
        elif choice == "3":
            metrics = analyze_telemetry_run()
            display_report(metrics)
        elif choice == "4":
            demo_dashboard()
        elif choice == "5":
            demo_report()
        elif choice == "6":
            demo_pdf()
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
