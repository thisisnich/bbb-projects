import time
import board
import busio
import digitalio
import Adafruit_BBIO.ADC as ADC
import adafruit_ssd1306
from board import SCL, SDA
from PIL import Image, ImageDraw, ImageFont

# Socket.IO for server communication
import socketio
from datetime import datetime

# ========== CONFIGURATION ==========
SERVER_URL = 'http://192.168.72.161:5000'  # CHANGE THIS to your server IP
COURT_ID = 'basketball_a'
MODULE_ID = 'feedback_kiosk_3'

# ========== SOCKET.IO CLIENT ==========
sio = socketio.Client()
is_connected = False

@sio.event
def connect():
    """Called when connected to server"""
    global is_connected
    is_connected = True
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Module 3 connected to server')
    
    # Register this module
    sio.emit('module_register', {
        'module_id': MODULE_ID,
        'module_type': 'feedback',
        'court_id': COURT_ID,
        'timestamp': datetime.now().isoformat()
    })
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Module registered with server')

@sio.event
def disconnect():
    """Called when disconnected from server"""
    global is_connected
    is_connected = False
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Module 3 disconnected from server')

# =====================================================
# OLED INITIALIZATION
# =====================================================
def OLEDClickInit():
    dc = digitalio.DigitalInOut(board.P9_16)
    dc.direction = digitalio.Direction.OUTPUT
    dc.value = False

    reset = digitalio.DigitalInOut(board.P9_23)
    reset.direction = digitalio.Direction.OUTPUT
    reset.value = True

    return busio.I2C(SCL, SDA)

i2c = OLEDClickInit()
display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)
font = ImageFont.load_default()

# =====================================================
# ADC INITIALIZATION
# =====================================================
ADC.setup()
POT_PIN = "P9_37"
KEY_PIN = "P9_39"
IR_PIN  = "P9_40"

# =====================================================
# SYSTEM SETTINGS
# =====================================================
IR_WAKE_DISTANCE = 15.0
TOTAL_PAGES = 3

ratings = []
last_rating = None
screen_on = False
current_page = 0
interaction_start_time = None

# =====================================================
# INPUT FUNCTIONS
# =====================================================
def read_keypad():
    v = ADC.read(KEY_PIN)
    if 0.90 < v < 1.10: return 1
    if 0.84 < v < 0.86: return 2
    if 0.67 < v < 0.69: return 3
    if 0.50 < v < 0.52: return 4
    if 0.33 < v < 0.35: return 5
    if 0.16 < v < 0.18: return 6
    return None

def read_ir_distance():
    dv = ADC.read(IR_PIN)
    if dv == 0:
        return None
    voltage = (dv * 1.8) * (2200 / 1200)
    return 29.988 * pow(voltage, -1.173)

def read_page_from_pot():
    value = ADC.read(POT_PIN)

    if value < 0.33:
        return 0
    elif value < 0.50:
        return 1
    else:
        return 2

# =====================================================
# FEEDBACK TRANSMISSION
# =====================================================

def send_status_update(is_active, distance=None):
    """
    Send kiosk status update to server (on/off based on proximity)
    
    Args:
        is_active: True if kiosk is active (user detected), False if idle
        distance: IR sensor distance reading (optional)
    """
    global is_connected
    
    if not is_connected:
        return False
    
    try:
        sio.emit('FeedbackStatusEvent', {
            'module_id': MODULE_ID,
            'court_id': COURT_ID,
            'timestamp': datetime.now().isoformat(),
            'status': 'active' if is_active else 'idle',
            'is_active': is_active,
            'distance_cm': distance,
            'screen_on': is_active
        })
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send status update: {e}")
        return False

def send_rating_to_server(rating):
    """
    Send rating feedback to server when user presses a key (1-6)
    
    Args:
        rating: Rating value from keypad (1-6)
    """
    global is_connected, interaction_start_time
    
    if not is_connected:
        print("[WARNING] Not connected to server. Rating saved locally only.")
        return False
    
    try:
        # Calculate interaction time if available
        interaction_time = 0
        if interaction_start_time:
            interaction_time = int(time.time() - interaction_start_time)
        
        # Map keypad buttons to questions
        # Keys 1-5: Overall quality rating (1-5 scale)
        # Key 6: Could be used for a different question or as "skip"
        if rating <= 5:
            question_id = 'overall_quality'
            question_text = 'How would you rate the overall court quality?'
            rating_scale = '1-5'
            actual_rating = rating  # Use key value directly (1-5)
        else:
            # Key 6: Could be a different question or skip
            question_id = 'court_satisfaction'
            question_text = 'Overall satisfaction?'
            rating_scale = '1-6'
            actual_rating = rating
        
        sio.emit('FeedbackDataEvent', {
            'module_id': MODULE_ID,
            'court_id': COURT_ID,
            'timestamp': datetime.now().isoformat(),
            'data': {
                'report_type': 'rating',
                'question_id': question_id,
                'question_text': question_text,
                'rating': actual_rating,
                'rating_scale': rating_scale,
                'interaction_time_seconds': interaction_time,
                'gesture_used': False  # Using keypad, not gestures
            }
        })
        
        print(f'[{datetime.now().strftime("%H:%M:%S")}] Rating sent to server: {actual_rating}/{rating_scale}')
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to send rating to server: {e}")
        return False

# =====================================================
# DISPLAY RENDERING
# =====================================================
def draw_page(page):
    image = Image.new("1", (display.width, display.height))
    draw = ImageDraw.Draw(image)
    draw.rectangle((32, 25, display.width, display.height), fill=0)

    if page == 0:
        avg = "--" if not ratings else f"{sum(ratings)/len(ratings):.2f}"
        draw.text((40, 40), "Average Feedback", font=font, fill=1)
        draw.text((40, 50), avg, font=font, fill=1)

    elif page == 1:
        txt = "--" if last_rating is None else str(last_rating)
        draw.text((40, 40), "Last Feedback", font=font, fill=1)
        draw.text((40, 50), txt, font=font, fill=1)

    elif page == 2:
        draw.text((40, 40), "Enter Feedback", font=font, fill=1)
        draw.text((40, 50), "Use Keys 1 - 6", font=font, fill=1)

    display.image(image)
    display.show()

# =====================================================
# MAIN LOOP
# =====================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Module 3: Feedback Kiosk")
    print("=" * 60)
    print(f"Module ID: {MODULE_ID}")
    print(f"Court ID: {COURT_ID}")
    print(f"Server URL: {SERVER_URL}")
    print("=" * 60)
    
    # Connect to server
    try:
        print(f"\nConnecting to server at {SERVER_URL}...")
        sio.connect(SERVER_URL)
        
        # Wait a moment for connection
        time.sleep(1)
        
        if sio.connected:
            print("Connected! Starting feedback kiosk...")
        else:
            print("[WARNING] Failed to connect to server")
            print("Continuing with local operation only...")
            
    except socketio.exceptions.ConnectionError as e:
        print(f"[WARNING] Connection error: {e}")
        print("Make sure the server is running and the URL is correct.")
        print("Continuing with local operation only...")
    except Exception as e:
        print(f"[WARNING] Error: {e}")
        print("Continuing with local operation only...")
    
    print("\nSystem Started (IR-controlled OLED)")
    print("Press Ctrl+C to stop.\n")
    
    try:
        while True:
            distance = read_ir_distance()
            
            # ---------- IR WAKE / SLEEP ----------
            if distance is not None and distance <= IR_WAKE_DISTANCE:
                if not screen_on:
                    print("[SYSTEM] User detected → OLED ON")
                    display.poweron()
                    screen_on = True
                    interaction_start_time = time.time()  # Start tracking interaction time
                    draw_page(2)  # Show "Enter Feedback" page
                    # Send status update: kiosk is now active
                    send_status_update(True, distance)
            else:
                if screen_on:
                    print("[SYSTEM] No user → OLED OFF")
                    display.fill(0)
                    display.show()
                    display.poweroff()
                    screen_on = False
                    interaction_start_time = None  # Reset interaction timer
                    # Send status update: kiosk is now idle
                    send_status_update(False, distance)
                time.sleep(0.2)
                continue
            
            # ---------- PAGE CONTROL ----------
            current_page = read_page_from_pot()

            # ---------- FEEDBACK INPUT ----------
            key = read_keypad()
            if key is not None:
                ratings.append(key)
                last_rating = key
                print(f"[FEEDBACK] Rating submitted: {key}")
                
                # Send to server
                send_rating_to_server(key)
                
                time.sleep(0.6)  # debounce
            else:
                key = None
            
            draw_page(current_page)
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        # Cleanup
        if sio.connected:
            sio.disconnect()
        if screen_on:
            display.fill(0)
            display.show()
            display.poweroff()
