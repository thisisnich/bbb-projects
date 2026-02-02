---
title: Module 5 — Court Displays
description: On-site screens that show real-time court status to users at the facility
categoryName: Modules
lastUpdated: February 2, 2026
readTime: 3
relatedArticles: ["crowd-intelligence", "check-court-status"]
---

# Module 5 — Court Displays

**Module 5** is the **Court Display** — the on-site screen (or screens) at each court that shows real-time status so people can see availability without opening the web dashboard.

## What they show

- **Court name** (e.g. Court A, Basketball A)
- **Status:** Empty / Light / Normal / Busy / Full
- **People count** (e.g. “8 people”)
- **Confidence** (optional, e.g. “95%”)
- Sometimes **environment** (e.g. temperature, “Playable” yes/no)

Content is driven by the same cloud data as the Guest and Personnel dashboards (from Module 1 and Module 2).

## Where they get data

- The display device (e.g. BBBW or small PC) connects to the same server as the web dashboards.
- It receives live crowd (and optionally environment) updates over the network (e.g. WebSocket / Socket.IO).
- When Module 1 (Crowd) or Module 2 (Environment) sends new data, the server pushes it to connected clients, including the court display.

## For facility managers

- **Placement:** Mount where users can see it before walking onto the court.
- **Refresh:** Data updates in real time; no need to tap or refresh.
- **Offline:** If the display loses connection, it may show “No data” or last known status until the link is restored.

For how crowd status is produced, see [Module 1 — Crowd Intelligence](crowd-intelligence). For checking before you visit, see [Check Court Status Before You Visit](/knowledge-base).
