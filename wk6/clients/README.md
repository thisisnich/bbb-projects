## BBBW Client Scripts (Section 1.3)

Each BeagleBone Black Wireless board runs a lightweight Socket.IO client that
talks to the Lab 6a server. Every teammate should configure one BBBW with a
unique `client_id` and (optionally) a dedicated sensor.

### 1. Prepare the BBBW

```bash
cd ~/cloud9/wk6/clients
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> If `Adafruit_BBIO` is not required for your sensor, you can remove it from the
> `requirements.txt` to reduce install time.

### 2. Choose a sensor profile

The default `simulated` sensor returns random values – great for dry runs.
Additional helpers live in `sensors/`:

| Sensor | Flag | Description |
| ------ | ---- | ----------- |
| `simulated` | `--sensor simulated` | Random value (software-only) |
| `adc` | `--sensor adc --adc-channel 2` | Reads `/sys/bus/iio/devices/iio:device0/in_voltage{N}_raw` |

You can add more readers (e.g., GPIO buttons, I²C sensors) by creating new files
inside `sensors/` and wiring them inside `sensors/__init__.py`.

### 3. Run the client

```bash
python bbbw_client.py \
  --server-url http://192.168.7.1:5000 \
  --client-id bbbw-teamA \
  --sensor adc \
  -o adc_channel=2 \
  --location "Lab Bench 1"
```

Important flags:

- `--server-url`: IP/hostname of the PC server.
- `--client-id`: Must be unique (stick to lowercase, digits, and dashes).
- `--sensor`: `simulated`, `adc`, or your custom reader.
- `--location`: Appears on the dashboard to identify the board.
- `--sampling-interval`: Seconds between readings (default `1.0`).

Environment variables offer the same controls (prefix them with `WK6_`, e.g.
`export WK6_SERVER_URL=http://192.168.7.1:5000`).

### 4. Map boards to teammates

| Teammate | BBBW Hostname | Client ID | Sensor | Notes |
| -------- | ------------- | --------- | ------ | ----- |
| _(fill me)_ |  |  |  |  |
| _(fill me)_ |  |  |  |  |
| _(fill me)_ |  |  |  |  |
| _(fill me)_ |  |  |  |  |

Keep this table updated so the instructor can verify who implemented which board.

### Optional: USR0 LED demo client

`usr0_led_client.py` matches the sample logic from the lab sheet:

```bash
python usr0_led_client.py
```

Environment variables let you tweak behaviour without editing code:

| Variable | Default | Description |
| --- | --- | --- |
| `USR0_SERVER_URL` | `http://192.168.7.1:5000` | Socket.IO server URL |
| `USR0_CONTROL_EVENT` | `ControlUSR0Led` | Event name that toggles the LED |
| `USR0_DATA_EVENT` | `BBBW3Event` | Event name for outgoing math strings |
| `USR0_LED_PIN` | `USR0` | LED GPIO pin |

Any server that emits `ControlUSR0Led` events with payload `"on"` or `"off"` will
drive the onboard LED, while the script keeps publishing random math results.

### 5. Troubleshooting

- Use `ping <server_ip>` from the BBBW to verify connectivity.
- If you see `ConnectionError`, confirm the server is reachable and that the
  firewall allows ports 5000/5001.
- Add `--debug` to the client command to print verbose logs and sensor values.

Once every BBBW connects, the Lab 6a dashboard (Section 1.4) will display live
sensor streams and let you broadcast `start/stop/reset` commands.

