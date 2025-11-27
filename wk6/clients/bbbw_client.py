"""
Configurable BBBW client for Lab 6a.
"""
from __future__ import annotations

import os
import sys
import time
import uuid
from datetime import datetime
from threading import Event, Thread
from typing import Dict, Any

import click
import socketio

from sensors import build_sensor, list_sensors


def env_default(key: str, fallback: str | None = None) -> str | None:
    return os.getenv(f"WK6_{key.upper()}", fallback)


class BBBWClient:
    def __init__(
        self,
        server_url: str,
        client_id: str,
        board_type: str,
        location: str,
        sensor_type: str,
        sensor_options: Dict[str, Any],
        sampling_interval: float,
        debug: bool = False,
    ):
        self.server_url = server_url
        self.client_id = client_id
        self.board_type = board_type
        self.location = location
        self.sensor_type = sensor_type
        self.sampling_interval = sampling_interval
        self.debug = debug

        self.sensor = build_sensor(sensor_type, **sensor_options)
        self.sio = socketio.Client(reconnection=True, logger=debug, engineio_logger=debug)
        self.reading = Event()
        self.shutdown = Event()

        self.sio.on("connect", self._on_connect)
        self.sio.on("disconnect", self._on_disconnect)
        self.sio.on("bbbw_ack", self._on_ack)
        self.sio.on("bbbw_command", self._on_command)

    # Socket.IO callbacks
    def _on_connect(self):
        click.echo(f"[{self.client_id}] Connected to {self.server_url}")
        self.sio.emit(
            "bbbw_connect",
            {
                "client_id": self.client_id,
                "board_type": self.board_type,
                "sensor_type": self.sensor_type,
                "location": self.location,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    def _on_disconnect(self):
        click.echo(f"[{self.client_id}] Disconnected")
        self.reading.clear()

    def _on_ack(self, data):
        click.echo(f"[{self.client_id}] Server ACK: {data.get('message')}")

    def _on_command(self, data):
        command = (data.get("command") or "").lower()
        click.echo(f"[{self.client_id}] Command received: {command}")
        if command == "start":
            self.reading.set()
        elif command == "stop":
            self.reading.clear()
        elif command == "reset":
            self.reading.clear()
        else:
            click.echo(f"[{self.client_id}] Unknown command '{command}'")

    # Streaming loop
    def _sensor_loop(self):
        while not self.shutdown.is_set():
            if self.reading.is_set():
                try:
                    payload = self.sensor.read()
                    payload.update(
                        {
                            "client_id": self.client_id,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
                    if self.debug:
                        click.echo(f"[{self.client_id}] Data -> {payload}")
                    self.sio.emit("sensor_data", payload)
                except Exception as exc:  # noqa: BLE001 - keep running even on sensor failure
                    click.echo(f"[{self.client_id}] Sensor error: {exc}", err=True)
                time.sleep(self.sampling_interval)
            else:
                time.sleep(0.2)

    def run(self):
        thread = Thread(target=self._sensor_loop, daemon=True)
        thread.start()

        while not self.shutdown.is_set():
            try:
                if not self.sio.connected:
                    click.echo(f"[{self.client_id}] Connecting to {self.server_url} ...")
                    self.sio.connect(self.server_url, wait=True)
                time.sleep(1)
            except KeyboardInterrupt:
                break
            except socketio.exceptions.ConnectionError as exc:
                click.echo(f"[{self.client_id}] Connection error: {exc}", err=True)
                time.sleep(3)

        self.shutdown.set()
        self.reading.clear()
        if self.sio.connected:
            self.sio.emit(
                "bbbw_disconnect",
                {"client_id": self.client_id, "timestamp": datetime.utcnow().isoformat()},
            )
            self.sio.disconnect()
        click.echo(f"[{self.client_id}] Client shut down.")


def parse_sensor_options(options: tuple[str, ...]) -> Dict[str, Any]:
    parsed: Dict[str, Any] = {}
    for option in options:
        if "=" not in option:
            raise click.BadParameter("Use key=value format for sensor options.")
        key, value = option.split("=", 1)
        parsed[key] = _coerce(value)
    return parsed


def _coerce(value: str) -> Any:
    for cast in (int, float):
        try:
            return cast(value)
        except ValueError:
            continue
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    return value


@click.command()
@click.option(
    "--server-url",
    default=lambda: env_default("SERVER_URL", "http://192.168.7.1:5000"),
    show_default=True,
    help="Lab 6a server URL.",
)
@click.option(
    "--client-id",
    default=lambda: env_default("CLIENT_ID", f"bbbw-{uuid.uuid4().hex[:6]}"),
    show_default=True,
    help="Unique identifier for this BBBW.",
)
@click.option(
    "--board-type",
    default=lambda: env_default("BOARD_TYPE", "BBBW"),
    show_default=True,
)
@click.option(
    "--location",
    default=lambda: env_default("LOCATION", "lab-bench"),
    show_default=True,
)
@click.option(
    "--sensor",
    "sensor_type",
    default=lambda: env_default("SENSOR", "simulated"),
    type=click.Choice(list_sensors()),
    show_default=True,
    help="Sensor reader to use.",
)
@click.option(
    "--sensor-option",
    "-o",
    multiple=True,
    help="Custom sensor option in key=value form (repeatable).",
)
@click.option(
    "--sampling-interval",
    default=lambda: float(env_default("SAMPLING_INTERVAL", "1.0")),
    show_default=True,
    help="Seconds between sensor readings.",
)
@click.option("--debug", is_flag=True, help="Enable verbose logging.")
def main(
    server_url: str,
    client_id: str,
    board_type: str,
    location: str,
    sensor_type: str,
    sensor_option: tuple[str, ...],
    sampling_interval: float,
    debug: bool,
):
    """Run the BBBW client."""
    try:
        options = parse_sensor_options(sensor_option)
    except click.BadParameter as exc:
        raise SystemExit(str(exc)) from exc

    click.echo("=" * 60)
    click.echo("EGE205 Lab 6a – BBBW Client")
    click.echo("=" * 60)
    click.echo(f"Client ID        : {client_id}")
    click.echo(f"Server URL       : {server_url}")
    click.echo(f"Sensor           : {sensor_type}")
    click.echo(f"Sampling Interval: {sampling_interval}s")
    click.echo("=" * 60)

    client = BBBWClient(
        server_url=server_url,
        client_id=client_id,
        board_type=board_type,
        location=location,
        sensor_type=sensor_type,
        sensor_options=options,
        sampling_interval=sampling_interval,
        debug=debug,
    )
    client.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)

