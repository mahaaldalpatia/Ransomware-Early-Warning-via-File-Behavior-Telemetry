import time
import random
from pathlib import Path


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
TEST_DIR = BASE_DIR / "test_data"

NORMAL_FILE_COUNT = 20
SUSPICIOUS_FILE_COUNT = 100


# --------------------------------------------------
# UTILITY FUNCTIONS
# --------------------------------------------------

def create_test_files(count, prefix):
    """
    Create harmless synthetic text files.
    """

    print(f"\nCreating {count} synthetic files...")

    for i in range(count):

        file_path = TEST_DIR / f"{prefix}_{i:03d}.txt"

        content = (
            f"This is synthetic test file {i}.\n"
            f"It is used for the ransomware early-warning project.\n"
            f"Test data only.\n"
        )

        file_path.write_text(content)

    print("File creation completed.")


def modify_file(file_path):
    """
    Modify a synthetic file.
    """

    with open(file_path, "a") as file:
        file.write(
            "\nAdditional synthetic test data.\n"
        )


# --------------------------------------------------
# NORMAL ACTIVITY
# --------------------------------------------------

def normal_activity():

    print("\n" + "=" * 60)
    print("NORMAL ACTIVITY SIMULATION")
    print("=" * 60)

    create_test_files(
        NORMAL_FILE_COUNT,
        "normal"
    )

    files = list(TEST_DIR.glob("normal_*.txt"))

    print("\nModifying a small number of files...")

    selected_files = random.sample(
        files,
        min(3, len(files))
    )

    for file_path in selected_files:

        modify_file(file_path)

        print(f"Modified: {file_path.name}")

        time.sleep(1)

    print("\nRenaming a few files...")

    selected_files = random.sample(
        files,
        min(2, len(files))
    )

    for index, file_path in enumerate(selected_files):

        new_path = file_path.with_name(
            f"normal_renamed_{index:03d}.txt"
        )

        file_path.rename(new_path)

        print(
            f"Renamed: {file_path.name} "
            f"-> {new_path.name}"
        )

        time.sleep(1)

    print("\nNormal activity completed.")


# --------------------------------------------------
# SUSPICIOUS ACTIVITY
# --------------------------------------------------

def suspicious_activity():

    print("\n" + "=" * 60)
    print("CONTROLLED SUSPICIOUS ACTIVITY SIMULATION")
    print("=" * 60)

    print(
        "\nThis simulation performs harmless "
        "mass file operations."
    )

    create_test_files(
        SUSPICIOUS_FILE_COUNT,
        "suspicious"
    )

    files = list(TEST_DIR.glob("suspicious_*.txt"))

    # ----------------------------------------------
    # MASS MODIFICATION
    # ----------------------------------------------

    print(
        "\nPerforming rapid modifications "
        "on synthetic files..."
    )

    for file_path in files:

        modify_file(file_path)

    print(
        f"Modified {len(files)} files rapidly."
    )

    # ----------------------------------------------
    # EXTENSION CHURN
    # ----------------------------------------------

    print(
        "\nChanging synthetic file extensions..."
    )

    current_files = list(
        TEST_DIR.glob("suspicious_*.txt")
    )

    for file_path in current_files:

        new_path = file_path.with_suffix(
            ".locked_test"
        )

        file_path.rename(new_path)

    print(
        f"Changed extensions of "
        f"{len(current_files)} files."
    )

    print("\nSuspicious activity simulation completed.")


# --------------------------------------------------
# CLEANUP
# --------------------------------------------------

def cleanup():

    print("\nCleaning simulator files...")

    patterns = [
        "normal_*.txt",
        "suspicious_*.txt",
        "suspicious_*.locked_test"
    ]

    deleted = 0

    for pattern in patterns:

        for file_path in TEST_DIR.glob(pattern):

            file_path.unlink()

            deleted += 1

    print(f"Deleted {deleted} synthetic files.")


# --------------------------------------------------
# MENU
# --------------------------------------------------

def main():

    TEST_DIR.mkdir(exist_ok=True)

    while True:

        print("\n")
        print("=" * 60)
        print(" RANSOMWARE EARLY-WARNING TEST SIMULATOR")
        print("=" * 60)

        print("1. Normal activity")
        print("2. Suspicious activity")
        print("3. Cleanup test files")
        print("4. Exit")

        choice = input("\nSelect an option: ").strip()

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

            print("Invalid option.")


if __name__ == "__main__":
    main()