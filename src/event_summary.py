import sqlite3
from pathlib import Path


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "telemetry.db"


# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

connection = sqlite3.connect(DATABASE_PATH)
cursor = connection.cursor()


# --------------------------------------------------
# TOTAL EVENTS
# --------------------------------------------------

cursor.execute("""
    SELECT COUNT(*)
    FROM file_events
""")

total_events = cursor.fetchone()[0]


# --------------------------------------------------
# EVENTS BY TYPE
# --------------------------------------------------

cursor.execute("""
    SELECT event_type, COUNT(*)
    FROM file_events
    GROUP BY event_type
    ORDER BY COUNT(*) DESC
""")

event_counts = cursor.fetchall()


# --------------------------------------------------
# UNIQUE FILES
# --------------------------------------------------

cursor.execute("""
    SELECT COUNT(DISTINCT file_path)
    FROM file_events
""")

unique_files = cursor.fetchone()[0]


# --------------------------------------------------
# FILES MODIFIED
# --------------------------------------------------

cursor.execute("""
    SELECT COUNT(DISTINCT file_path)
    FROM file_events
    WHERE event_type = 'MODIFY'
""")

modified_files = cursor.fetchone()[0]


# --------------------------------------------------
# FILES CREATED
# --------------------------------------------------

cursor.execute("""
    SELECT COUNT(DISTINCT file_path)
    FROM file_events
    WHERE event_type = 'CREATE'
""")

created_files = cursor.fetchone()[0]


# --------------------------------------------------
# FILES DELETED
# --------------------------------------------------

cursor.execute("""
    SELECT COUNT(DISTINCT file_path)
    FROM file_events
    WHERE event_type = 'DELETE'
""")

deleted_files = cursor.fetchone()[0]


# --------------------------------------------------
# FILES MOVED
# --------------------------------------------------

cursor.execute("""
    SELECT COUNT(DISTINCT file_path)
    FROM file_events
    WHERE event_type IN ('MOVE_FROM', 'MOVE_TO')
""")

moved_files = cursor.fetchone()[0]


# --------------------------------------------------
# TIME RANGE
# --------------------------------------------------

cursor.execute("""
    SELECT MIN(timestamp), MAX(timestamp)
    FROM file_events
""")

start_time, end_time = cursor.fetchone()


# --------------------------------------------------
# DISPLAY SUMMARY
# --------------------------------------------------

print()
print("=" * 60)
print("        FILE BEHAVIOR TELEMETRY SUMMARY")
print("=" * 60)

print(f"Total events          : {total_events}")
print(f"Unique files observed : {unique_files}")
print(f"Files created         : {created_files}")
print(f"Files modified        : {modified_files}")
print(f"Files deleted         : {deleted_files}")
print(f"Files moved           : {moved_files}")

print()
print("EVENT BREAKDOWN")
print("-" * 60)

for event_type, count in event_counts:
    print(f"{event_type:<15}: {count}")

print()
print("MONITORING PERIOD")
print("-" * 60)

print(f"First event           : {start_time}")
print(f"Last event            : {end_time}")

print()
print("=" * 60)

connection.close()

# --------------------------------------------------
# BASIC ACTIVITY CLASSIFICATION
# --------------------------------------------------

print()
print("ACTIVITY ASSESSMENT")
print("-" * 60)

if total_events == 0:

    print("Status                : NO ACTIVITY")

elif modified_files >= 50 or moved_files >= 50:

    print("Status                : HIGH FILE ACTIVITY")
    print("Possible explanation  : Large number of file operations detected.")

elif modified_files >= 10 or moved_files >= 10:

    print("Status                : ELEVATED FILE ACTIVITY")
    print("Possible explanation  : More file activity than normal.")

else:

    print("Status                : LOW/NORMAL FILE ACTIVITY")
    print("Possible explanation  : Limited file operations detected.")