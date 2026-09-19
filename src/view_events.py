import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = BASE_DIR / "database" / "telemetry.db"


connection = sqlite3.connect(DATABASE_PATH)

cursor = connection.cursor()

cursor.execute("""
    SELECT
        id,
        timestamp,
        event_type,
        file_path,
        file_size,
        sha256
    FROM file_events
    ORDER BY id
""")

events = cursor.fetchall()

print("\nFILE TELEMETRY")
print("=" * 100)

for event in events:

    event_id, timestamp, event_type, path, size, sha256 = event

    print(f"\nID       : {event_id}")
    print(f"Time     : {timestamp}")
    print(f"Event    : {event_type}")
    print(f"File     : {path}")
    print(f"Size     : {size}")

    if sha256:
        print(f"SHA-256  : {sha256}")

print("\n" + "=" * 100)

connection.close()