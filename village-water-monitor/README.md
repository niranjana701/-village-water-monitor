# Village Water Point Uptime Monitoring

**SIH 2026 Internal Practical Assessment — Niranjana Devi M (411723106060), PSVPEC ECE**

## Problem (2 lines)

Handpumps and taps stop working and stay unrepaired for weeks because breakdowns are only reported when someone walks to the panchayat office to complain. This project automatically detects whether a water point is working and shows the panchayat which points are down and for how long, so repairs can be prioritised without waiting for a complaint.

## Technology Stack

- **Python 3** — dataset generation, the question-answering assistant, and integration testing
- **ESP32 (simulated in Wokwi)** — the sensing node, written in C++/Arduino
- No external libraries required for the Python side (standard library only: `csv`, `re`, `string`, `datetime`, `collections`)

## Project Structure