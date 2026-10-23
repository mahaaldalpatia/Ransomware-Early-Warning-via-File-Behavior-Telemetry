import os
import sys
import sqlite3
import hashlib
import math
import time
import queue
import argparse
import threading
from collections import deque
from datetime import datetime
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_WATCH_DIR = BASE_DIR / "real_world_data"
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "telemetry.db"

# A unique ID for every collector run
RUN_ID = datetime.now().strftime("RUN_%Y%m%d_%H%M%S")

# Real-time sliding window configuration
SLIDING_WINDOW_SECONDS = 5.0
LIVE_BURST_RATE_THRESHOLD = 15.0  # ops/sec
LIVE_ENTROPY_THRESHOLD = 7.0

# System files and directories to ignore in real-world monitoring
IGNORE_FILENAMES = {
    "desktop.ini", "thumbs.db", ".ds_store", "ntuser.dat",
    "iconcache.db", ".git", ".venv", "node_modules", "__pycache__"
}
IGNORE_PREFIXES = ("~$", ".~", "tmp_", ".#")
IGNORE_SUFFIXES = (".tmp", ".crdownload", ".part", ".db-wal", ".db-shm", ".bak")

# Known suspicious ransomware extensions
SUSPICIOUS_EXTENSIONS = (
    ".locked", ".locked_test", ".crypto", ".enc",
    ".crypted", ".ransom", ".wncry", ".dark", ".vault"
)

# --------------------------------------------------
# THREAD-SAFE DATABASE WRITER & QUEUE
# --------------------------------------------------

event_queue = queue.Queue()
_db_stop_event = threading.Event()
_live_events_window = deque()
_live_alert_triggered = False
_entropy_baselines = {}  # In-memory baseline tracker: {file_path: baseline_entropy}


def should_ignore_file(file_path):
    """
    Filters out background OS noise, temporary Word/Excel lock files,
    system thumbs, and dev artifacts to keep telemetry clean and accurate.
    """
    try:
        p = Path(file_path)
        name = p.name.lower()
        if not name:
            return True
        if name in IGNORE_FILENAMES:
            return True
        if any(name.startswith(pre) for pre in IGNORE_PREFIXES):
            return True
        if any(name.endswith(suf) for suf in IGNORE_SUFFIXES):
            return True
        for part in p.parts:
            if part.lower() in IGNORE_FILENAMES:
                return True
        return False
    except Exception:
        return False


def initialize_database():
    """
    Initializes database schema, creates high-performance indices,
    and performs non-destructive schema migrations for real-world fields.
    """
    DATABASE_DIR.mkdir(exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")

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

    # Non-destructive schema migration for real-world file attributes
    cursor.execute("PRAGMA table_info(file_events)")
    existing_cols = [col[1] for col in cursor.fetchall()]

    if "file_extension" not in existing_cols:
        cursor.execute("ALTER TABLE file_events ADD COLUMN file_extension TEXT;")
    if "entropy_delta" not in existing_cols:
        cursor.execute("ALTER TABLE file_events ADD COLUMN entropy_delta REAL;")

    # High-performance B-tree indices
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_events_run_id ON file_events(run_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_events_run_timestamp ON file_events(run_id, timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_events_run_type ON file_events(run_id, event_type)")

    connection.commit()
    connection.close()


def db_writer_worker():
    """
    Dedicated background worker thread that drains the event queue
    and performs efficient batch inserts to SQLite.
    """
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")

    insert_sql = """
        INSERT INTO file_events
        (run_id, timestamp, event_type, file_path, file_size, sha256, entropy, file_extension, entropy_delta)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    batch = []
    last_commit_time = time.time()

    while not _db_stop_event.is_set() or not event_queue.empty():
        try:
            event_data = event_queue.get(timeout=0.1)
            batch.append(event_data)
            event_queue.task_done()
        except queue.Empty:
            pass

        now = time.time()
        if batch and (len(batch) >= 50 or (now - last_commit_time) >= 0.5 or _db_stop_event.is_set()):
            cursor.executemany(insert_sql, batch)
            connection.commit()
            batch.clear()
            last_commit_time = now

    if batch:
        cursor.executemany(insert_sql, batch)
        connection.commit()

    connection.close()


# --------------------------------------------------
# FILE HASH (SHA-256)
# --------------------------------------------------

def calculate_sha256(file_path):
    """
    Calculate SHA-256 hash of a file with retry handling
    for transient Windows file locking.
    """
    for _ in range(3):
        try:
            sha256 = hashlib.sha256()
            with open(file_path, "rb") as file:
                while chunk := file.read(65536):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except (PermissionError, OSError):
            time.sleep(0.01)
        except FileNotFoundError:
            return None
    return None


# --------------------------------------------------
# FILE ENTROPY (SHANNON ENTROPY)
# --------------------------------------------------

def calculate_entropy(file_path):
    """
    Calculate Shannon entropy of a file (range 0.0 to 8.0).
    Values > 7.0 strongly indicate encrypted or compressed data.
    """
    for _ in range(3):
        try:
            with open(file_path, "rb") as file:
                data = file.read()

            if not data:
                return 0.0

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
        except (PermissionError, OSError):
            time.sleep(0.01)
        except FileNotFoundError:
            return None
    return None


# --------------------------------------------------
# REAL-TIME EARLY WARNING EVALUATION
# --------------------------------------------------

def check_live_early_warning(event_type, file_path, entropy, entropy_delta):
    """
    Evaluates events in a rolling sliding window to raise early warning
    alerts in real-time before mass encryption is complete.
    """
    global _live_alert_triggered
    current_time = time.time()
    _live_events_window.append((current_time, event_type, file_path, entropy, entropy_delta))

    # Evict events older than SLIDING_WINDOW_SECONDS
    cutoff = current_time - SLIDING_WINDOW_SECONDS
    while _live_events_window and _live_events_window[0][0] < cutoff:
        _live_events_window.popleft()

    window_size = len(_live_events_window)
    if window_size < 5:
        return

    duration = max(current_time - _live_events_window[0][0], 0.1)
    rate = window_size / duration

    # Count high entropy files and suspicious renames in window
    high_entropy_count = sum(1 for e in _live_events_window if e[3] is not None and e[3] >= LIVE_ENTROPY_THRESHOLD)
    suspicious_renames = sum(
        1 for e in _live_events_window
        if e[1] == "MOVE_TO" and any(e[2].endswith(ext) for ext in SUSPICIOUS_EXTENSIONS)
    )

    # Trigger real-time alert
    if (rate >= LIVE_BURST_RATE_THRESHOLD or suspicious_renames >= 3) and (high_entropy_count >= 3 or suspicious_renames >= 3):
        if not _live_alert_triggered:
            _live_alert_triggered = True
            print("\n" + "!" * 72)
            print(" [!!!] REAL-WORLD EARLY-WARNING ALERT TRIGGERED IN REAL TIME [!!!]")
            print(f" Event Rate: {rate:.1f} ops/sec | High-Entropy Cryptographic Spikes: {high_entropy_count}")
            print(f" Suspicious Extension Churn: {suspicious_renames} files | File: {Path(file_path).name}")
            print(" Potential automated ransomware encryption loop intercepted!")
            print("!" * 72 + "\n")


# --------------------------------------------------
# RECORD EVENT
# --------------------------------------------------

def record_event(event_type, file_path):
    """
    Extract file telemetry, classify file type, compute entropy delta,
    and push event to the asynchronous writer queue.
    """
    if should_ignore_file(file_path):
        return

    timestamp = datetime.now().isoformat(timespec="milliseconds")
    file_path_str = str(file_path)
    file_ext = Path(file_path).suffix.lower()

    file_size = None
    file_hash = None
    file_entropy = None
    entropy_delta = None

    if os.path.isfile(file_path):
        try:
            file_size = os.path.getsize(file_path)
            file_hash = calculate_sha256(file_path)
            file_entropy = calculate_entropy(file_path)

            if file_entropy is not None:
                if file_path_str in _entropy_baselines:
                    entropy_delta = round(file_entropy - _entropy_baselines[file_path_str], 4)
                else:
                    _entropy_baselines[file_path_str] = file_entropy
                    entropy_delta = 0.0
        except OSError:
            pass

    # Push to background database writer
    event_queue.put((
        RUN_ID,
        timestamp,
        event_type,
        file_path_str,
        file_size,
        file_hash,
        file_entropy,
        file_ext,
        entropy_delta
    ))

    # Evaluate live early warning
    check_live_early_warning(event_type, file_path_str, file_entropy, entropy_delta)

    entropy_str = f"| H={file_entropy:.2f}" if file_entropy is not None else ""
    delta_str = f"(ΔH={entropy_delta:+.2f})" if entropy_delta and abs(entropy_delta) > 0.1 else ""
    ext_badge = f"[{file_ext or 'FILE'}]"
    print(f"[{timestamp}] {event_type:<10} {ext_badge:<8} {Path(file_path).name:<32} {entropy_str} {delta_str}")


# --------------------------------------------------
# EVENT HANDLER
# --------------------------------------------------

class FileTelemetryHandler(FileSystemEventHandler):

    def on_created(self, event):
        if not event.is_directory:
            record_event("CREATE", event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            record_event("MODIFY", event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            record_event("DELETE", event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            record_event("MOVE_FROM", event.src_path)
            record_event("MOVE_TO", event.dest_path)


# --------------------------------------------------
# MAIN COLLECTOR RUNNER
# --------------------------------------------------

def run_collector(watch_dir=None, duration=None):
    """
    Runs the collector.
    Can monitor ANY directory: custom folder, Desktop, Documents, or Sandbox.
    """
    target_dir = Path(watch_dir) if watch_dir else DEFAULT_WATCH_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    initialize_database()

    # Start background database writer thread
    writer_thread = threading.Thread(target=db_writer_worker, daemon=True)
    writer_thread.start()

    event_handler = FileTelemetryHandler()
    observer = Observer()
    observer.schedule(event_handler, str(target_dir), recursive=True)
    observer.start()

    print("=" * 70)
    print("      REAL-WORLD RANSOMWARE EARLY-WARNING TELEMETRY COLLECTOR")
    print("=" * 70)
    print(f" Monitored Target Directory : {target_dir}")
    print(f" Database Store             : {DATABASE_PATH}")
    print(f" Active Run ID              : {RUN_ID}")
    print(f" Noise Filter               : ACTIVE (ignoring temp/system files)")
    print(f" Real-Time Early Warning    : ACTIVE (Sliding Window: {SLIDING_WINDOW_SECONDS}s)")
    print("=" * 70)
    print(" Telemetry sensor active. Monitoring real filesystem operations.\n")

    start_time = time.time()
    try:
        while True:
            observer.join(1)
            if duration and (time.time() - start_time) >= duration:
                break
    except KeyboardInterrupt:
        print("\nStopping collector...")
    finally:
        observer.stop()
        observer.join()
        _db_stop_event.set()
        writer_thread.join(timeout=3.0)
        print("Collector stopped successfully. All telemetry flushed to database.")


def main():
    parser = argparse.ArgumentParser(description="Real-World Ransomware Telemetry Collector")
    parser.add_argument("--watch", type=str, help="Custom folder path to monitor (e.g. Documents or real folder)")
    parser.add_argument("--duration", type=int, help="Optional duration in seconds to monitor")
    args = parser.parse_args()

    run_collector(watch_dir=args.watch, duration=args.duration)


if __name__ == "__main__":
    main()
