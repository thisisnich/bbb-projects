---
title: Module 1 — Crowd Intelligence
description: How the crowd detection module works: webcam, MIC, Motion, Proximity, and OLED display
categoryName: Modules
lastUpdated: February 2, 2026
readTime: 5
relatedArticles: ["court-availability", "court-displays"]
---

# Module 1 — Crowd Intelligence

Module 1 is the **Crowd Intelligence** unit. It gives real-time occupancy and activity level for each court using several sensors and optional AI image recognition.

## Hardware (typical setup)

- **BeagleBone Black Wireless (BBBW)**
- **USB webcam** (not counted in click board limit)
- **Click boards (e.g. 4):**
  - **MIC Click** — audio level (ball bounce, voices)
  - **Motion Click** — PIR motion
  - **OLED Click** — local status display
  - **Proximity Click** — people near court boundary

## How it works

1. **Webcam** — Counts people on court (and may use cloud AI for higher accuracy).
2. **MIC Click** — Measures noise level (e.g. dB). High noise often means active play.
3. **Motion Click** — Detects movement in the last 30 seconds.
4. **Proximity Click** — Detects people within a few metres of the court.

The BBBW **fuses** these: when count, noise, and motion agree, confidence is high and status (e.g. FULL, EMPTY) is more reliable.

## What gets sent to the server

The module sends events (e.g. `CrowdDataEvent`) with:

- `people_count`, `crowd_level` (empty/light/normal/busy/full)
- `noise_db`, `motion_detected`, `proximity_triggered`
- `confidence`
- `court_id`, `module_id`, `timestamp`

The cloud server uses this to drive the **Guest Dashboard**, **Personnel Dashboard**, and **Court Displays** (Module 5).

## OLED display (on the device)

The OLED Click can cycle through:

- Current court status and people count
- Sensor health (camera, mic, motion, proximity)
- Confidence

This helps on-site checks and debugging without opening the web dashboard.

For how this turns into “court availability” for users, see [Understanding Court Availability](/knowledge-base). For what users see on-site, see [Module 5 — Court Displays](court-displays).
