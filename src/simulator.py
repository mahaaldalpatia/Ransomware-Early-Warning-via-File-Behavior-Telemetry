import os
import time
import random
from pathlib import Path


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
TEST_DIR = BASE_DIR / "test_data"

NORMAL_FILE_COUNT = 20
SUSPICIOUS_FILE_COUNT = 60


# --------------------------------------------------
# UTILITY FUNCTIONS
# --------------------------------------------------

def create_test_files(count, prefix):
    """
    Create harmless synthetic text files with normal English text (low entropy ~4.0).
    """
    TEST_DIR.mkdir(exist_ok=True)
    print(f"\n[+] Generating {count} synthetic test documents ({prefix}_*.txt)...")

    sample_texts = [
        "Quarterly Financial and Performance Report for Internal Review.\n"
        "Budget allocations and projected expenditures for the upcoming fiscal cycle.\n"
        "All departmental teams are requested to submit receipts by end of week.\n",
        
        "System Architecture and Deployment Guidelines.\n"
        "Microservices communication protocols, authentication tokens, and caching layers.\n"
        "Ensure all endpoints are verified before promoting to production.\n",
        
        "Employee Onboarding and Security Policies Documentation.\n"
        "Guidelines regarding remote access, password complexity, and data privacy compliance.\n"
        "Confidential information must remain within authorized network perimeter.\n"
    ]

    for i in range(count):
        file_path = TEST_DIR / f"{prefix}_{i:03d}.txt"
        body = random.choice(sample_texts)
        content = (
            f"FILE ID: {prefix.upper()}-{i:04d}\n"
            f"CREATED: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"--------------------------------------------------\n"
            f"{body}\n"
            f"Record status: ACTIVE\n"
        )
        file_path.write_text(content, encoding="utf-8")

    print(f"[OK] {count} files successfully generated in {TEST_DIR.name}/")


def modify_normal_file(file_path):
    """
    Perform benign file edit (appends plain text, keeps entropy normal).
    """
    with open(file_path, "a", encoding="utf-8") as file:
        file.write(f"\n[Updated at {time.strftime('%H:%M:%S')}] User edit: added remarks and review notes.\n")


def encrypt_file_simulated(file_path):
    """
    Simulate ransomware encryption behavior:
    Overwrites the file with pseudorandom ciphertext bytes.
    This raises Shannon entropy to ~7.8 - 7.95, mimicking AES/ChaCha20 encryption.
    """
    original_size = file_path.stat().st_size if file_path.exists() else 512
    # Create high-entropy pseudo-random ciphertext
    cipher_bytes = os.urandom(max(original_size, 256))
    
    # Overwrite the original document with high-entropy bytes
    with open(file_path, "wb") as f:
        f.write(cipher_bytes)


# --------------------------------------------------
# NORMAL ACTIVITY SIMULATION
# --------------------------------------------------

def normal_activity():
    """
    Simulates everyday benign user behavior:
    - Moderate file creation
    - Occasional edits with realistic human pauses
    - Benign file renames
    """
    print("\n" + "=" * 65)
    print("      NORMAL USER ACTIVITY SIMULATION (BENIGN BASELINE)")
    print("=" * 65)

    create_test_files(NORMAL_FILE_COUNT, "normal")
    files = list(TEST_DIR.glob("normal_*.txt"))

    print("\n[+] Simulating normal user document edits (with realistic delay)...")
    selected_files = random.sample(files, min(4, len(files)))

    for file_path in selected_files:
        modify_normal_file(file_path)
        print(f"  [User Action] Saved updates to {file_path.name}")
        time.sleep(0.8)

    print("\n[+] Simulating normal file renaming (e.g. archiving/drafting)...")
    rename_targets = [f for f in files if f not in selected_files][:2]

    for index, file_path in enumerate(rename_targets):
        new_path = file_path.with_name(f"normal_archive_{index:03d}.txt")
        file_path.rename(new_path)
        print(f"  [User Action] Renamed: {file_path.name} -> {new_path.name}")
        time.sleep(0.8)

    print("\n[OK] Normal benign activity simulation completed.")
    print("=" * 65)


# --------------------------------------------------
# SUSPICIOUS / RANSOMWARE ACTIVITY SIMULATION
# --------------------------------------------------

def suspicious_activity(target_extension=".locked_test", delay=0.03):
    """
    Simulates real-world ransomware attack dynamics:
    1. Rapid burst of file modifications
    2. Cryptographic payload overwrite (spiking Shannon entropy to ~7.9)
    3. Mass extension changes to ransomware indicators (.locked_test, .crypto, etc.)
    4. Optional ransom note creation
    """
    print("\n" + "=" * 65)
    print("     CONTROLLED RANSOMWARE ATTACK SIMULATION (MALICIOUS)")
    print("=" * 65)
    print(" Warning: Simulates high-speed encryption burst and extension churn.")
    print(f" Target count: {SUSPICIOUS_FILE_COUNT} files | Extension: {target_extension}")

    # Generate baseline test files to encrypt
    create_test_files(SUSPICIOUS_FILE_COUNT, "suspicious")
    files = list(TEST_DIR.glob("suspicious_*.txt"))

    print("\n[!] STAGE 1: Launching high-speed cryptographic file encryption...")
    print("    (Watch entropy jump from ~4.0 to ~7.9+ in telemetry)\n")

    encrypted_count = 0
    for file_path in files:
        encrypt_file_simulated(file_path)
        encrypted_count += 1
        if encrypted_count % 10 == 0 or encrypted_count == len(files):
            print(f"  [*] Encrypted {encrypted_count}/{len(files)} files...")
        if delay > 0:
            time.sleep(delay)

    print(f"[OK] High-speed encryption complete on {len(files)} files.")

    print(f"\n[!] STAGE 2: Mass extension alteration (appending {target_extension})...\n")

    renamed_count = 0
    current_files = list(TEST_DIR.glob("suspicious_*.txt"))
    for file_path in current_files:
        new_path = file_path.with_suffix(target_extension)
        file_path.rename(new_path)
        renamed_count += 1
        if renamed_count % 10 == 0 or renamed_count == len(current_files):
            print(f"  [*] Renamed {renamed_count}/{len(current_files)} files -> {target_extension}")
        if delay > 0:
            time.sleep(delay)

    # Stage 3: Drop Ransom Note
    ransom_note = TEST_DIR / "README_DECRYPT_FILES.txt"
    ransom_note.write_text(
        "!!! YOUR FILES HAVE BEEN ENCRYPTED (SIMULATION) !!!\n"
        "This is an academic simulation for Ransomware Early-Warning Telemetry.\n"
        "All original data was synthetic test data.\n",
        encoding="utf-8"
    )
    print(f"\n[!] STAGE 3: Dropped simulated ransom note ({ransom_note.name}).")

    print("\n[OK] Ransomware attack simulation completed.")
    print("=" * 65)


# --------------------------------------------------
# CLEANUP
# --------------------------------------------------

def cleanup():
    """
    Safely removes synthetic test files and simulated ransom notes.
    """
    print("\n[+] Cleaning simulated test files from test_data/...")

    patterns = [
        "normal_*.txt",
        "suspicious_*.txt",
        "*.locked_test",
        "*.crypto",
        "*.enc",
        "README_DECRYPT_FILES.txt"
    ]

    deleted = 0
    for pattern in patterns:
        for file_path in TEST_DIR.glob(pattern):
            try:
                file_path.unlink()
                deleted += 1
            except OSError:
                pass

    print(f"[OK] Deleted {deleted} test files. Test directory clean.")


# --------------------------------------------------
# INTERACTIVE MENU
# --------------------------------------------------

def main():
    TEST_DIR.mkdir(exist_ok=True)

    while True:
        print("\n" + "=" * 60)
        print("    RANSOMWARE EARLY-WARNING TEST SIMULATOR")
        print("=" * 60)
        print(" 1. Run Normal Activity Simulation (Benign Baseline)")
        print(" 2. Run Ransomware Attack Simulation (High Entropy & Extension Churn)")
        print(" 3. Cleanup Test Directory")
        print(" 4. Exit")

        choice = input("\nSelect an option [1-4]: ").strip()

        if choice == "1":
            normal_activity()
        elif choice == "2":
            suspicious_activity()
        elif choice == "3":
            cleanup()
        elif choice == "4":
            print("Exiting simulator.")
            break
        else:
            print("[!] Invalid option. Please enter 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()