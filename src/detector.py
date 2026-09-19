import sqlite3
from pathlib import Path
from datetime import datetime


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "telemetry.db"


# Initial experimental thresholds.
# These will be calibrated using our normal/suspicious
# experiments later.

OPERATION_RATE_THRESHOLD = 20.0
EXTENSION_CHANGE_THRESHOLD = 10
MODIFICATION_THRESHOLD = 30


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

connection = sqlite3.connect(DATABASE_PATH)
cursor = connection.cursor()


# --------------------------------------------------
# GET LATEST RUN
# --------------------------------------------------

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


# --------------------------------------------------
# TOTAL EVENTS
# --------------------------------------------------

cursor.execute("""
    SELECT COUNT(*)
    FROM file_events
    WHERE run_id = ?
""", (latest_run,))

total_events = cursor.fetchone()[0]


# --------------------------------------------------
# MODIFY EVENTS
# --------------------------------------------------

cursor.execute("""
    SELECT COUNT(*)
    FROM file_events
    WHERE run_id = ?
    AND event_type = 'MODIFY'
""", (latest_run,))

modify_events = cursor.fetchone()[0]


# --------------------------------------------------
# EXTENSION CHANGES
# --------------------------------------------------

cursor.execute("""
    SELECT COUNT(*)
    FROM file_events
    WHERE run_id = ?
    AND event_type = 'MOVE_TO'
    AND file_path LIKE '%.locked_test'
""", (latest_run,))

extension_changes = cursor.fetchone()[0]


# --------------------------------------------------
# TIME RANGE
# --------------------------------------------------

cursor.execute("""
    SELECT
        MIN(timestamp),
        MAX(timestamp)
    FROM file_events
    WHERE run_id = ?
""", (latest_run,))

start_time, end_time = cursor.fetchone()


# --------------------------------------------------
# OPERATIONS PER SECOND
# --------------------------------------------------

operations_per_second = 0.0

if start_time and end_time:

    start = datetime.fromisoformat(start_time)
    end = datetime.fromisoformat(end_time)

    duration = (end - start).total_seconds()

    if duration > 0:
        operations_per_second = total_events / duration


# --------------------------------------------------
# ENTROPY
# --------------------------------------------------

cursor.execute("""
    SELECT AVG(entropy)
    FROM file_events
    WHERE run_id = ?
    AND entropy IS NOT NULL
""", (latest_run,))

average_entropy = cursor.fetchone()[0]


# --------------------------------------------------
# SIGNAL SCORES
# --------------------------------------------------

# Signal 1: Operation burst

if operations_per_second >= OPERATION_RATE_THRESHOLD:

    burst_score = 40

elif operations_per_second >= OPERATION_RATE_THRESHOLD / 2:

    burst_score = 20

else:

    burst_score = 0


# Signal 2: Modification burst

if modify_events >= MODIFICATION_THRESHOLD:

    modification_score = 25

elif modify_events >= MODIFICATION_THRESHOLD / 2:

    modification_score = 12

else:

    modification_score = 0


# Signal 3: Extension churn

if extension_changes >= EXTENSION_CHANGE_THRESHOLD:

    extension_score = 25

elif extension_changes > 0:

    extension_score = 10

else:

    extension_score = 0


# Signal 4: Entropy

# This is intentionally weak for now because
# entropy alone cannot identify ransomware.

if average_entropy is not None and average_entropy >= 7.0:

    entropy_score = 10

else:

    entropy_score = 0


# --------------------------------------------------
# TOTAL RISK SCORE
# --------------------------------------------------

risk_score = (
    burst_score
    + modification_score
    + extension_score
    + entropy_score
)


risk_score = min(risk_score, 100)


# --------------------------------------------------
# ALERT LEVEL
# --------------------------------------------------

if risk_score >= 70:

    alert_level = "HIGH"

elif risk_score >= 40:

    alert_level = "MEDIUM"

elif risk_score >= 20:

    alert_level = "LOW"

else:

    alert_level = "NORMAL"


# --------------------------------------------------
# DISPLAY RESULT
# --------------------------------------------------

print()
print("=" * 65)
print("          RANSOMWARE EARLY-WARNING DETECTOR")
print("=" * 65)

print()
print(f"Analyzed run        : {latest_run}")

print()
print("BEHAVIORAL FEATURES")
print("-" * 65)

print(
    f"Operations/second  : "
    f"{operations_per_second:.2f}"
)

print(
    f"Modify events      : "
    f"{modify_events}"
)

print(
    f"Extension changes  : "
    f"{extension_changes}"
)

if average_entropy is not None:

    print(
        f"Average entropy    : "
        f"{average_entropy:.4f}"
    )

else:

    print(
        "Average entropy    : "
        "N/A"
    )


print()
print("SIGNAL SCORES")
print("-" * 65)

print(f"Operation burst    : {burst_score}/40")
print(f"Modification burst : {modification_score}/25")
print(f"Extension churn    : {extension_score}/25")
print(f"Entropy signal     : {entropy_score}/10")


print()
print("=" * 65)

print(
    f"RISK SCORE         : "
    f"{risk_score}/100"
)

print(
    f"ALERT LEVEL        : "
    f"{alert_level}"
)

print("=" * 65)


# --------------------------------------------------
# EXPLANATION
# --------------------------------------------------

print()
print("EXPLANATION")
print("-" * 65)

if burst_score > 0:

    print(
        "[+] Rapid file operations detected."
    )

if modification_score > 0:

    print(
        "[+] Large number of file modifications detected."
    )

if extension_score > 0:

    print(
        "[+] Unusual test-extension changes detected."
    )

if entropy_score > 0:

    print(
        "[+] High average file entropy detected."
    )

if risk_score < 20:

    print(
        "[+] No significant suspicious behavior detected."
    )

print()


connection.close()