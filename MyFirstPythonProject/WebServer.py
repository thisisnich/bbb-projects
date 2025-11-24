from flask import Flask
from flask import render_template, jsonify, request, Response
import Adafruit_BBIO.GPIO as GPIO
import importlib.util
import threading
import time
import sys
import os
import csv
from collections import deque
from datetime import datetime, timedelta

# Import 8x8 module (handles module name starting with number)
spec = importlib.util.spec_from_file_location("ledmatrix8x8", os.path.join(os.path.dirname(__file__), "8x8.py"))
ledmatrix_module = importlib.util.module_from_spec(spec)
sys.modules["ledmatrix8x8"] = ledmatrix_module
spec.loader.exec_module(ledmatrix_module)
LedMatrix8x8 = ledmatrix_module.LedMatrix8x8

# Import OLED helper (optional)
try:
    from oled import OledDisplay
except Exception as oled_exc:  # pragma: no cover
    OledDisplay = None  # type: ignore
    print(f"[WARN] OLED import failed: {oled_exc}")

# Import webcam module (optional)
try:
    from webcam_module import WebcamCapture
    webcam = WebcamCapture(device_index=0, width=640, height=480, fps=15, lazy_hw=True)
    print("[WEBCAM] Webcam module loaded successfully")
except Exception as webcam_exc:  # pragma: no cover
    WebcamCapture = None  # type: ignore
    webcam = None
    print(f"[WARN] Webcam import failed: {webcam_exc}")

app = Flask(__name__)

# Paths
BASE_DIR = os.path.dirname(__file__)
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "motion_log.csv")
os.makedirs(LOG_DIR, exist_ok=True)

# Setup GPIO pins
GPIO.setup("USR0", GPIO.OUT)
PIR_PIN = "P9_15"
GPIO.setup(PIR_PIN, GPIO.IN)

# Initialize 8x8 LED Matrix
matrix = LedMatrix8x8(lazy_hw=True)
matrix.open()

# Initialize OLED (optional)
oled_display = None
oled_lock = threading.Lock()
if OledDisplay:
    try:
        oled_display = OledDisplay(lazy_hw=True)
        oled_display.open()
    except Exception as exc:
        print(f"[WARN] OLED init failed: {exc}")
        oled_display = None

# Global state
led_status = 'OFF'
matrix_pattern = 'clear'
animation_running = False
animation_thread = None

# Motion monitoring state
per_second_history = deque(maxlen=3600)  # last hour (3600 seconds)
history_lock = threading.Lock()
last_detection_time = None
current_minute_bucket = None
current_minute_total = 0
stop_event = threading.Event()

def load_existing_history():
    """Load recent history from CSV if available."""
    if not os.path.exists(LOG_FILE):
        return
    try:
        with open(LOG_FILE, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)[-3600:]
        for row in rows:
            ts = datetime.fromisoformat(row["timestamp"])
            count = int(row["second_count"])
            per_second_history.append({'timestamp': ts, 'count': count})
        if rows:
            last_row_time = datetime.fromisoformat(rows[-1]["timestamp"])
            _update_minute_state(last_row_time, rows[-1]["second_count"])
    except Exception as exc:
        print(f"[WARN] Failed to preload motion history: {exc}")

def _update_minute_state(ts: datetime, count: int):
    """Track current minute totals for OLED display."""
    global current_minute_bucket, current_minute_total
    minute_bucket = ts.replace(second=0, microsecond=0)
    if current_minute_bucket is None or minute_bucket != current_minute_bucket:
        current_minute_bucket = minute_bucket
        current_minute_total = 0
    current_minute_total += int(count)
    _update_oled_display()

def _append_csv(ts: datetime, count: int):
    """Append a row to CSV, creating header when needed."""
    file_exists = os.path.exists(LOG_FILE)
    with open(LOG_FILE, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["timestamp", "second_count"])
        writer.writerow([ts.isoformat(), count])

def _update_oled_display():
    if not oled_display:
        return
    try:
        with oled_lock:
            oled_display.clear()
            oled_display.draw_text(f"Motion/min: {current_minute_total:02d}", 0, 0)
            if last_detection_time:
                oled_display.draw_text(f"Last: {last_detection_time.strftime('%H:%M:%S')}", 0, 16)
            else:
                oled_display.draw_text("Last: --:--:--", 0, 16)
            print(f"[OLED] Updated at {datetime.now().strftime('%H:%M:%S')}")
    except Exception as exc:  # pragma: no cover
        print(f"[WARN] OLED update failed: {exc}")

def motion_sampler():
    """Background thread polling the PIR sensor and logging counts."""
    global last_detection_time
    detection_seen = False
    second_start = time.time()

    while not stop_event.is_set():
        try:
            value = GPIO.input(PIR_PIN)
            if value:
                detection_seen = True
                last_detection_time = datetime.now()
            now = time.time()
            if now - second_start >= 1.0:
                ts = datetime.now()
                count = 1 if detection_seen else 0
                with history_lock:
                    per_second_history.append({'timestamp': ts, 'count': count})
                _append_csv(ts, count)
                _update_minute_state(ts, count)
                detection_seen = False
                second_start = now
            time.sleep(0.05)
        except Exception as exc:  # pragma: no cover
            print(f"[WARN] Motion sampler error: {exc}")
            time.sleep(0.5)

def stop_animation():
    """Stop any running animation."""
    global animation_running, animation_thread
    animation_running = False
    if animation_thread and animation_thread.is_alive():
        animation_thread.join(timeout=1.0)

@app.route('/')
def index():
    """Main page."""
    template_data = {
        'LedStatusText': led_status,
        'MatrixPattern': matrix_pattern,
    }
    return render_template('index.html', **template_data)

@app.route('/led/<state>')
def control_led(state):
    """Control USR0 LED."""
    global led_status
    if state == 'on':
        GPIO.output("USR0", GPIO.HIGH)
        led_status = 'ON'
    elif state == 'off':
        GPIO.output("USR0", GPIO.LOW)
        led_status = 'OFF'
    return index()

@app.route('/matrix/<pattern>')
def control_matrix(pattern):
    """Control 8x8 LED Matrix pattern."""
    global matrix_pattern
    stop_animation()
    
    if pattern == 'clear':
        matrix.clear()
        matrix_pattern = 'clear'
    elif pattern == 'fill':
        matrix.fill()
        matrix_pattern = 'fill'
    elif pattern in matrix.PRESETS:
        matrix.set_preset(pattern)
        matrix_pattern = pattern
    else:
        matrix_pattern = 'unknown'
    
    return index()

@app.route('/matrix/animate/<anim_type>')
def animate_matrix(anim_type):
    """Start matrix animation."""
    global animation_running, animation_thread, matrix_pattern
    
    stop_animation()
    animation_running = True
    matrix_pattern = f'animate_{anim_type}'
    
    def run_animation():
        try:
            if anim_type == 'spin':
                matrix.animate_spin(delay_s=0.1, cycles=3)
            elif anim_type == 'sweep_h':
                matrix.animate_sweep_horizontal(delay_s=0.1, cycles=3)
            elif anim_type == 'sweep_v':
                matrix.animate_sweep_vertical(delay_s=0.1, cycles=3)
            elif anim_type == 'grow':
                matrix.animate_grow(delay_s=0.1, cycles=2)
            elif anim_type == 'blink_smiley':
                matrix.animate_blink('smiley', delay_s=0.3, cycles=5)
            elif anim_type == 'blink_heart':
                matrix.animate_blink('heart', delay_s=0.3, cycles=5)
            elif anim_type == 'cycle':
                matrix.animate_cycle_presets(delay_s=0.5, cycles=1)
        finally:
            global animation_running
            animation_running = False
    
    animation_thread = threading.Thread(target=run_animation, daemon=True)
    animation_thread.start()
    
    return index()

@app.route('/motion')
def motion_dashboard():
    """Render motion monitoring dashboard."""
    return render_template('motion.html')

@app.route('/api/motion-data')
def motion_data():
    """Provide motion data for the past hour aggregated per minute."""
    now = datetime.now()
    cutoff = now - timedelta(hours=1)
    with history_lock:
        recent = [entry for entry in per_second_history if entry['timestamp'] >= cutoff]

    # Aggregate by minute
    buckets = {}
    for entry in recent:
        minute_key = entry['timestamp'].replace(second=0, microsecond=0)
        buckets.setdefault(minute_key, 0)
        buckets[minute_key] += entry['count']

    # Fill missing minutes with zero for continuity
    timeline = []
    for i in range(60):
        minute = (now - timedelta(minutes=59 - i)).replace(second=0, microsecond=0)
        timeline.append({
            "minute": minute.isoformat(),
            "count": buckets.get(minute, 0)
        })

    summary = {
        "currentMinuteCount": current_minute_total,
        "lastDetection": last_detection_time.isoformat() if last_detection_time else None
    }
    return jsonify({"timeline": timeline, "summary": summary})

@app.route('/webcam')
def webcam_page():
    """Render webcam viewing page."""
    if webcam is None:
        return render_template('webcam.html', error="Webcam module not available. Please install opencv-python-headless.")
    return render_template('webcam.html')

@app.route('/video_feed')
def video_feed():
    """MJPEG video streaming route."""
    if webcam is None:
        return Response("Webcam not available", status=503, mimetype='text/plain')
    
    # Ensure webcam is open
    if not webcam.is_open:
        if not webcam.open():
            return Response("Failed to open webcam", status=503, mimetype='text/plain')
    
    def generate():
        """Generator function for MJPEG streaming."""
        consecutive_errors = 0
        max_errors = 10
        
        while True:
            try:
                frame = webcam.read_frame()
                if frame is None:
                    consecutive_errors += 1
                    if consecutive_errors > max_errors:
                        # Send error message as text
                        error_msg = b'--frame\r\nContent-Type: text/plain\r\n\r\nWebcam error\r\n'
                        yield error_msg
                        time.sleep(1)
                        consecutive_errors = 0
                    else:
                        time.sleep(0.1)
                    continue
                
                consecutive_errors = 0
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                print(f"[WEBCAM] Stream error: {e}")
                time.sleep(0.5)
                consecutive_errors += 1
                if consecutive_errors > max_errors:
                    break
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/webcam/status')
def webcam_status():
    """Get webcam status."""
    if webcam is None:
        return jsonify({'error': 'Webcam not available'}), 503
    
    status = webcam.get_status()
    return jsonify(status)

@app.route('/api/webcam/config', methods=['POST'])
def webcam_config():
    """Update webcam configuration (frame rate, resolution)."""
    if webcam is None:
        return jsonify({'error': 'Webcam not available'}), 503
    
    try:
        data = request.get_json() or {}
        width = data.get('width')
        height = data.get('height')
        fps = data.get('fps')
        
        # Validate inputs
        if width is not None and (not isinstance(width, int) or width < 160 or width > 1920):
            return jsonify({'error': 'Invalid width (must be 160-1920)'}), 400
        if height is not None and (not isinstance(height, int) or height < 120 or height > 1080):
            return jsonify({'error': 'Invalid height (must be 120-1080)'}), 400
        if fps is not None and (not isinstance(fps, int) or fps < 1 or fps > 30):
            return jsonify({'error': 'Invalid FPS (must be 1-30)'}), 400
        
        success = webcam.update_config(width=width, height=height, fps=fps)
        
        if success:
            return jsonify({'message': 'Configuration updated', 'status': webcam.get_status()})
        else:
            return jsonify({'error': 'Failed to update configuration'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Use 0.0.0.0 to listen on all network interfaces
    # Access via WiFi: http://192.168.72.242:5000
    # Access via USB: http://192.168.7.2:5000
    load_existing_history()
    sampler_thread = threading.Thread(target=motion_sampler, daemon=True)
    sampler_thread.start()
    
    # Initialize webcam if available (will open on first use due to lazy_hw=True)
    if webcam is not None:
        print("[WEBCAM] Webcam ready (will open on first access)")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
    stop_event.set()
    
    # Cleanup webcam on shutdown
    if webcam is not None:
        webcam.close()

