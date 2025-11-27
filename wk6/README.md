## Lab 6a – Connected System with Multiple BBBW Boards

This folder contains a clean implementation of the Lab 6a deliverables for the
Connected System Design Project (EGE205). The goal is to run a Python web server
on a PC and control several BeagleBone Black Wireless (BBBW) boards that act as
web clients publishing sensor data.

### Repository layout

```
wk6/
├─ README.md               # This file – lab overview and workflow
├─ server/                 # Flask-Socket.IO server that runs on the PC
│  ├─ app.py               # Main application (UI + REST + realtime)
│  ├─ requirements.txt     # Server-only Python dependencies
│  ├─ templates/index.html # Dashboard UI
│  └─ static/dashboard.js  # Lightweight frontend logic
└─ clients/                # BBBW-side clients
   ├─ bbbw_client.py       # Configurable Socket.IO client
   ├─ requirements.txt     # BBBW Python dependencies
   ├─ README.md            # Deployment notes for each board
   └─ sensors/             # Optional sensor helpers (ADC, GPIO, simulated)
      ├─ __init__.py
      ├─ adc.py
      └─ simulated.py
```

### Quick start

1. **Server (Section 1.2)**
   - Install Python 3.9+ on the PC.
   - `cd wk6/server`
   - `python -m venv .venv && .venv\Scripts\activate`
   - `pip install -r requirements.txt`
   - `python app.py`
   - Open the printed URL (default `http://0.0.0.0:5000`) to view the dashboard.

2. **Clients (Section 1.3)**
   - Copy the `wk6/clients` folder to each BBBW (or pull the repo).
   - On every BBBW: `cd wk6/clients && ./setup.sh` *(optional helper)* or
     `pip install -r requirements.txt`.
   - Configure each board’s ID/sensor behaviour via CLI flags or environment
     variables (see `clients/README.md` for examples).
   - Run `python bbbw_client.py --server-url http://<PC_IP>:5000 --sensor pot`.

3. **Connected demo (Section 1.4)**
   - Once all boards are connected, use the dashboard to broadcast
     `start/stop/reset` commands.
   - Observe live sensor readings, connection status, and per-board logs.

### Networking tips

- Ensure all BBBWs and the PC share the same network (Wi-Fi AP or USB gadget).
- If using USB gadget mode, the PC usually exposes `192.168.7.1`; update the
  `--server-url` accordingly.
- Open TCP ports 5000 (HTTP/WebSocket) and 5001 (optional Socket.IO long polling
  fallback) on the PC’s firewall.

### Customisation hooks

- **Sensor integration:** Extend `clients/sensors/adc.py` or add new modules for
  GPIO/IC sensors, then point to them via `--sensor`.
- **Board metadata:** Each client advertises `client_id`, `board_type`,
  `sensor_type`, and `location` so the UI can group devices.
- **Automation:** Use the `/api/command` REST endpoint to drive the system from
  scripts or Node-RED flows.

### Next steps

- Tie real sensors/actuators into the provided hooks.
- Add student names/board labels in `clients/README.md`.
- Document any troubleshooting steps you encounter during integration so the
  rest of the team can benefit.

