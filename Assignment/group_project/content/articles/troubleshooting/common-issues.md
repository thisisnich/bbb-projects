---
title: Common Issues and Troubleshooting
description: Fix login problems, missing data, and display issues on the Smart Sports system
categoryName: Troubleshooting
lastUpdated: February 2, 2026
readTime: 4
relatedArticles: []
---

# Common Issues and Troubleshooting

Quick fixes for the most common problems with the Smart Sports web dashboard and court displays.

## Login

- **Wrong password:** Double-check username and password. Use “Forgot password” if available; otherwise contact your admin for a reset.
- **Can’t reach login page:** Confirm the URL and that you’re on the correct network. Try in a private/incognito window in case of cache or cookie issues.
- **Redirect loop or blank page:** Clear cookies for the site or try another browser. If it persists, report to your admin (could be server/session config).

See the [Login](/knowledge-base) FAQ for more.

## Dashboard data not updating

- **Stuck numbers or old status:** The dashboard updates over a live connection (e.g. WebSocket). Refresh the page once. If it keeps happening, the server or module might be down.
- **“No data” or empty courts:** Modules might be offline or not yet connected. Personnel can check the activity log for “module connected” and “data received” for each court.
- **Wrong court:** Make sure you’re looking at the correct court; some dashboards let you switch court or location.

## Court display (Module 5) not updating

- **Screen frozen or old status:** Check network connection of the display device (e.g. BBBW). Restart the display app or device if needed.
- **Wrong court on display:** Verify the display is configured with the correct `court_id` or device ID so it receives the right feed.

## Module not sending data

- **On the BBBW / device:** Confirm the client script is running and the server URL (and port) are correct. Check the activity log on the server for that module’s connection and last event.
- **Network:** Ensure the device and server are on the same network (or that firewall/port rules allow the connection). Ping or open the server URL from the device if possible.

## Environment or crowd looks wrong

- **Sensor issue:** A single bad sensor can skew results. Personnel can compare with other courts or the activity log. Facility may need to recalibrate or replace the sensor.
- **Delay:** There can be a short delay (a few seconds) between real-world change and the dashboard update.

For more on logs and alerts, see [Alerts and Logs on the Personnel Dashboard](/knowledge-base). For login-specific help, see the Login FAQ.
