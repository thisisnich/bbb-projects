"""
Lab 6a Server – Flask + Socket.IO dashboard for multiple BBBW boards.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from threading import Lock
from typing import Dict, Any

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, abort
from flask_socketio import SocketIO

load_dotenv()

HOST = os.getenv("SERVER_HOST", "0.0.0.0")
PORT = int(os.getenv("SERVER_PORT", "5000"))
CORS_ORIGIN = os.getenv("CORS_ALLOW", "*")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "wk6-lab-secret!")
socketio = SocketIO(app, cors_allowed_origins=CORS_ORIGIN, async_mode="eventlet")

# Shared state
_clients: Dict[str, Dict[str, Any]] = {}
_sid_to_client: Dict[str, str] = {}
_lock = Lock()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _serialise_clients() -> list[dict[str, Any]]:
    snapshot = []
    with _lock:
        for client_id, payload in _clients.items():
            entry = payload.copy()
            entry["client_id"] = client_id
            for key in ("connected_at", "last_seen"):
                if entry.get(key):
                    entry[key] = entry[key].isoformat()
            snapshot.append(entry)
    return snapshot


def _register_client(client_id: str, sid: str, meta: Dict[str, Any]) -> None:
    with _lock:
        _clients[client_id] = {
            "sid": sid,
            "board_type": meta.get("board_type", "BBBW"),
            "sensor_type": meta.get("sensor_type", "generic"),
            "location": meta.get("location", "unknown"),
            "status": "connected",
            "connected_at": _utcnow(),
            "last_seen": _utcnow(),
            "last_payload": {},
        }
        _sid_to_client[sid] = client_id


def _update_client_from_sid(sid: str, status: str = "disconnected") -> None:
    with _lock:
        client_id = _sid_to_client.get(sid)
        if not client_id:
            return
        client = _clients.get(client_id, {})
        client["status"] = status
        client["last_seen"] = _utcnow()
        if status == "disconnected":
            client.pop("sid", None)
        if status == "disconnected":
            _sid_to_client.pop(sid, None)


def _update_sensor_payload(client_id: str, payload: Dict[str, Any]) -> None:
    with _lock:
        if client_id not in _clients:
            return
        _clients[client_id]["last_payload"] = payload
        _clients[client_id]["last_seen"] = _utcnow()
        _clients[client_id]["status"] = "streaming"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/healthz")
def health():
    return {"status": "ok", "timestamp": _utcnow().isoformat()}


@app.route("/api/clients", methods=["GET"])
def api_clients():
    return jsonify({"clients": _serialise_clients()})


@app.route("/api/command", methods=["POST"])
def api_command():
    data = request.get_json(force=True, silent=True)
    if not data:
        abort(400, "Missing JSON payload")

    command = data.get("command", "").strip()
    if not command:
        abort(400, "Command is required")

    target = data.get("target", "all")
    note = data.get("note")

    payload = {
        "command": command,
        "note": note,
        "server_timestamp": _utcnow().isoformat(),
    }

    sent = 0
    if target == "all":
        socketio.emit("bbbw_command", payload, broadcast=True)
        sent = len(_clients)
    else:
        with _lock:
            client = _clients.get(target)
            sid = client.get("sid") if client else None
        if not sid:
            abort(404, f"Client '{target}' not connected")
        socketio.emit("bbbw_command", payload, to=sid)
        sent = 1
    return jsonify({"status": "ok", "sent": sent, "target": target})


@app.route("/api/reset", methods=["POST"])
def api_reset():
    with _lock:
        for client in _clients.values():
            client["status"] = "idle"
            client["last_payload"] = {}
    socketio.emit(
        "bbbw_command",
        {"command": "reset", "server_timestamp": _utcnow().isoformat()},
        broadcast=True,
    )
    return jsonify({"status": "reset"})


@socketio.on("connect")
def handle_connect():
    socketio.emit(
        "server_ack",
        {"message": "Connected to Lab 6a server", "timestamp": _utcnow().isoformat()},
        to=request.sid,
    )


@socketio.on("disconnect")
def handle_disconnect():
    _update_client_from_sid(request.sid, status="disconnected")


@socketio.on("bbbw_connect")
def handle_bbbw_connect(data):
    client_id = data.get("client_id")
    if not client_id:
        return
    _register_client(client_id, request.sid, data)
    socketio.emit(
        "bbbw_ack",
        {
            "message": f"Registered {client_id}",
            "client_id": client_id,
            "timestamp": _utcnow().isoformat(),
        },
        to=request.sid,
    )


@socketio.on("bbbw_disconnect")
def handle_bbbw_disconnect(data):
    client_id = data.get("client_id")
    if not client_id:
        return
    with _lock:
        client = _clients.get(client_id)
        if client:
            sid = client.get("sid")
            if sid:
                _sid_to_client.pop(sid, None)
            client["status"] = "disconnected"
            client["last_seen"] = _utcnow()


@socketio.on("sensor_data")
def handle_sensor_data(data):
    client_id = data.get("client_id")
    if not client_id:
        return
    _update_sensor_payload(client_id, data)


@socketio.on("heartbeat")
def handle_heartbeat(data):
    client_id = data.get("client_id")
    if not client_id:
        return
    with _lock:
        client = _clients.get(client_id)
        if client:
            client["last_seen"] = _utcnow()
            client["status"] = data.get("status", client["status"])


if __name__ == "__main__":
    print(f"Starting Lab 6a server on {HOST}:{PORT} (Ctrl+C to quit)")
    socketio.run(app, host=HOST, port=PORT)

