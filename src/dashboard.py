import sqlite3
from pathlib import Path
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "telemetry.db"

connection = sqlite3.connect(DATABASE_PATH)
cursor = connection.cursor()

# Get latest run
cursor.execute("""
    SELECT run_id
    FROM file_events
    ORDER BY id DESC
    LIMIT 1
""")

result = cursor.fetchone()

if not result:
    print("No telemetry data found.")
    connection.close()
    exit()

latest_run = result[0]

# Event types
event_types = [
    "CREATE",
    "MODIFY",
    "DELETE",
    "MOVE_FROM",
    "MOVE_TO"
]

event_counts = {}

# Count events
for event_type in event_types:

    cursor.execute("""
        SELECT COUNT(*)
        FROM file_events
        WHERE run_id = ?
        AND event_type = ?
    """, (latest_run, event_type))

    event_counts[event_type] = cursor.fetchone()[0]

# Unique files
cursor.execute("""
    SELECT COUNT(DISTINCT file_path)
    FROM file_events
    WHERE run_id = ?
""", (latest_run,))

unique_files = cursor.fetchone()[0]

# Total events
cursor.execute("""
    SELECT COUNT(*)
    FROM file_events
    WHERE run_id = ?
""", (latest_run,))

total_events = cursor.fetchone()[0]

# Extension changes
cursor.execute("""
    SELECT COUNT(*)
    FROM file_events
    WHERE run_id = ?
    AND event_type = 'MOVE_TO'
    AND file_path LIKE '%.locked_test'
""", (latest_run,))

extension_changes = cursor.fetchone()[0]

# Average entropy
cursor.execute("""
    SELECT AVG(entropy)
    FROM file_events
    WHERE run_id = ?
    AND entropy IS NOT NULL
""", (latest_run,))

average_entropy = cursor.fetchone()[0]

# Terminal output
print()
print("=" * 60)
print("       RANSOMWARE EARLY-WARNING DASHBOARD")
print("=" * 60)

print()
print(f"Latest Run          : {latest_run}")
print(f"Total Events        : {total_events}")
print(f"Unique Files        : {unique_files}")
print(f"Extension Changes   : {extension_changes}")

if average_entropy is not None:
    print(f"Average Entropy     : {average_entropy:.4f}")
else:
    print("Average Entropy     : N/A")

print()
print("EVENT BREAKDOWN")
print("-" * 60)

for event_type, count in event_counts.items():
    print(f"{event_type:<15}: {count}")

# Create chart
labels = list(event_counts.keys())
values = list(event_counts.values())

plt.figure(figsize=(10, 6))

plt.bar(labels, values)

plt.title("File System Event Breakdown")
plt.xlabel("Event Type")
plt.ylabel("Number of Events")

plt.tight_layout()

plt.show()

connection.close()