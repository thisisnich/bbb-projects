## Lab 6a Server (Section 1.2)

This Flask-Socket.IO app runs on the PC and provides:

- A Bootstrap-based dashboard (`/`) with live client status.
- REST helpers for automation (`/api/clients`, `/api/command`, `/api/reset`).
- Socket.IO messaging to/from BBBW clients.

### Setup

```powershell
cd wk6\server
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Environment variables (optional):

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `SERVER_HOST` | `0.0.0.0` | Bind interface |
| `SERVER_PORT` | `5000` | HTTP/Socket.IO port |
| `SECRET_KEY` | `wk6-lab-secret!` | Flask secret |
| `CORS_ALLOW` | `*` | Allowed origins for Socket.IO |

### REST summary

- `GET /api/clients` – JSON snapshot of all registered boards.
- `POST /api/command` – Body: `{ "command": "start", "target": "all" }`.
  Use a specific `client_id` in `target` to control just that board.
- `POST /api/reset` – Resets server-side state and broadcasts `reset`.

### Files

- `app.py` – main Flask app and Socket.IO handlers.
- `templates/index.html` – dashboard layout (Bootstrap 5).
- `static/dashboard.js` – fetch + table rendering logic.

### Testing tips

1. Start the server and watch the console for registration logs.
2. Run multiple instances of `clients/bbbw_client.py` (simulated sensors) from
   the PC to emulate BBBWs before deploying to the real boards.
3. Use browser dev tools → Network tab to verify `/api/clients` polling and the
   POST payloads whenever you press the control buttons.

