import sqlite3
from pathlib import Path
from datetime import datetime


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
# GET ALL RUNS
# --------------------------------------------------

cursor.execute("""
    SELECT DISTINCT run_id
    FROM file_events
    ORDER BY run_id
""")

runs = [row[0] for row in cursor.fetchall()]


if not runs:

    print("No telemetry data found.")

    connection.close()
    exit()


# --------------------------------------------------
# ANALYZE EACH RUN
# --------------------------------------------------

for run_id in runs:

    print()
    print("=" * 70)
    print(f"RUN: {run_id}")
    print("=" * 70)

    # ----------------------------------------------
    # TOTAL EVENTS
    # ----------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM file_events
        WHERE run_id = ?
    """, (run_id,))

    total_events = cursor.fetchone()[0]

    # ----------------------------------------------
    # UNIQUE FILES
    # ----------------------------------------------

    cursor.execute("""
        SELECT COUNT(DISTINCT file_path)
        FROM file_events
        WHERE run_id = ?
    """, (run_id,))

    unique_files = cursor.fetchone()[0]

    # ----------------------------------------------
    # EVENT COUNTS
    # ----------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM file_events
        WHERE run_id = ?
        AND event_type = 'CREATE'
    """, (run_id,))

    create_events = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM file_events
        WHERE run_id = ?
        AND event_type = 'MODIFY'
    """, (run_id,))

    modify_events = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM file_events
        WHERE run_id = ?
        AND event_type = 'DELETE'
    """, (run_id,))

    delete_events = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM file_events
        WHERE run_id = ?
        AND event_type IN ('MOVE_FROM', 'MOVE_TO')
    """, (run_id,))

    move_events = cursor.fetchone()[0]

    # ----------------------------------------------
    # EXTENSION CHURN
    # ----------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM file_events
        WHERE run_id = ?
        AND event_type = 'MOVE_TO'
        AND file_path LIKE '%.locked_test'
    """, (run_id,))

    extension_changes = cursor.fetchone()[0]

    # ----------------------------------------------
    # ENTROPY
    # ----------------------------------------------

    cursor.execute("""
        SELECT
            MIN(entropy),
            MAX(entropy),
            AVG(entropy)
        FROM file_events
        WHERE run_id = ?
        AND entropy IS NOT NULL
    """, (run_id,))

    min_entropy, max_entropy, avg_entropy = cursor.fetchone()

    # ----------------------------------------------
    # TIME RANGE
    # ----------------------------------------------

    cursor.execute("""
        SELECT
            MIN(timestamp),
            MAX(timestamp)
        FROM file_events
        WHERE run_id = ?
    """, (run_id,))

    start_time, end_time = cursor.fetchone()

    # ----------------------------------------------
    # OPERATIONS PER SECOND
    # ----------------------------------------------

    operations_per_second = 0.0

    if start_time and end_time:

        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)

        duration = (end - start).total_seconds()

        if duration > 0:
            operations_per_second = total_events / duration

    # ----------------------------------------------
    # DISPLAY RESULTS
    # ----------------------------------------------

    print()
    print("FILE ACTIVITY")
    print("-" * 70)

    print(f"Total events          : {total_events}")
    print(f"Unique files          : {unique_files}")
    print(f"Create events         : {create_events}")
    print(f"Modify events         : {modify_events}")
    print(f"Delete events         : {delete_events}")
    print(f"Move events           : {move_events}")

    print()
    print("ACTIVITY RATE")
    print("-" * 70)

    print(
        f"Operations/second    : "
        f"{operations_per_second:.2f}"
    )

    print()
    print("EXTENSION BEHAVIOR")
    print("-" * 70)

    print(
        f".locked_test changes : "
        f"{extension_changes}"
    )

    print()
    print("ENTROPY")
    print("-" * 70)

    if avg_entropy is not None:

        print(
            f"Minimum entropy      : "
            f"{min_entropy:.4f}"
        )

        print(
            f"Maximum entropy      : "
            f"{max_entropy:.4f}"
        )

        print(
            f"Average entropy      : "
            f"{avg_entropy:.4f}"
        )

    else:

        print("No entropy data available.")

    print()
    print("TIME RANGE")
    print("-" * 70)

    print(f"First event          : {start_time}")
    print(f"Last event           : {end_time}")


# --------------------------------------------------
# CLOSE DATABASE
# --------------------------------------------------

connection.close()