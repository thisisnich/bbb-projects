---
title: Understanding Court Availability
description: How court status (empty, light, busy, full) is determined and what it means for your visit
categoryName: Getting Started
lastUpdated: February 2, 2026
readTime: 3
relatedArticles: ["welcome", "crowd-intelligence", "check-court-status"]
---

# Understanding Court Availability

Court availability is shown as **crowd level**: Empty, Light, Normal, Busy, or Full. The system combines multiple sensors to give you a reliable status before you go.

## How status is determined

The Crowd Intelligence module (Module 1) uses:

- **People count** from the camera
- **Noise level** (e.g. ball bouncing, voices) from the MIC Click
- **Motion** from the PIR Motion Click
- **Proximity** from the Proximity Click near the court

When these agree (e.g. high count + high noise + motion), the system reports a **confidence score**. Higher confidence means the status is more reliable.

## What each level means

| Level   | Meaning                    | Typical use                          |
|---------|----------------------------|--------------------------------------|
| Empty   | No one on court            | Good time to go                      |
| Light   | Few people                 | Likely space to play                 |
| Normal  | Moderate use               | May need to wait or share            |
| Busy    | Heavy use                  | Expect waiting or a full court       |
| Full    | Court at capacity          | Consider another time or court      |

## Where you see it

- **Guest Dashboard:** Live crowd level and people count per court
- **Court displays (Module 5):** On-site screens at each court
- **Map page:** Court locations and status at a glance

Check [Module 1 Crowd Intelligence](crowd-intelligence) for technical details, or [Check Court Status Before You Visit](check-court-status) for using the guest view.
