"""
assistant.py
------------
The "assistant" for the Village Water Point Uptime Monitoring project.

Supports 5 real questions (Task 2):
    1. Is waterpoint X working?
    2. How long has waterpoint X been down?
    3. Which waterpoints are currently down?
    4. How many times was water drawn at waterpoint X? (usage count)
    5. Which habitation has the most down waterpoints right now?

Matching approach: normalize input (trim, lowercase, strip punctuation),
then match against keyword patterns for each intent. No ML - simple and
explainable, appropriate for an Easy-level assessment.

NOTE: Task 3 (privacy/refusal) builds directly on top of this file -
see assistant_with_auth.py.
"""

import csv
import re
import string
from datetime import datetime
from collections import defaultdict

DATA_PATH = "../dataset/waterpoint_readings.csv"
READING_INTERVAL_MINUTES = 15  # must match generate_dataset.py


# ---------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------

def load_data(path=DATA_PATH):
    """Load CSV into a list of dicts with proper types. Handles the
    'missing value' and other awkward cases gracefully."""
    rows = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "reading_id": int(r["reading_id"]),
                "waterpoint_id": r["waterpoint_id"],
                "habitation": r["habitation"],
                "flow_ok": int(r["flow_ok"]) if r["flow_ok"] != "" else None,
                "usage_count": int(r["usage_count"]),
                "recorded_at": datetime.strptime(r["recorded_at"], "%Y-%m-%d %H:%M:%S"),
                "status_label": r["status_label"],
            })
    return rows


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def normalize_input(text):
    """Trim, lowercase, strip punctuation - required by Task 2."""
    text = text.strip().lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return text


def extract_waterpoint_id(text):
    """Pull a waterpoint id like 'wp003' or 'wp3' out of free text."""
    match = re.search(r"wp\s*0*(\d+)", text)
    if not match:
        return None
    num = int(match.group(1))
    return f"WP{num:03d}"


def latest_reading(data, waterpoint_id):
    """Most recent reading for a given waterpoint."""
    readings = [r for r in data if r["waterpoint_id"] == waterpoint_id]
    if not readings:
        return None
    return max(readings, key=lambda r: r["recorded_at"])


def all_waterpoint_ids(data):
    return sorted(set(r["waterpoint_id"] for r in data))


# ---------------------------------------------------------------------
# Intent 1: Is waterpoint X working?
# ---------------------------------------------------------------------

def intent_is_working(data, waterpoint_id):
    reading = latest_reading(data, waterpoint_id)
    if reading is None:
        return f"I have no records for {waterpoint_id}."
    if reading["status_label"] == "working":
        return f"{waterpoint_id} ({reading['habitation']}) is currently WORKING (last checked {reading['recorded_at']})."
    return f"{waterpoint_id} ({reading['habitation']}) is currently DOWN (last checked {reading['recorded_at']})."


# ---------------------------------------------------------------------
# Intent 2: How long has waterpoint X been down?
# ---------------------------------------------------------------------

def intent_downtime_duration(data, waterpoint_id):
    readings = sorted(
        [r for r in data if r["waterpoint_id"] == waterpoint_id],
        key=lambda r: r["recorded_at"],
        reverse=True,  # most recent first
    )
    if not readings:
        return f"I have no records for {waterpoint_id}."

    if readings[0]["status_label"] != "down":
        return f"{waterpoint_id} is currently working, so it is not down."

    # Walk backward through consecutive 'down' readings
    down_streak = []
    for r in readings:
        if r["status_label"] == "down":
            down_streak.append(r)
        else:
            break

    earliest_down = down_streak[-1]["recorded_at"]
    latest_down = down_streak[0]["recorded_at"]
    duration = latest_down - earliest_down
    minutes = int(duration.total_seconds() // 60) + READING_INTERVAL_MINUTES

    return (f"{waterpoint_id} has been down for at least {minutes} minutes "
            f"(since approximately {earliest_down}), based on {len(down_streak)} consecutive down readings.")


# ---------------------------------------------------------------------
# Intent 3: Which waterpoints are currently down?
# ---------------------------------------------------------------------

def intent_list_down(data):
    down_points = []
    for wp in all_waterpoint_ids(data):
        reading = latest_reading(data, wp)
        if reading and reading["status_label"] == "down":
            down_points.append(f"{wp} ({reading['habitation']})")

    if not down_points:
        return "No waterpoints are currently down."
    return "Currently down: " + ", ".join(down_points)


# ---------------------------------------------------------------------
# Intent 4: How many times was water drawn at waterpoint X?
# ---------------------------------------------------------------------

def intent_usage_count(data, waterpoint_id):
    readings = [r for r in data if r["waterpoint_id"] == waterpoint_id]
    if not readings:
        return f"I have no records for {waterpoint_id}."
    total = sum(r["usage_count"] for r in readings)
    return f"{waterpoint_id} recorded {total} total water draws across {len(readings)} readings."


# ---------------------------------------------------------------------
# Intent 5: Which habitation has the most down waterpoints right now?
# ---------------------------------------------------------------------

def intent_habitation_most_down(data):
    down_counts = defaultdict(int)
    for wp in all_waterpoint_ids(data):
        reading = latest_reading(data, wp)
        if reading and reading["status_label"] == "down":
            down_counts[reading["habitation"]] += 1

    if not down_counts:
        return "No habitation currently has any down waterpoints."

    top_habitation = max(down_counts, key=down_counts.get)
    count = down_counts[top_habitation]
    return f"{top_habitation} currently has the most down waterpoints: {count}."


# ---------------------------------------------------------------------
# Intent matching
# ---------------------------------------------------------------------

SUPPORTED_QUESTIONS = [
    "Is waterpoint <id> working? (e.g. 'is wp003 working')",
    "How long has waterpoint <id> been down? (e.g. 'how long has wp004 been down')",
    "Which waterpoints are currently down? (e.g. 'list down waterpoints')",
    "How many times was water drawn at waterpoint <id>? (e.g. 'usage count for wp002')",
    "Which habitation has the most down waterpoints? (e.g. 'which habitation has most down points')",
]


def match_intent(raw_text, data):
    text = normalize_input(raw_text)
    wp_id = extract_waterpoint_id(text)

    if wp_id and any(k in text for k in ["working", "status", "is up", "is it down"]):
        return intent_is_working(data, wp_id)

    if wp_id and any(k in text for k in ["how long", "down for", "since when"]):
        return intent_downtime_duration(data, wp_id)

    if any(k in text for k in ["which waterpoints are down", "list down", "currently down", "all down"]):
        return intent_list_down(data)

    if wp_id and any(k in text for k in ["usage", "how many times", "draw", "drawn"]):
        return intent_usage_count(data, wp_id)

    if any(k in text for k in ["which habitation", "most down", "habitation with"]):
        return intent_habitation_most_down(data)

    listing = "\n  - ".join(SUPPORTED_QUESTIONS)
    return ("I'm not confident I understood that question. Here is what I can answer:\n  - " + listing)


# ---------------------------------------------------------------------
# Simple manual test when run directly
# ---------------------------------------------------------------------

if __name__ == "__main__":
    data = load_data()
    test_queries = [
        "Is WP003 working?",
        "How long has wp004 been down",
        "Which waterpoints are currently down",
        "Usage count for wp002",
        "Which habitation has the most down waterpoints",
        "What is the weather today",  # should trigger refusal
    ]
    for q in test_queries:
        print(f"Q: {q}")
        print(f"A: {match_intent(q, data)}\n")