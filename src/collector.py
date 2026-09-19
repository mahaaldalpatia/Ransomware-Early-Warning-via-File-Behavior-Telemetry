import os
import sqlite3
import hashlib
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


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

def initialize_database():
    DATABASE_DIR.mkdir(exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER,
            sha256 TEXT
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
# RECORD EVENT
# --------------------------------------------------

def record_event(event_type, file_path):

    timestamp = datetime.now().isoformat(timespec="milliseconds")

    file_size = None
    file_hash = None

    if os.path.isfile(file_path):

        try:
            file_size = os.path.getsize(file_path)
            file_hash = calculate_sha256(file_path)

        except OSError:
            pass

    connection = sqlite3.connect(DATABASE_PATH)

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO file_events
        (
            timestamp,
            event_type,
            file_path,
            file_size,
            sha256
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        timestamp,
        event_type,
        str(file_path),
        file_size,
        file_hash
    ))

    connection.commit()
    connection.close()

    print(
        f"[{timestamp}] "
        f"{event_type:<8} "
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
    print(" File Telemetry Collector")
    print("=" * 60)

    print(f"Monitoring : {WATCH_DIR}")
    print(f"Database   : {DATABASE_PATH}")
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


if __name__ == "__main__":
    main()