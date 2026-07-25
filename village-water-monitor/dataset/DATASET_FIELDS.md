# Dataset Field Documentation — waterpoint_readings.csv

| Field | Meaning | Type / Possible Values |
|---|---|---|
| `reading_id` | Unique ID for this sensor reading | Integer, auto-incrementing |
| `waterpoint_id` | Which physical water point produced this reading | String, `WP001`–`WP010` |
| `habitation` | Village/hamlet the water point belongs to | String: `Kollampalayam`, `Sundapatti`, `Marudur`, `Perumbakkam` |
| `flow_ok` | Did the sensor detect valid water flow during this reading window? | `1` = flow detected, `0` = no flow, *(blank)* = sensor error / missing reading |
| `usage_count` | Number of times water was drawn during this reading window | Integer, normally `0`–`20`. One row deliberately has `500` to simulate a faulty/spiked sensor reading |
| `recorded_at` | Timestamp of the reading | `YYYY-MM-DD HH:MM:SS`, readings taken every 15 minutes per water point |
| `status_label` | Ground-truth outcome for this reading — used to check calculated figures and as the "history to learn from" required by the assessment | `working` or `down` |

## Deliberate awkward cases (required by the assessment)

1. **Missing value** — one row has a blank `flow_ok` (sensor didn't report). The assistant/dashboard must decide what to show when a value can't be calculated, rather than crashing or guessing.
2. **Out-of-range value** — one row has `usage_count=500`, far outside the plausible 0–20 range. This tests the plausibility check in Task 4.
3. **Stuck reading** — `WP004`'s last 4 readings repeat the identical `usage_count=7`. A real water point's usage naturally varies reading to reading; an identical repeated value signals a jammed/stuck sensor rather than genuine unchanged usage. This tests the smoothing logic in Task 4.

## How "down" is defined

A water point is considered **down** when `flow_ok = 0` persists across a stretch of consecutive readings, not just a single bad reading. This is the definition the dashboard/assistant uses to answer "how long has X been down?"

## Simulator note

The Task 4 ESP32 simulator (Wokwi) produces readings with this exact same shape and field names (`waterpoint_id`, `flow_ok`, `usage_count`, `recorded_at`) so the sensing node and the dashboard/assistant are reading from a consistent format.