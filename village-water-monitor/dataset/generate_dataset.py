"""
generate_dataset.py
--------------------
Generates a realistic dataset of village water point usage readings
for the SIH 2026 "Village Water Point Uptime Monitoring" project.

Fields:
    reading_id     - unique integer ID, auto-incrementing
    waterpoint_id  - which physical water point (WP001-WP010)
    habitation     - which village/hamlet the water point belongs to
    flow_ok        - 1 (flow detected), 0 (no flow), '' (missing/sensor error)
    usage_count    - number of times water was drawn in this reading window
    recorded_at    - timestamp of the reading (15 min apart per water point)
    status_label   - ground truth outcome: 'working' or 'down'

Deliberate awkward cases (as required by the assessment):
    1. One row with flow_ok MISSING
    2. One row with usage_count far outside the plausible range (spike/faulty sensor)
    3. A STUCK reading - several consecutive identical usage_count values
       from the same water point (sensor stuck, not a real pattern)
"""

import csv
import random
from datetime import datetime, timedelta

random.seed(42)  # reproducible output

HABITATIONS = {
    "WP001": "Kollampalayam", "WP002": "Kollampalayam",
    "WP003": "Sundapatti",    "WP004": "Sundapatti",
    "WP005": "Sundapatti",
    "WP006": "Marudur",       "WP007": "Marudur",
    "WP008": "Marudur",
    "WP009": "Perumbakkam",   "WP010": "Perumbakkam",
}

WATERPOINTS = list(HABITATIONS.keys())
READINGS_PER_WP = 10          # 10 waterpoints x 10 readings = 100 rows
INTERVAL_MINUTES = 15
START_TIME = datetime(2026, 7, 20, 6, 0, 0)  # 6:00 AM start

rows = []
reading_id = 1

for wp in WATERPOINTS:
    behaviour = random.choices(
        ["healthy", "down", "flaky"], weights=[0.5, 0.3, 0.2], k=1
    )[0]

    current_time = START_TIME

    for i in range(READINGS_PER_WP):
        flow_ok = 1
        usage_count = 0
        status_label = "working"

        if behaviour == "healthy":
            flow_ok = 1
            usage_count = random.randint(3, 20)
            status_label = "working"
        elif behaviour == "down":
            flow_ok = 0
            usage_count = 0
            status_label = "down"
        else:  # flaky
            flow_ok = random.choice([0, 1])
            usage_count = random.randint(0, 12) if flow_ok else 0
            status_label = "working" if flow_ok else "down"

        rows.append({
            "reading_id": reading_id,
            "waterpoint_id": wp,
            "habitation": HABITATIONS[wp],
            "flow_ok": flow_ok,
            "usage_count": usage_count,
            "recorded_at": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "status_label": status_label,
        })

        reading_id += 1
        current_time += timedelta(minutes=INTERVAL_MINUTES)

# ---- Inject the 3 deliberate awkward cases ----

missing_row = random.choice(rows)
missing_row["flow_ok"] = ""

spike_row = random.choice(rows)
while spike_row is missing_row:
    spike_row = random.choice(rows)
spike_row["usage_count"] = 500
spike_row["flow_ok"] = 1

stuck_wp = "WP004"
stuck_rows = [r for r in rows if r["waterpoint_id"] == stuck_wp][-4:]
for r in stuck_rows:
    r["flow_ok"] = 1
    r["usage_count"] = 7
    r["status_label"] = "working"

# ---- Write to CSV (saves in the SAME folder as this script) ----
output_path = "waterpoint_readings.csv"
fieldnames = ["reading_id", "waterpoint_id", "habitation", "flow_ok",
              "usage_count", "recorded_at", "status_label"]

with open(output_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} rows -> {output_path}")
print(f"Missing flow_ok injected at reading_id={missing_row['reading_id']}")
print(f"Spike usage_count injected at reading_id={spike_row['reading_id']}")
print(f"Stuck readings injected at waterpoint={stuck_wp}, "
      f"reading_ids={[r['reading_id'] for r in stuck_rows]}")