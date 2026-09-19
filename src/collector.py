import os
import sqlite3
import hashlib
import math

from datetime import datetime
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

WATCH_DIR = BASE_DIR / "test_data"

DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "telemetry.db"

# A unique ID for every collector run
RUN_ID = datetime.now().strftime("RUN_%Y%m%d_%H%M%S")


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

def initialize_database():
    """
    Create the database and file_events table if they
    do not already exist.
    """

    DATABASE_DIR.mkdir(exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER,
            sha256 TEXT,
            entropy REAL
        )
    """)

    connection.commit()
    connection.close()


# --------------------------------------------------
# FILE HASH
# --------------------------------------------------

def calculate_sha256(file_path):
    """
    Calculate SHA-256 hash of a file.

    Returns None if the file cannot be read.
    """

    try:
        sha256 = hashlib.sha256()

        with open(file_path, "rb") as file:
            while chunk := file.read(8192):
                sha256.update(chunk)

        return sha256.hexdigest()

    except (FileNotFoundError, PermissionError, OSError):
        return None


# --------------------------------------------------
# FILE ENTROPY
# --------------------------------------------------

def calculate_entropy(file_path):
    """
    Calculate Shannon entropy of a file.

    Entropy range:
        0.0 -> very predictable data
        8.0 -> highly random-looking data

    Returns None if the file cannot be read.
    """

    try:
        with open(file_path, "rb") as file:
            data = file.read()

        if not data:
            return 0.0

        # Count frequency of every possible byte value
        frequency = [0] * 256

        for byte in data:
            frequency[byte] += 1

        entropy = 0.0
        data_length = len(data)

        for count in frequency:

            if count == 0:
                continue

            probability = count / data_length

            entropy -= probability * math.log2(probability)

        return round(entropy, 4)

    except (FileNotFoundError, PermissionError, OSError):
        return None


# --------------------------------------------------
# RECORD EVENT
# --------------------------------------------------

def record_event(event_type, file_path):
    """
    Record a filesystem event in SQLite.
    """

    timestamp = datetime.now().isoformat(timespec="milliseconds")

    file_size = None
    file_hash = None
    file_entropy = None

    # File may disappear immediately after an event,
    # so all file calculations are protected.
    if os.path.isfile(file_path):

        try:
            file_size = os.path.getsize(file_path)

            file_hash = calculate_sha256(file_path)

            file_entropy = calculate_entropy(file_path)

        except OSError:
            pass

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO file_events
        (
            run_id,
            timestamp,
            event_type,
            file_path,
            file_size,
            sha256,
            entropy
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        RUN_ID,
        timestamp,
        event_type,
        str(file_path),
        file_size,
        file_hash,
        file_entropy
    ))

    connection.commit()
    connection.close()

    print(
        f"[{timestamp}] "
        f"{event_type:<10} "
        f"{file_path}"
    )


# --------------------------------------------------
# EVENT HANDLER
# --------------------------------------------------

class FileTelemetryHandler(FileSystemEventHandler):

    def on_created(self, event):

        if not event.is_directory:

            record_event(
                "CREATE",
                event.src_path
            )

    def on_modified(self, event):

        if not event.is_directory:

            record_event(
                "MODIFY",
                event.src_path
            )

    def on_deleted(self, event):

        if not event.is_directory:

            record_event(
                "DELETE",
                event.src_path
            )

    def on_moved(self, event):

        if not event.is_directory:

            record_event(
                "MOVE_FROM",
                event.src_path
            )

            record_event(
                "MOVE_TO",
                event.dest_path
            )


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    # Make sure required directories exist
    WATCH_DIR.mkdir(exist_ok=True)

    initialize_database()

    event_handler = FileTelemetryHandler()

    observer = Observer()

    observer.schedule(
        event_handler,
        str(WATCH_DIR),
        recursive=True
    )

    observer.start()

    print("=" * 60)
    print(" RANSOMWARE EARLY-WARNING")
    print(" FILE TELEMETRY COLLECTOR")
    print("=" * 60)

    print(f"Monitoring : {WATCH_DIR}")
    print(f"Database   : {DATABASE_PATH}")
    print(f"Run ID     : {RUN_ID}")

    print()
    print("Monitoring file activity...")
    print("Press CTRL+C to stop.")
    print("=" * 60)

    try:

        while True:
            observer.join(1)

    except KeyboardInterrupt:

        print("\nStopping collector...")

        observer.stop()

    observer.join()


# --------------------------------------------------
# PROGRAM ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    main()