"""
Module 5: Smart Court Information Display - Client
Displays court information on OLED, Bar Graph, and handles button navigation
Receives data from cloud server via SocketIO
"""
import socketio
import time
import threading
from datetime import datetime
import sys

# ========== CONFIGURATION ==========
SERVER_URL = 'http://192.168.72.161:5000'  # CHANGE THIS to your server IP
COURT_ID = 'basketball_a'
MODULE_ID = 'court_display_5_a'
OLED_WIDTH = 128
OLED_HEIGHT = 64
AUTO_ROTATION_IDLE_SECONDS = 60  # Auto-rotate after 60 seconds idle

# ========== GLOBAL VARIABLES ==========
sio = socketio.Client()
current_view = 'status'  # 'status', 'history_today', 'history_week', 'weather', 'alternatives', 'info'
current_data = None
last_interaction_time = time.time()
auto_rotation_enabled = True
rotation_index = 0

# ========== HARDWARE IMPORTS ==========
# Import OLED library (from MyFirstPythonProject) - same pattern as WebServer.py
try:
    import os
    import sys
    
    # Find MyFirstPythonProject directory
    # File is at: /var/lib/cloud9/Assignment/module5/Module5_Display_Client.py
    # Need: /var/lib/cloud9/MyFirstPythonProject/oled.py
    current_file = os.path.abspath(__file__)
    # Go: module5/ -> Assignment/ -> cloud9/ -> MyFirstPythonProject/
    assignment_dir = os.path.dirname(os.path.dirname(current_file))  # /var/lib/cloud9/Assignment
    cloud9_dir = os.path.dirname(assignment_dir)  # /var/lib/cloud9
    myproject_dir = os.path.join(cloud9_dir, 'MyFirstPythonProject')  # /var/lib/cloud9/MyFirstPythonProject
    
    # Try the correct path first
    oled_file = os.path.join(myproject_dir, 'oled.py')
    if os.path.exists(oled_file):
        sys.path.insert(0, myproject_dir)
        from oled import OledDisplay
        OLED_AVAILABLE = True
        print(f"[OLED] OLED library found at {oled_file}")
    else:
        # Try alternative: if MyFirstPythonProject is inside Assignment
        alt_path = os.path.join(assignment_dir, 'MyFirstPythonProject', 'oled.py')
        if os.path.exists(alt_path):
            sys.path.insert(0, os.path.join(assignment_dir, 'MyFirstPythonProject'))
            from oled import OledDisplay
            OLED_AVAILABLE = True
            print(f"[OLED] OLED library found at {alt_path}")
        else:
            print(f"[WARNING] OLED library not found")
            print(f"[WARNING] Tried: {oled_file}")
            print(f"[WARNING] Tried: {alt_path}")
            OLED_AVAILABLE = False
            OledDisplay = None
except ImportError as e:
    print(f"[WARNING] OLED library import failed: {e}")
    import traceback
    traceback.print_exc()
    OLED_AVAILABLE = False
    OledDisplay = None
except Exception as e:
    print(f"[WARNING] Error setting up OLED import: {e}")
    import traceback
    traceback.print_exc()
    OLED_AVAILABLE = False
    OledDisplay = None

# Global hardware objects
oled_display = None

def init_oled():
    """Initialize OLED display - Slot 3 (I2C) - using same pattern as WebServer.py"""
    global oled_display
    print("[OLED] Initializing OLED display (Slot 3 - I2C)...")
    
    if not OLED_AVAILABLE:
        print("[OLED] OLED library not available - using console output only")
        return
    
    try:
        # Use same pattern as WebServer.py: lazy_hw=True, then open()
        # Default size is 64x32, default I2C address is 0x3C
        print("[OLED] Creating OledDisplay with lazy_hw=True...")
        oled_display = OledDisplay(lazy_hw=True)
        print("[OLED] Calling open()...")
        oled_display.open()
        print("[OLED] Display opened successfully")
        
        # Test display
        print("[OLED] Testing display...")
        oled_display.clear()
        oled_display.draw_text("Module 5", 0, 0)
        oled_display.draw_text("Ready...", 0, 10)
        print("[OLED] OLED display initialized successfully")
    except Exception as e:
        print(f"[OLED] Error initializing OLED: {e}")
        print(f"[OLED] Error details: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        oled_display = None

def init_bar_graph():
    """Initialize Bar Graph 2 Click or 8x8 LED Matrix"""
    print("[BARGRAPH] Initializing bar graph...")
    # TODO: Will add later - focus on OLED first
    pass

def init_buttons():
    """Initialize Analog Key Click (5 buttons)"""
    print("[BUTTONS] Initializing buttons...")
    # TODO: Will add later - focus on OLED first
    pass

def init_buzz():
    """Initialize Buzz 2 Click"""
    print("[BUZZ] Initializing buzzer...")
    # TODO: Will add later - focus on OLED first
    pass

def read_button():
    """Read which button is pressed (1-5) or 0 if none"""
    # TODO: Will add later - focus on OLED first
    return 0

def update_oled_display(view, data):
    """Update OLED display with current view"""
    global oled_display
    
    if not data:
        print("[OLED] No data to display")
        return
    
    if not oled_display:
        print("[OLED] OLED display not initialized - skipping update")
        return
    
    print(f"[OLED] Updating view: {view}")
    
    try:
        if view == 'status':
            show_current_status(data)
        elif view == 'history_today':
            show_today_pattern(data)
        elif view == 'history_week':
            show_weekly_comparison(data)
        elif view == 'weather':
            show_weather_details(data)
        elif view == 'alternatives':
            show_alternatives(data)
        elif view == 'info':
            show_court_info(data)
        else:
            print(f"[OLED] Unknown view: {view}")
    except Exception as e:
        print(f"[OLED] Error in update_oled_display: {e}")
        import traceback
        traceback.print_exc()

def show_current_status(data):
    """Display View 1: Current Status"""
    global oled_display
    
    current = data.get('current', {})
    weather = data.get('weather', {})
    info = data.get('info', {})
    
    people = current.get('people_count', 0)
    level = current.get('crowd_level', 'unknown')
    wait = current.get('estimated_wait_min', 0)
    temp = weather.get('temp_c', 0)
    rating = info.get('rating_avg', 0)
    
    # Draw on OLED if available - using same pattern as WebServer.py
    if oled_display:
        try:
            # Clear and draw text (each draw_text calls show() internally)
            oled_display.clear()
            oled_display.draw_text("COURT A", 0, 0)
            oled_display.draw_text("=" * 10, 0, 8)  # Shorter for 64px width
            
            level_text = f"{level.upper()}"
            oled_display.draw_text(level_text, 0, 16)
            oled_display.draw_text(f"Ppl: {people}", 0, 24)
        except Exception as e:
            print(f"[OLED] Error drawing status: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("[OLED] WARNING: oled_display is None - cannot draw")
    
    # Also print to console for debugging
    print(f"""
    ┌─────────────────────┐
    │ 🏀 COURT A          │
    │ ═══════════════════ │
    │                     │
    │ NOW: {get_level_emoji(level)} {level.upper():<10}│
    │ People: {people:<13}│
    │ Est wait: {wait} min    │
    │                     │
    │ Weather: ☀️ {temp}°C    │
    │ Rating: {'⭐' * int(rating)}     │
    │                     │
    │ Press [2] for best  │
    │ times to visit →    │
    └─────────────────────┘
    """)

def show_today_pattern(data):
    """Display View 2A: Today's Pattern"""
    global oled_display
    
    patterns = data.get('patterns', {})
    hourly = patterns.get('today_hourly', [])
    
    # Draw on OLED if available
    if oled_display:
        try:
            oled_display.clear()
            oled_display.draw_text("TODAY PATTERN", 0, 0)
            oled_display.draw_text("=" * 15, 0, 8)
            
            y = 16
            for hour_data in hourly[:6]:  # Show 6 hours
                hour = hour_data.get('hour', 0)
                occupancy = hour_data.get('occupancy', 0)
                bar = int(occupancy * 8)  # Scale to 8 chars for OLED
                hour_text = f"{hour:2d}H {'*' * bar}"
                oled_display.draw_text(hour_text, 0, y)
                y += 8
                if y > 60:
                    break
        except Exception as e:
            print(f"[OLED] Error drawing pattern: {e}")
    
    # Also print to console
    print(f"""
    ┌─────────────────────┐
    │ TODAY'S PATTERN     │
    │ ═══════════════════ │
    │                     │
    │ 8AM  ░░░░░ Empty   │
    │ 10AM ██░░░ Light   │
    │ 12PM ████░ Busy    │
    │ 2PM  █████ Full    │
    │ 3PM  █████ FULL ←  │
    │ 5PM  ████░ Busy    │
    │ 7PM  ███░░ Moderate│
    │ 9PM  ░░░░░ Empty   │
    │                     │
    │ 💡 Quiet after 8PM  │
    │ Press [2] again →   │
    └─────────────────────┘
    """)

def show_weekly_comparison(data):
    """Display View 2B: Weekly Comparison"""
    global oled_display
    
    patterns = data.get('patterns', {})
    weekly = patterns.get('week_same_time', [])
    
    # Draw on OLED if available
    if oled_display:
        try:
            oled_display.clear()
            oled_display.draw_text("WEEKLY", 0, 0)
            oled_display.draw_text("=" * 15, 0, 8)
            
            y = 16
            for day_data in weekly[:6]:  # Show 6 days
                day = day_data.get('day', '')
                occupancy = day_data.get('occupancy', 0)
                bar = int(occupancy * 8)
                day_text = f"{day} {'*' * bar}"
                oled_display.draw_text(day_text, 0, y)
                y += 8
                if y > 60:
                    break
        except Exception as e:
            print(f"[OLED] Error drawing weekly: {e}")
    
    # Also print to console
    print(f"""
    ┌─────────────────────┐
    │ THIS TIME WEEKLY    │
    │ ═══════════════════ │
    │ 3PM Comparison:     │
    │                     │
    │ MON  ████░ 75%     │
    │ TUE  ███░░ 65%     │
    │ WED  █████ 90%     │
    │ THU  █████ 85% ←   │
    │ FRI  █████ 95%     │
    │ SAT  ████░ 70%     │
    │ SUN  ██░░░ 45%     │
    │                     │
    │ 💡 Sundays quieter! │
    │ Press [1] for now → │
    └─────────────────────┘
    """)

def show_weather_details(data):
    """Display View 3: Weather Details"""
    global oled_display
    
    weather = data.get('weather', {})
    
    temp = weather.get('temp_c', 0)
    humidity = weather.get('humidity_percent', 0)
    uv = weather.get('uv_index', 0)
    comfort = weather.get('comfort_score', 0)
    
    # Draw on OLED if available
    if oled_display:
        try:
            oled_display.clear()
            oled_display.draw_text("WEATHER", 0, 0)
            oled_display.draw_text("=" * 15, 0, 8)
            oled_display.draw_text(f"Temp: {temp}C", 0, 16)
            oled_display.draw_text(f"Humid: {humidity}%", 0, 24)
            oled_display.draw_text(f"UV: {uv}", 0, 32)
            oled_display.draw_text(f"Comfort: {comfort}/5", 0, 40)
        except Exception as e:
            print(f"[OLED] Error drawing weather: {e}")
    
    # Also print to console
    print(f"""
    ┌─────────────────────┐
    │ WEATHER CONDITIONS  │
    │ ═══════════════════ │
    │ Temp: {temp}°C ☀️       │
    │ Humidity: {humidity}%       │
    │ UV: {uv} (Very High)⚠️ │
    │ Air Quality: Good ✓ │
    │                     │
    │ Comfort: {comfort}/5        │
    │ [Bar shows: ███░░]  │
    │                     │
    │ TIPS:               │
    │ • Use sunscreen     │
    │ • Stay hydrated     │
    │ • Best: After 6PM   │
    └─────────────────────┘
    """)

def show_alternatives(data):
    """Display View 4: Alternative Courts"""
    global oled_display
    
    recommendations = data.get('recommendations', {})
    alternatives = recommendations.get('nearby_alternatives', [])
    
    # Draw on OLED if available
    if oled_display:
        try:
            oled_display.clear()
            oled_display.draw_text("OTHER COURTS", 0, 0)
            oled_display.draw_text("=" * 15, 0, 8)
            
            y = 16
            for alt in alternatives[:2]:  # Show 2 alternatives
                name = alt.get('name', 'Court')
                people = alt.get('people', 0)
                status = alt.get('status', 'unknown')
                oled_display.draw_text(f"{name}: {status}", 0, y)
                oled_display.draw_text(f"  {people} people", 0, y + 8)
                y += 16
                if y > 50:
                    break
        except Exception as e:
            print(f"[OLED] Error drawing alternatives: {e}")
    
    # Also print to console
    print(f"""
    ┌─────────────────────┐
    │ OTHER COURTS NEARBY │
    │ ═══════════════════ │
    │                     │
    │ THIS: 🔴 FULL (8)   │
    │                     │
    │ Court B (200m away) │
    │ → 🟡 Light (3 ppl)  │
    │                     │
    │ Court C (500m away) │
    │ → 🟢 Empty (0 ppl)  │
    │                     │
    │ 💡 Court C best now!│
    │                     │
    │ [Buzz confirms]     │
    └─────────────────────┘
    """)

def show_court_info(data):
    """Display View 5: Court Information"""
    global oled_display
    
    info = data.get('info', {})
    
    surface = info.get('surface', 'Unknown')
    lights = info.get('lighting_hours', 'N/A')
    rating = info.get('rating_avg', 0)
    
    # Draw on OLED if available
    if oled_display:
        try:
            oled_display.clear()
            oled_display.draw_text("COURT INFO", 0, 0)
            oled_display.draw_text("=" * 15, 0, 8)
            oled_display.draw_text(f"Surface: {surface}", 0, 16)
            oled_display.draw_text(f"Lights: {lights}", 0, 24)
            oled_display.draw_text(f"Rating: {rating:.1f}", 0, 32)
        except Exception as e:
            print(f"[OLED] Error drawing info: {e}")
    
    # Also print to console
    print(f"""
    ┌─────────────────────┐
    │ COURT INFORMATION   │
    │ ═══════════════════ │
    │                     │
    │ Surface: {surface:<12}│
    │ Lights: {lights:<13}│
    │ Size: Full court    │
    │                     │
    │ FACILITIES:         │
    │ ✓ Water cooler      │
    │ ✓ Covered seating   │
    │ ✓ Restrooms nearby  │
    │                     │
    │ Rating: {'⭐' * int(rating)} ({rating})│
    │ Cleaned: Today 8AM  │
    └─────────────────────┘
    """)

def update_bar_graph(data):
    """Update Bar Graph 2 Click or 8x8 LED Matrix with hourly pattern"""
    patterns = data.get('patterns', {})
    hourly = patterns.get('today_hourly', [])
    
    # TODO: Actually update bar graph hardware
    # Example: For 8 bars showing 8-hour window
    print(f"[BARGRAPH] Updating bar graph with {len(hourly)} data points")
    
    # Show occupancy levels as bars
    for i, hour_data in enumerate(hourly[:8]):  # Show 8 hours
        occupancy = hour_data.get('occupancy', 0)
        bar_level = int(occupancy * 8)  # Scale to 8 levels
        print(f"  Hour {i}: {'█' * bar_level}{'░' * (8 - bar_level)} ({int(occupancy*100)}%)")

def buzz_beep(count=1):
    """Play buzzer beep"""
    # TODO: Actually trigger buzzer
    print(f"[BUZZ] Beep x{count}")

def get_level_emoji(level):
    """Get emoji for crowd level"""
    emoji_map = {
        'empty': '🟢',
        'light': '🟡',
        'moderate': '🟠',
        'busy': '🟠',
        'full': '🔴'
    }
    return emoji_map.get(level.lower(), '⚪')

# ========== SOCKET.IO EVENTS ==========

@sio.event
def connect():
    """Called when connected to server"""
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Module 5 connected to server')
    
    # Register this module
    sio.emit('module_register', {
        'module_id': MODULE_ID,
        'module_type': 'display',
        'court_id': COURT_ID,
        'timestamp': datetime.now().isoformat()
    })

@sio.event
def disconnect():
    """Called when disconnected from server"""
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Module 5 disconnected from server')

@sio.event
def registration_ack(data):
    """Acknowledgment from server"""
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Registration confirmed: {data.get("status")}')

@sio.event
def DisplayUpdate(data):
    """Receive display update from server"""
    global current_data, oled_display
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Display update received')
    
    current_data = data
    
    # Update bar graph (always visible)
    update_bar_graph(data)
    
    # Update OLED based on current view
    print(f'[DEBUG] Updating OLED with view: {current_view}, OLED available: {oled_display is not None}')
    update_oled_display(current_view, data)

# ========== BUTTON HANDLING ==========

def handle_button_press(button_id):
    """Handle button press - switch views"""
    global current_view, last_interaction_time, rotation_index
    
    if button_id == 0:
        return  # No button pressed
    
    # Buzz feedback
    buzz_beep(1)
    
    # Change view based on button
    if button_id == 1:
        current_view = 'status'
    elif button_id == 2:
        # Toggle between today/week history
        if current_view == 'history_today':
            current_view = 'history_week'
        else:
            current_view = 'history_today'
    elif button_id == 3:
        current_view = 'weather'
    elif button_id == 4:
        current_view = 'alternatives'
    elif button_id == 5:
        current_view = 'info'
    
    # Reset auto-rotation timer
    last_interaction_time = time.time()
    rotation_index = 0
    
    # Update display immediately
    if current_data:
        update_oled_display(current_view, current_data)
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Button {button_id} pressed -> View: {current_view}')

def auto_rotation():
    """Auto-cycle through views if no user interaction"""
    global current_view, rotation_index, last_interaction_time
    
    if not auto_rotation_enabled or not current_data:
        return
    
    idle_time = time.time() - last_interaction_time
    
    if idle_time > AUTO_ROTATION_IDLE_SECONDS:
        rotation_views = ['status', 'history_today', 'weather', 'status']
        current_view = rotation_views[rotation_index % len(rotation_views)]
        rotation_index += 1
        
        # Update display
        update_oled_display(current_view, current_data)
        
        # Reset timer (will rotate again in 15 seconds)
        last_interaction_time = time.time() + 15  # Show each view for 15 seconds

# ========== MAIN LOOPS ==========

def button_loop():
    """Continuously read buttons"""
    while True:
        try:
            button = read_button()
            if button > 0:
                handle_button_press(button)
            time.sleep(0.1)  # Check buttons 10 times per second
        except Exception as e:
            print(f'[BUTTON] Error: {e}')
            time.sleep(0.5)

def auto_rotation_loop():
    """Auto-rotation check loop"""
    while True:
        try:
            auto_rotation()
            time.sleep(1)  # Check every second
        except Exception as e:
            print(f'[AUTO_ROTATION] Error: {e}')
            time.sleep(1)

# ========== MAIN FUNCTION ==========

def main():
    """Main function"""
    print("=" * 60)
    print("Module 5: Smart Court Information Display")
    print("=" * 60)
    print(f"Module ID: {MODULE_ID}")
    print(f"Court ID: {COURT_ID}")
    print(f"Server URL: {SERVER_URL}")
    print("=" * 60)
    
    # Initialize hardware (starting with OLED only)
    try:
        init_oled()
        # init_bar_graph()  # Will add later
        # init_buttons()     # Will add later
        # init_buzz()        # Will add later
        if oled_display:
            print("\n[OK] OLED initialized successfully")
        else:
            print("\n[WARNING] OLED not initialized - using console output only")
    except Exception as e:
        print(f"\n[WARNING] Hardware initialization error: {e}")
        print("Continuing with software simulation...")
        import traceback
        traceback.print_exc()
    
    # Connect to server
    try:
        print(f"\nConnecting to server at {SERVER_URL}...")
        sio.connect(SERVER_URL)
        
        # Wait a moment for connection
        time.sleep(1)
        
        if sio.connected:
            print("Connected! Waiting for data from server...")
            
            # TODO: Start button reading thread (will add later)
            # button_thread = threading.Thread(target=button_loop, daemon=True)
            # button_thread.start()
            
            # TODO: Start auto-rotation thread (will add later)
            # rotation_thread = threading.Thread(target=auto_rotation_loop, daemon=True)
            # rotation_thread.start()
            
            # Keep main thread alive
            print("\nDisplay running. OLED will update when data received.")
            print("(Buttons and auto-rotation will be added next)")
            print("Press Ctrl+C to stop.\n")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping...")
        else:
            print("[ERROR] Failed to connect to server")
            
    except socketio.exceptions.ConnectionError as e:
        print(f"[ERROR] Connection error: {e}")
        print("Make sure the server is running and the URL is correct.")
    except Exception as e:
        print(f"[ERROR] Error: {e}")
    finally:
        # Cleanup
        if sio.connected:
            sio.disconnect()
        print("Client disconnected. Goodbye!")

if __name__ == '__main__':
    main()

