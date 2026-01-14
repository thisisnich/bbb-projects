# Motion
import time
import Adafruit_BBIO.GPIO as GPIO
# MIC
import Adafruit_BBIO.ADC as ADC
# OLED
import board
import busio
import digitalio
import adafruit_ssd1306
from board import SCL, SDA
from PIL import Image, ImageDraw, ImageFont

# Socket.IO for server communication
import socketio
from datetime import datetime
import threading

# Webcam support
import subprocess
import base64
import os

# ========== CONFIGURATION ==========
SERVER_URL = 'http://192.168.72.161:5000'  # CHANGE THIS to your server IP
COURT_ID = 'basketball_a'
MODULE_ID = 'crowd_unit_1'
SEND_INTERVAL = 0.5  # Send data every 0.5 seconds (2 FPS)
WEBCAM_DEVICE = '/dev/video0'  # USB webcam device path

# ========== SOCKET.IO CLIENT ==========
sio = socketio.Client()
is_connected = False

@sio.event
def connect():
    """Called when connected to server"""
    global is_connected
    is_connected = True
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Module 1 connected to server')
    
    # Register this module
    sio.emit('module_register', {
        'module_id': MODULE_ID,
        'module_type': 'crowd_detection',
        'court_id': COURT_ID,
        'timestamp': datetime.now().isoformat()
    })
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Module registered with server')

@sio.event
def disconnect():
    """Called when disconnected from server"""
    global is_connected
    is_connected = False
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Module 1 disconnected from server')

# ========== HARDWARE INITIALIZATION ==========

# MIC
ADC.setup()
# Motion
GPIO.setup("P9_15", GPIO.IN)

# OLED
def OLEDClickInit():
    Pin_DC = digitalio.DigitalInOut(board.P9_16)
    Pin_DC.direction = digitalio.Direction.OUTPUT
    Pin_DC.value = False
    Pin_RESET = digitalio.DigitalInOut(board.P9_23)
    Pin_RESET.direction = digitalio.Direction.OUTPUT
    Pin_RESET.value = True
    L_I2c = busio.I2C(SCL, SDA)
    return L_I2c

#OLED
G_I2c = OLEDClickInit()
Display = adafruit_ssd1306.SSD1306_I2C(128, 64, G_I2c, addr=0x3C)
ImageObj = Image.new("1", (Display.width, Display.height))
Draw = ImageDraw.Draw(ImageObj)
Draw.rectangle((32, 25, Display.width - 1, Display.height - 1), outline=1, fill=0)
Font = ImageFont.load_default()

# ========== WEBCAM FUNCTIONS ==========

def check_fswebcam():
    """Check if fswebcam is installed"""
    try:
        subprocess.run(['fswebcam', '--version'], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL, 
                      check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_webcam_device():
    """Check if webcam device exists"""
    return os.path.exists(WEBCAM_DEVICE)

def capture_video_frame():
    """
    Capture video frame from webcam using fswebcam.
    Returns base64 encoded JPEG string, or None if capture fails.
    """
    if not check_webcam_device():
        return None
    
    try:
        # Capture frame using fswebcam
        # -r 640x480: resolution
        # -S 1: skip first frame (often corrupted)
        # --no-banner: no timestamp banner
        # --jpeg 85: JPEG quality
        # -: output to stdout
        result = subprocess.run(
            ['fswebcam', '-r', '640x480', '-S', '1', '--no-banner', '--jpeg', '85', '-'],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=2
        )
        
        if result.returncode == 0 and result.stdout:
            # Encode to base64
            frame_base64 = base64.b64encode(result.stdout).decode('utf-8')
            return frame_base64
        else:
            return None
            
    except subprocess.TimeoutExpired:
        print("[WEBCAM] Capture timeout")
        return None
    except Exception as e:
        print(f"[WEBCAM] Error capturing frame: {e}")
        return None

# ========== SENSOR READING FUNCTIONS ==========

def read_motion_sensor():
    """Read motion sensor (GPIO P9_15)"""
    return GPIO.input("P9_15")

def read_sound_sensor():
    """
    Read sound/microphone sensor (ADC P9_40) and convert to noise level.
    Uses string comparison as in the original code.
    """
    DigitalValue = str(ADC.read("P9_40"))
    baseline = "0.010012210346758366"  # Default baseline value
    
    # Convert ADC reading to noise level (dB approximation)
    # ADC reading is typically 0.0 to 1.0, where baseline is quiet
    # Scale to approximate dB: baseline = 30dB (quiet), higher = louder
    if DigitalValue == baseline:
        noise_db = 30  # Quiet baseline
    else:
        try:
            adc_float = float(DigitalValue)
            # Map ADC value to noise level (30-90 dB range)
            # Higher ADC value = louder sound
            noise_db = 30 + (adc_float * 60)  # Scale to 30-90 dB range
            noise_db = max(30, min(90, noise_db))  # Clamp to reasonable range
        except ValueError:
            noise_db = 30  # Default if conversion fails
    
    return noise_db, DigitalValue

# ========== DATA TRANSMISSION FUNCTION ==========

def send_sensor_data():
    """Send sensor data to server"""
    global is_connected
    
    if not is_connected:
        return
    
    try:
        # Read sensors
        motion_detected = read_motion_sensor()
        noise_db, adc_value = read_sound_sensor()
        
        # Capture video frame
        video_frame = capture_video_frame()
        webcam_status = 'ok' if video_frame is not None else 'error'
        
        # Prepare data payload
        data_payload = {
            'noise_db': noise_db,
            'motion_detected': bool(motion_detected),
            'proximity_triggered': False,  # TODO: Add proximity sensor when available
            'sensors_status': {
                'webcam': webcam_status,
                'mic': 'ok',
                'motion': 'ok',
                'proximity': 'not_implemented'
            }
        }
        
        # Add video frame if available
        if video_frame is not None:
            data_payload['video_frame'] = video_frame
        
        # Send video frame event
        sio.emit('CrowdVideoFrameEvent', {
            'module_id': MODULE_ID,
            'court_id': COURT_ID,
            'timestamp': datetime.now().isoformat(),
            'data': data_payload
        })
        
        frame_info = f", Frame: {len(video_frame)} bytes" if video_frame else ", No frame"
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Data sent: Motion={motion_detected}, Noise={noise_db:.1f}dB{frame_info}")
        
    except Exception as e:
        print(f"[ERROR] Failed to send data: {e}")

# ========== MAIN LOOP ==========

def main_loop():
    """Main sensor reading and display loop"""
    last_send_time = 0
    
    while True:
        #Clear OLED Screen
        ImageObj = Image.new("1", (Display.width, Display.height))
        Draw = ImageDraw.Draw(ImageObj)
        
        # Read sensors
        motion_detected = read_motion_sensor()
        noise_db, adc_value = read_sound_sensor()
        
        # Determine motion status
        if motion_detected:
            Motion = "Detected"
            Draw.text((90, 30), "Yes", font=Font, fill=1)
        else:
            Motion = "Not Detected"
            Draw.text((90, 30), "No", font=Font, fill=1)
        
        # Determine sound status (using string comparison as in original)
        if adc_value == "0.010012210346758366":  # Default baseline
            Sound = "Not Detected"
            Draw.text((90, 50), "No", font=Font, fill=1)
        else:
            Sound = "Detected"
            Draw.text((90, 50), "Yes", font=Font, fill=1)
        
        # Display on OLED
        Draw.text((40, 30), "Motion?", font=Font, fill=1)
        Draw.text((40, 50), "Sound?", font=Font, fill=1)
        print("Motion is %s     Sound is %s     Noise: %.1f dB" % (Motion, Sound, noise_db))
        
        #OLED
        Display.image(ImageObj)
        Display.show()
        
        # Send data to server at specified interval
        current_time = time.time()
        if current_time - last_send_time >= SEND_INTERVAL:
            send_sensor_data()
            last_send_time = current_time
        
        time.sleep(0.1)

# ========== STARTUP ==========

if __name__ == "__main__":
    print("=" * 60)
    print("Module 1: Crowd Intelligence Unit")
    print("=" * 60)
    print(f"Module ID: {MODULE_ID}")
    print(f"Court ID: {COURT_ID}")
    print(f"Server URL: {SERVER_URL}")
    print(f"Webcam Device: {WEBCAM_DEVICE}")
    print("=" * 60)
    
    # Check webcam
    if not check_webcam_device():
        print(f"[WARNING] Webcam device {WEBCAM_DEVICE} not found")
        print("Video frames will not be sent, but sensor data will still work")
    else:
        if not check_fswebcam():
            print("[WARNING] fswebcam not installed")
            print("Install with: sudo apt-get update && sudo apt-get install -y fswebcam")
            print("Video frames will not be sent, but sensor data will still work")
        else:
            print("[OK] Webcam ready")
    
    # Connect to server
    try:
        print(f"\nConnecting to server at {SERVER_URL}...")
        sio.connect(SERVER_URL)
        
        # Wait a moment for connection
        time.sleep(1)
        
        if sio.connected:
            print("Connected! Starting sensor loop...")
            print("Press Ctrl+C to stop.\n")
            
            # Start main loop
            try:
                main_loop()
            except KeyboardInterrupt:
                print("\nStopping...")
        else:
            print("[ERROR] Failed to connect to server")
            print("Continuing with local display only...")
            # Run without server connection
            main_loop()
            
    except socketio.exceptions.ConnectionError as e:
        print(f"[ERROR] Connection error: {e}")
        print("Make sure the server is running and the URL is correct.")
        print("Continuing with local display only...")
        # Run without server connection
        main_loop()
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        print("Continuing with local display only...")
        main_loop()
    finally:
        # Cleanup
        if sio.connected:
            sio.disconnect()
