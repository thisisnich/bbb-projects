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
last_button_state = 0  # Track last button state for edge detection

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
    
    # Use oled.py (Adafruit CircuitPython version) - works reliably
    oled_file = os.path.join(myproject_dir, 'oled.py')
    simple_oled_file = os.path.join(myproject_dir, 'oled_simple.py')
    
    if os.path.exists(oled_file):
        sys.path.insert(0, myproject_dir)
        from oled import OledDisplay
        OLED_AVAILABLE = True
        print(f"[OLED] OLED library found (Adafruit CircuitPython) at {oled_file}")
    elif os.path.exists(simple_oled_file):
        sys.path.insert(0, myproject_dir)
        from oled_simple import OledDisplay
        OLED_AVAILABLE = True
        print(f"[OLED] OLED library found (simple version, fallback) at {simple_oled_file}")
    else:
        # Try alternative: if MyFirstPythonProject is inside Assignment
        alt_oled = os.path.join(assignment_dir, 'MyFirstPythonProject', 'oled.py')
        alt_simple = os.path.join(assignment_dir, 'MyFirstPythonProject', 'oled_simple.py')
        
        if os.path.exists(alt_oled):
            sys.path.insert(0, os.path.join(assignment_dir, 'MyFirstPythonProject'))
            from oled import OledDisplay
            OLED_AVAILABLE = True
            print(f"[OLED] OLED library found (Adafruit CircuitPython) at {alt_oled}")
        elif os.path.exists(alt_simple):
            sys.path.insert(0, os.path.join(assignment_dir, 'MyFirstPythonProject'))
            from oled_simple import OledDisplay
            OLED_AVAILABLE = True
            print(f"[OLED] OLED library found (simple version, fallback) at {alt_simple}")
        else:
            print(f"[WARNING] OLED library not found")
            print(f"[WARNING] Tried: {oled_file}")
            print(f"[WARNING] Tried: {simple_oled_file}")
            print(f"[WARNING] Tried: {alt_oled}")
            print(f"[WARNING] Tried: {alt_simple}")
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

# Import AnalogueKeypad (from MyFirstPythonProject) - same pattern as OLED
try:
    import os
    import sys
    
    # Find MyFirstPythonProject directory (already computed above)
    analogue_keypad_file = os.path.join(myproject_dir, 'analogue_key.py')
    alt_keypad_file = os.path.join(assignment_dir, 'MyFirstPythonProject', 'analogue_key.py')
    
    if os.path.exists(analogue_keypad_file):
        sys.path.insert(0, myproject_dir)
        from analogue_key import AnalogueKeypad
        KEYPAD_AVAILABLE = True
        print(f"[KEYPAD] Analogue keypad library found at {analogue_keypad_file}")
    elif os.path.exists(alt_keypad_file):
        sys.path.insert(0, os.path.join(assignment_dir, 'MyFirstPythonProject'))
        from analogue_key import AnalogueKeypad
        KEYPAD_AVAILABLE = True
        print(f"[KEYPAD] Analogue keypad library found at {alt_keypad_file}")
    else:
        print(f"[WARNING] Analogue keypad library not found")
        print(f"[WARNING] Tried: {analogue_keypad_file}")
        print(f"[WARNING] Tried: {alt_keypad_file}")
        KEYPAD_AVAILABLE = False
        AnalogueKeypad = None
except ImportError as e:
    print(f"[WARNING] Analogue keypad library import failed: {e}")
    import traceback
    traceback.print_exc()
    KEYPAD_AVAILABLE = False
    AnalogueKeypad = None
except Exception as e:
    print(f"[WARNING] Error setting up Analogue keypad import: {e}")
    import traceback
    traceback.print_exc()
    KEYPAD_AVAILABLE = False
    AnalogueKeypad = None

# Global hardware objects
oled_display = None
analogue_keypad = None
pot_adc = None  # Potentiometer ADC
POT_AVAILABLE = False

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
        # Note: oled.py uses Adafruit CircuitPython libraries (board, busio, adafruit_ssd1306)
        print("[OLED] Creating OledDisplay with lazy_hw=True...")
        oled_display = OledDisplay(lazy_hw=True)
        print("[OLED] Calling open()...")
        oled_display.open()
        print("[OLED] Display opened successfully")
        
        # Test display
        print("[OLED] Testing display...")
        oled_display.clear()  # clear() calls show()
        oled_display.draw_text("Module 5", 0, 0)  # draw_text() calls show()
        oled_display.draw_text("Ready...", 0, 10)  # draw_text() calls show()
        # No need to call show() again - draw_text() already does it
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
    """Initialize Analog Key Click (6 buttons via AnalogueKeypad)"""
    global analogue_keypad
    print("[BUTTONS] Initializing analogue keypad (6 buttons)...")
    
    if not KEYPAD_AVAILABLE:
        print("[BUTTONS] Analogue keypad library not available - buttons disabled")
        return
    
    try:
        # Use same pattern as OLED: lazy_hw=True, then open()
        # Default pin is P9_40 (ADC)
        # Use thresholds from analogueKey.py (exact matches)
        thresholds = {
            "T1": (0.90, 1.10),   # T1: > 0.90 and < 1.10
            "T2": (0.84, 0.86),   # T2: > 0.84 and < 0.86
            "T3": (0.67, 0.69),   # T3: > 0.67 and < 0.69
            "T4": (0.50, 0.52),   # T4: > 0.50 and < 0.52
            "T5": (0.33, 0.35),   # T5: > 0.33 and < 0.35
            "T6": (0.16, 0.18),   # T6: > 0.16 and < 0.18
            "NONE": (0.00, 0.10)  # NONE: >= 0.00 and < 0.10
        }
        print("[BUTTONS] Creating AnalogueKeypad with lazy_hw=True and custom thresholds...")
        analogue_keypad = AnalogueKeypad(lazy_hw=True, thresholds=thresholds, debounce_ms=50)
        print("[BUTTONS] Calling open()...")
        analogue_keypad.open()
        print("[BUTTONS] Analogue keypad initialized successfully")
        print("[BUTTONS] Buttons: T1=Status, T2=History, T3=Weather, T4=Alternatives, T5=Info, T6=Cycle")
    except Exception as e:
        print(f"[BUTTONS] Error initializing analogue keypad: {e}")
        print(f"[BUTTONS] Error details: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        analogue_keypad = None

def init_potentiometer():
    """Initialize potentiometer on P9_38 for scrolling control"""
    global pot_adc, POT_AVAILABLE
    print("[POT] Initializing potentiometer (P9_38) for scrolling...")
    
    try:
        import Adafruit_BBIO.ADC as ADC
        pot_adc = ADC
        ADC.setup()
        POT_AVAILABLE = True
        print("[POT] Potentiometer initialized successfully")
    except ImportError:
        print("[POT] Adafruit_BBIO.ADC not available - scrolling disabled")
        POT_AVAILABLE = False
        pot_adc = None
    except Exception as e:
        print(f"[POT] Error initializing potentiometer: {e}")
        POT_AVAILABLE = False
        pot_adc = None

def read_potentiometer():
    """Read potentiometer value (0.0-1.0) for scroll control
    
    Maps actual pot range (e.g., 0.17-1.0) to full range (0.0-1.0)
    Returns: (mapped_value, raw_value) tuple for debugging
    """
    global pot_adc, POT_AVAILABLE
    
    if not POT_AVAILABLE or not pot_adc:
        return (0.0, 0.0)
    
    try:
        raw_digital = pot_adc.read("P9_38")
        raw_voltage = raw_digital * 1.8
        
        # Map pot range (0.17-1.0) to full range (0.0-1.0)
        # If pot minimum is 0.17, map it so 0.17 -> 0.0 and 1.0 -> 1.0
        POT_MIN = 0.17  # Minimum value the pot actually reaches
        POT_MAX = 1.0   # Maximum value the pot reaches
        
        if raw_digital <= POT_MIN:
            mapped_value = 0.0
        elif raw_digital >= POT_MAX:
            mapped_value = 1.0
        else:
            # Linear mapping: (value - min) / (max - min)
            mapped_value = (raw_digital - POT_MIN) / (POT_MAX - POT_MIN)
        
        return (mapped_value, raw_digital)  # Returns (mapped 0.0-1.0, raw 0.0-1.0)
    except Exception as e:
        print(f"[POT] Error reading potentiometer: {e}")
        return (0.0, 0.0)

def init_buzz():
    """Initialize Buzz 2 Click"""
    print("[BUZZ] Initializing buzzer...")
    # TODO: Will add later - focus on OLED first
    pass

def read_button():
    """Read which button is pressed (1-6) or 0 if none
    
    Maps AnalogueKeypad keys to button IDs:
    - T1 -> 1 (Status)
    - T2 -> 2 (History)
    - T3 -> 3 (Weather)
    - T4 -> 4 (Alternatives)
    - T5 -> 5 (Info)
    - T6 -> 6 (Cycle views)
    """
    global analogue_keypad
    
    if not analogue_keypad:
        return 0
    
    try:
        # Read raw ADC value (0.0-1.0) like analogueKey.py does
        raw_value = analogue_keypad.read_raw()
        
        # Check thresholds exactly like analogueKey.py (using > and <, not >= and <=)
        if raw_value >= 0.00 and raw_value < 0.10:
            key = None  # No key pressed
        elif raw_value > 0.16 and raw_value < 0.18:
            key = 'T6'
        elif raw_value > 0.33 and raw_value < 0.35:
            key = 'T5'
        elif raw_value > 0.50 and raw_value < 0.52:
            key = 'T4'
        elif raw_value > 0.67 and raw_value < 0.69:
            key = 'T3'
        elif raw_value > 0.84 and raw_value < 0.86:
            key = 'T2'
        elif raw_value > 0.90 and raw_value < 1.10:
            key = 'T1'
        else:
            key = None  # Outside all ranges
        
        if key is None:
            return 0
        
        # Map T1-T6 to button IDs 1-6
        key_map = {
            'T1': 1,
            'T2': 2,
            'T3': 3,
            'T4': 4,
            'T5': 5,
            'T6': 6
        }
        
        button_id = key_map.get(key, 0)
        
        # Debug: print raw value and detected key
        if button_id > 0:
            print(f'[BUTTONS DEBUG] Raw ADC: {raw_value:.3f}, Key: {key}, Button ID: {button_id}')
        
        return button_id
    except Exception as e:
        print(f"[BUTTONS] Error reading button: {e}")
        import traceback
        traceback.print_exc()
        return 0

def show_connecting():
    """Display 'Connecting...' message on OLED (compact, 2 lines)"""
    global oled_display
    if oled_display:
        try:
            oled_display.clear()  # clear() calls show()
            oled_display.draw_centered_text("Connecting", 8)  # draw_centered_text() calls show()
            oled_display.draw_centered_text("...", 20)  # draw_centered_text() calls show()
            # No need to call show() again - draw_centered_text() already does it
        except Exception as e:
            print(f"[OLED] Error showing connecting: {e}")

def show_connected():
    """Display 'Connected' message on OLED (compact, 2 lines)"""
    global oled_display
    if oled_display:
        try:
            oled_display.clear()  # clear() calls show()
            oled_display.draw_centered_text("Connected", 8)  # draw_centered_text() calls show()
            oled_display.draw_centered_text("Waiting...", 20)  # draw_centered_text() calls show()
            # No need to call show() again - draw_centered_text() already does it
        except Exception as e:
            print(f"[OLED] Error showing connected: {e}")

def show_connection_error():
    """Display connection error on OLED (compact, 3 lines)"""
    global oled_display
    if oled_display:
        try:
            oled_display.clear()  # clear() calls show()
            oled_display.draw_centered_text("Error!", 0)  # draw_centered_text() calls show()
            oled_display.draw_centered_text("No server", 12)  # draw_centered_text() calls show()
            oled_display.draw_centered_text("Check URL", 24)  # draw_centered_text() calls show()
            # No need to call show() again - draw_centered_text() already does it
        except Exception as e:
            print(f"[OLED] Error showing error: {e}")

def update_oled_display(view, data):
    """Update OLED display with current view"""
    global oled_display
    
    if not data:
        print("[OLED] No data to display")
        return
    
    if not oled_display:
        print("[OLED] OLED display not initialized - skipping update")
        return
    
    print(f"[OLED] Updating view: {view}, OLED available: {oled_display is not None}")
    
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
            # Show error on OLED
            if oled_display:
                try:
                    oled_display.clear()  # clear() calls show()
                    oled_display.draw_text("ERROR", 0, 0)  # draw_text() calls show()
                    oled_display.draw_text(f"View: {view[:10]}", 0, 8)  # draw_text() calls show()
                    # No need to call show() again - draw_text() already does it
                except:
                    pass
    except Exception as e:
        print(f"[OLED] Error in update_oled_display: {e}")
        import traceback
        traceback.print_exc()
        # Try to show error on OLED
        if oled_display:
            try:
                oled_display.clear()  # clear() calls show()
                oled_display.draw_text("ERROR", 0, 0)  # draw_text() calls show()
                oled_display.draw_text(str(e)[:20], 0, 8)  # draw_text() calls show()
                # No need to call show() again - draw_text() already does it
            except:
                pass

def show_current_status(data):
    """Display View 1: Current Status (scrollable)"""
    global oled_display
    
    current = data.get('current', {})
    weather = data.get('weather', {})
    info = data.get('info', {})
    
    people = current.get('people_count', 0)
    level = current.get('crowd_level', 'unknown')
    wait = current.get('estimated_wait_min', 0)
    temp = weather.get('temp_c', 0)
    rating = info.get('rating_avg', 0)
    humidity = weather.get('humidity_percent', 0)
    uv = weather.get('uv_index', 0)
    comfort = weather.get('comfort_score', 0)
    confidence = current.get('confidence', 0)
    occupancy = current.get('occupancy', 0)
    
    # Prepare all status lines (scrollable content - more details)
    status_lines = [
        f"A:{level.upper()[:4]}",  # Line 0: Court + Level
        f"PPL:{people}",           # Line 1: People count
        f"WAIT:{wait}m" if wait > 0 else f"T:{temp}C",  # Line 2: Wait or Temp
        f"T:{temp}C",               # Line 3: Temperature
        f"R:{rating:.1f}/5",         # Line 4: Rating
        f"H:{humidity}%",           # Line 5: Humidity
        f"UV:{uv}",                 # Line 6: UV Index
        f"C:{comfort}/5",           # Line 7: Comfort Score
        f"OCC:{int(occupancy*100)}%", # Line 8: Occupancy %
        f"CONF:{int(confidence*100)}%", # Line 9: Confidence %
    ]
    
    # Calculate scroll offset from potentiometer
    pot_value, raw_pot = read_potentiometer()
    max_items = len(status_lines)
    max_scroll = max(0, max_items - 3)  # Can scroll to show all lines (3 visible at a time)
    scroll_offset = int(pot_value * max_scroll)
    
    # Debug output
    print(f'[SCROLL DEBUG] STATUS: pot={pot_value:.3f}, max_items={max_items}, max_scroll={max_scroll}, offset={scroll_offset}')
    
    # Draw on OLED - Page 1: Status (scrollable, 3 lines visible)
    if oled_display:
        try:
            # Batch all drawing operations, then show() once to avoid corruption
            if oled_display._draw is None:
                oled_display.open()
            oled_display._draw.rectangle((0, 0, OLED_WIDTH - 1, OLED_HEIGHT - 1), outline=0, fill=0)
            
            # Line 1: Title with scroll indicator
            if max_scroll > 0:
                scroll_indicator = f"STATUS [{scroll_offset+1}-{min(scroll_offset+3, max_items)}/{max_items}]"
            else:
                scroll_indicator = "STATUS"
            oled_display._draw.text((0, 0), scroll_indicator[:16], font=oled_display._font, fill=1)
            
            # Show 3 lines starting from scroll_offset
            y = 8
            for i in range(3):
                idx = scroll_offset + i
                if idx < len(status_lines):
                    oled_display._draw.text((0, y), status_lines[idx], font=oled_display._font, fill=1)
                    y += 8
            
            # Show once at the end
            oled_display.show()
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
    """Display View 2A: Today's Pattern (scrollable)"""
    global oled_display
    
    patterns = data.get('patterns', {})
    hourly = patterns.get('today_hourly', [])
    
    # Calculate scroll offset from potentiometer (0.0-1.0 maps to 0 to max_scroll)
    pot_value, raw_pot = read_potentiometer()
    max_items = len(hourly)
    max_scroll = max(0, max_items - 3)  # Can scroll to show all items (3 visible at a time)
    scroll_offset = int(pot_value * max_scroll)
    
    # Debug output
    print(f'[SCROLL DEBUG] TODAY: pot={pot_value:.3f}, max_items={max_items}, max_scroll={max_scroll}, offset={scroll_offset}')
    
    # Draw on OLED - Page 2: Today Pattern (scrollable, 3 lines visible)
    if oled_display:
        try:
            # Batch all drawing operations, then show() once to avoid corruption
            if oled_display._draw is None:
                oled_display.open()
            oled_display._draw.rectangle((0, 0, OLED_WIDTH - 1, OLED_HEIGHT - 1), outline=0, fill=0)
            
            # Line 1: Title with scroll indicator
            if max_scroll > 0:
                scroll_indicator = f"TODAY [{scroll_offset+1}-{min(scroll_offset+3, max_items)}/{max_items}]"
            else:
                scroll_indicator = "TODAY"
            oled_display._draw.text((0, 0), scroll_indicator[:16], font=oled_display._font, fill=1)
            
            # Show 3 hours starting from scroll_offset
            y = 8
            for i in range(3):
                idx = scroll_offset + i
                if idx < len(hourly):
                    hour_data = hourly[idx]
                    hour_24 = hour_data.get('hour', 0)
                    occ = hour_data.get('occupancy', 0)
                    
                    # Convert 24-hour to 12-hour format with AM/PM
                    if hour_24 == 0:
                        hour_12 = 12
                        am_pm = "AM"
                    elif hour_24 < 12:
                        hour_12 = hour_24
                        am_pm = "AM"
                    elif hour_24 == 12:
                        hour_12 = 12
                        am_pm = "PM"
                    else:
                        hour_12 = hour_24 - 12
                        am_pm = "PM"
                    
                    oled_display._draw.text((0, y), f"{hour_12:2d}{am_pm}:{int(occ*100)}%", font=oled_display._font, fill=1)
                    y += 8
            
            # Show once at the end
            oled_display.show()
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
    """Display View 2B: Weekly Comparison (scrollable)"""
    global oled_display
    
    patterns = data.get('patterns', {})
    weekly = patterns.get('week_same_time', [])
    
    # Calculate scroll offset from potentiometer
    pot_value, raw_pot = read_potentiometer()
    max_items = len(weekly)
    max_scroll = max(0, max_items - 3)  # Can scroll to show all days (3 visible at a time)
    scroll_offset = int(pot_value * max_scroll)
    
    # Debug output
    print(f'[SCROLL DEBUG] WEEKLY: pot={pot_value:.3f}, max_items={max_items}, max_scroll={max_scroll}, offset={scroll_offset}')
    
    # Draw on OLED - Page 3: Weekly Comparison (scrollable, 3 lines visible)
    if oled_display:
        try:
            # Batch all drawing operations, then show() once to avoid corruption
            if oled_display._draw is None:
                oled_display.open()
            oled_display._draw.rectangle((0, 0, OLED_WIDTH - 1, OLED_HEIGHT - 1), outline=0, fill=0)
            
            # Line 1: Title with scroll indicator
            if max_scroll > 0:
                scroll_indicator = f"WEEKLY [{scroll_offset+1}-{min(scroll_offset+3, max_items)}/{max_items}]"
            else:
                scroll_indicator = "WEEKLY"
            oled_display._draw.text((0, 0), scroll_indicator[:16], font=oled_display._font, fill=1)
            
            # Show 3 days starting from scroll_offset
            y = 8
            for i in range(3):
                idx = scroll_offset + i
                if idx < len(weekly):
                    day_data = weekly[idx]
                    day_name = day_data.get('day', '')[:3]  # Mon, Tue, etc
                    occ = day_data.get('occupancy', 0)
                    oled_display._draw.text((0, y), f"{day_name}:{int(occ*100)}%", font=oled_display._font, fill=1)
                    y += 8
            
            # Show once at the end
            oled_display.show()
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
    
    # Draw on OLED - Page 4: Weather (compact, 3 lines)
    if oled_display:
        try:
            # Batch all drawing operations, then show() once to avoid corruption
            if oled_display._draw is None:
                oled_display.open()
            oled_display._draw.rectangle((0, 0, OLED_WIDTH - 1, OLED_HEIGHT - 1), outline=0, fill=0)
            
            # Line 1: Title
            oled_display._draw.text((0, 0), "WEATHER", font=oled_display._font, fill=1)
            # Line 2: Temperature
            oled_display._draw.text((0, 8), f"T:{temp}C H:{humidity}%", font=oled_display._font, fill=1)
            # Line 3: UV and Comfort
            oled_display._draw.text((0, 16), f"UV:{uv} C:{comfort}/5", font=oled_display._font, fill=1)
            
            # Show once at the end
            oled_display.show()
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
    """Display View 4: Alternative Courts (scrollable)"""
    global oled_display
    
    recommendations = data.get('recommendations', {})
    alternatives = recommendations.get('nearby_alternatives', [])
    
    # Calculate scroll offset from potentiometer
    pot_value, raw_pot = read_potentiometer()
    max_items = len(alternatives)
    max_scroll = max(0, max_items - 1)  # Can scroll to show all alternatives (1 visible at a time, 3 lines each)
    scroll_offset = int(pot_value * max_scroll)
    
    # Debug output
    print(f'[SCROLL DEBUG] ALTERNATIVES: pot={pot_value:.3f}, max_items={max_items}, max_scroll={max_scroll}, offset={scroll_offset}')
    
    # Draw on OLED - Page 5: Alternatives (scrollable, 1 alternative visible = 3 lines)
    if oled_display:
        try:
            # Batch all drawing operations, then show() once to avoid corruption
            if oled_display._draw is None:
                oled_display.open()
            oled_display._draw.rectangle((0, 0, OLED_WIDTH - 1, OLED_HEIGHT - 1), outline=0, fill=0)
            
            # Line 1: Title with scroll indicator
            if max_scroll > 0:
                scroll_indicator = f"OTHERS [{scroll_offset+1}/{max_items}]"
            else:
                scroll_indicator = "OTHERS"
            oled_display._draw.text((0, 0), scroll_indicator[:16], font=oled_display._font, fill=1)
            
            # Show alternative at scroll_offset
            if scroll_offset < len(alternatives):
                alt = alternatives[scroll_offset]
                name = alt.get('name', 'Court')[:6]  # Truncate if too long
                people = alt.get('people', 0)
                status = alt.get('status', 'unknown')[:3]  # Short status
                # Line 2: Court name and status
                oled_display._draw.text((0, 8), f"{name}:{status}", font=oled_display._font, fill=1)
                # Line 3: People count
                oled_display._draw.text((0, 16), f"PPL:{people}", font=oled_display._font, fill=1)
            else:
                oled_display._draw.text((0, 8), "None", font=oled_display._font, fill=1)
            
            # Show once at the end
            oled_display.show()
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
    """Display View 5: Court Information (scrollable)"""
    global oled_display
    
    info = data.get('info', {})
    
    surface = info.get('surface', 'Unknown')
    lights = info.get('lighting_hours', 'N/A')
    rating = info.get('rating_avg', 0)
    size = info.get('size', 'Full court')
    facilities = info.get('facilities', [])
    
    # Prepare all info lines (scrollable content - more details)
    info_lines = [
        f"S:{surface[:8]}",         # Line 0: Surface
        f"L:{str(lights)[:10]}",    # Line 1: Lighting hours
        f"R:{rating:.1f}/5",         # Line 2: Rating
        f"Sz:{size[:8]}",           # Line 3: Size
    ]
    
    # Add facilities if available
    if facilities:
        for facility in facilities[:4]:  # Show up to 4 facilities
            info_lines.append(f"F:{facility[:8]}")
    
    # Add more court details if available
    cleaned = info.get('last_cleaned', 'Unknown')
    capacity = info.get('capacity', 'N/A')
    if cleaned != 'Unknown':
        info_lines.append(f"Clean:{cleaned[:6]}")
    if capacity != 'N/A':
        info_lines.append(f"Cap:{capacity}")
    
    # Calculate scroll offset from potentiometer
    pot_value, raw_pot = read_potentiometer()
    max_items = len(info_lines)
    max_scroll = max(0, max_items - 3)  # Can scroll to show all lines (3 visible at a time)
    scroll_offset = int(pot_value * max_scroll)
    
    # Debug output
    print(f'[SCROLL DEBUG] INFO: pot={pot_value:.3f}, max_items={max_items}, max_scroll={max_scroll}, offset={scroll_offset}')
    
    # Draw on OLED - Page 6: Court Info (scrollable, 3 lines visible)
    if oled_display:
        try:
            # Batch all drawing operations, then show() once to avoid corruption
            if oled_display._draw is None:
                oled_display.open()
            oled_display._draw.rectangle((0, 0, OLED_WIDTH - 1, OLED_HEIGHT - 1), outline=0, fill=0)
            
            # Line 1: Title with scroll indicator
            if max_scroll > 0:
                scroll_indicator = f"INFO [{scroll_offset+1}-{min(scroll_offset+3, max_items)}/{max_items}]"
            else:
                scroll_indicator = "INFO"
            oled_display._draw.text((0, 0), scroll_indicator[:16], font=oled_display._font, fill=1)
            
            # Show 3 lines starting from scroll_offset
            y = 8
            for i in range(3):
                idx = scroll_offset + i
                if idx < len(info_lines):
                    oled_display._draw.text((0, y), info_lines[idx], font=oled_display._font, fill=1)
                    y += 8
            
            # Show once at the end
            oled_display.show()
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
        'normal': '🟠',
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
        # T1: Status view
        current_view = 'status'
    elif button_id == 2:
        # T2: Toggle between today/week history
        if current_view == 'history_today':
            current_view = 'history_week'
        else:
            current_view = 'history_today'
    elif button_id == 3:
        # T3: Weather view
        current_view = 'weather'
    elif button_id == 4:
        # T4: Alternatives view
        current_view = 'alternatives'
    elif button_id == 5:
        # T5: Info view
        current_view = 'info'
    elif button_id == 6:
        # T6: Cycle through all views
        view_order = ['status', 'history_today', 'history_week', 'weather', 'alternatives', 'info']
        try:
            current_index = view_order.index(current_view)
            current_view = view_order[(current_index + 1) % len(view_order)]
        except ValueError:
            # If current_view not in list, start with status
            current_view = 'status'
    
    # Reset auto-rotation timer
    last_interaction_time = time.time()
    rotation_index = 0
    
    # Debug output to console
    button_name = f"T{button_id}"
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Button {button_id} ({button_name}) pressed -> View: {current_view}')
    
    # Update display immediately
    if current_data:
        try:
            update_oled_display(current_view, current_data)
            print(f'[DEBUG] Display updated to view: {current_view}')
        except Exception as e:
            print(f'[ERROR] Failed to update OLED display: {e}')
            import traceback
            traceback.print_exc()
    else:
        print(f'[WARNING] No data available to display for view: {current_view}')
        # Show a placeholder on OLED if no data
        if oled_display:
            try:
                oled_display.clear()  # clear() calls show()
                oled_display.draw_text("NO DATA", 0, 0)  # draw_text() calls show()
                oled_display.draw_text(f"View: {current_view[:8]}", 0, 8)  # draw_text() calls show()
                oled_display.draw_text("Waiting...", 0, 16)  # draw_text() calls show()
                # No need to call show() again - draw_text() already does it
            except Exception as e:
                print(f'[ERROR] Failed to show placeholder: {e}')
    
    # Send debug info to web dashboard
    if sio.connected:
        try:
            sio.emit('button_press_debug', {
                'module_id': MODULE_ID,
                'button_id': button_id,
                'button_name': button_name,
                'view': current_view,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            print(f'[DEBUG] Error sending button press to server: {e}')

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
    """Continuously read buttons with edge detection (only trigger on press, not while held)"""
    global last_button_state
    
    while True:
        try:
            button = read_button()
            
            # Edge detection: only trigger when button changes from 0 to >0 (press), not while held
            if button > 0 and last_button_state == 0:
                # Button was just pressed (edge detected)
                handle_button_press(button)
                last_button_state = button
            elif button == 0 and last_button_state > 0:
                # Button was just released
                print(f'[BUTTONS] Button {last_button_state} released')
                last_button_state = 0
            elif button > 0:
                # Button still held (don't trigger again)
                last_button_state = button
            else:
                # No button pressed
                last_button_state = 0
            
            time.sleep(0.05)  # Check buttons 20 times per second (faster for better edge detection)
        except Exception as e:
            print(f'[BUTTON] Error: {e}')
            import traceback
            traceback.print_exc()
            time.sleep(0.5)

def scroll_update_loop():
    """Continuously update display when potentiometer changes (for scrolling)"""
    global current_view, current_data
    last_pot_value = -1.0
    
    while True:
        try:
            if POT_AVAILABLE:
                pot_value, raw_pot = read_potentiometer()
                raw_voltage = raw_pot * 1.8
                
                # Debug output to console
                if abs(pot_value - last_pot_value) > 0.01:  # Print when pot changes by 1%
                    print(f'[POT DEBUG] Mapped: {pot_value:.3f}, Raw: {raw_pot:.3f}, Voltage: {raw_voltage:.3f}V, View: {current_view}')
                
                # Only update if pot value changed significantly (0.05 threshold to avoid constant updates)
                if abs(pot_value - last_pot_value) > 0.05:
                    if current_data:
                        # Update display with new scroll position (all views are now scrollable)
                        if current_view in ['status', 'history_today', 'history_week', 'weather', 'alternatives', 'info']:
                            print(f'[SCROLL] Pot changed: {last_pot_value:.3f} -> {pot_value:.3f}, Updating {current_view}')
                            update_oled_display(current_view, current_data)
                            last_pot_value = pot_value
                        else:
                            # Not a scrollable view, but still update last_pot_value
                            last_pot_value = pot_value
                    else:
                        last_pot_value = pot_value
                elif last_pot_value == -1.0:
                    # First reading, just store it
                    last_pot_value = pot_value
            else:
                time.sleep(1)  # If pot not available, check less frequently
            time.sleep(0.1)  # Check potentiometer 10 times per second
        except Exception as e:
            print(f'[SCROLL] Error: {e}')
            import traceback
            traceback.print_exc()
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
    
    # Initialize hardware
    try:
        init_oled()
        init_buttons()  # Initialize analogue keypad
        init_potentiometer()  # Initialize potentiometer for scrolling
        # init_bar_graph()  # Will add later
        # init_buzz()        # Will add later
        if oled_display:
            print("\n[OK] OLED initialized successfully")
        else:
            print("\n[WARNING] OLED not initialized - using console output only")
        if analogue_keypad:
            print("[OK] Analogue keypad initialized successfully")
        else:
            print("[WARNING] Analogue keypad not initialized - button navigation disabled")
        if POT_AVAILABLE:
            print("[OK] Potentiometer initialized successfully (scrolling enabled)")
        else:
            print("[WARNING] Potentiometer not initialized - scrolling disabled")
    except Exception as e:
        print(f"\n[WARNING] Hardware initialization error: {e}")
        print("Continuing with software simulation...")
        import traceback
        traceback.print_exc()
    
    # Connect to server
    try:
        print(f"\nConnecting to server at {SERVER_URL}...")
        # Show "Connecting..." on OLED
        show_connecting()
        
        sio.connect(SERVER_URL)
        
        # Wait a moment for connection
        time.sleep(1)
        
        if sio.connected:
            print("Connected! Waiting for data from server...")
            # Show "Connected" on OLED
            show_connected()
            time.sleep(1)  # Show connected message briefly
            
            # Start button reading thread
            if analogue_keypad:
                button_thread = threading.Thread(target=button_loop, daemon=True)
                button_thread.start()
                print("[OK] Button reading thread started")
            else:
                print("[WARNING] Button reading thread not started (keypad not available)")
            
            # Start scroll update thread (for potentiometer-controlled scrolling)
            if POT_AVAILABLE:
                scroll_thread = threading.Thread(target=scroll_update_loop, daemon=True)
                scroll_thread.start()
                print("[OK] Scroll update thread started (potentiometer-controlled)")
            
            # Start auto-rotation thread
            if auto_rotation_enabled:
                rotation_thread = threading.Thread(target=auto_rotation_loop, daemon=True)
                rotation_thread.start()
                print("[OK] Auto-rotation thread started")
            
            # Keep main thread alive
            print("\nDisplay running. OLED will update when data received.")
            if analogue_keypad:
                print("Button navigation enabled:")
                print("  T1 = Status, T2 = History, T3 = Weather")
                print("  T4 = Alternatives, T5 = Info, T6 = Cycle views")
            print("Press Ctrl+C to stop.\n")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping...")
        else:
            print("[ERROR] Failed to connect to server")
            show_connection_error()
            
    except socketio.exceptions.ConnectionError as e:
        print(f"[ERROR] Connection error: {e}")
        print("Make sure the server is running and the URL is correct.")
        show_connection_error()
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        show_connection_error()
    finally:
        # Cleanup
        if sio.connected:
            sio.disconnect()
        if analogue_keypad:
            try:
                analogue_keypad.close()
                print("[BUTTONS] Analogue keypad closed")
            except Exception as e:
                print(f"[BUTTONS] Error closing keypad: {e}")
        print("Client disconnected. Goodbye!")

if __name__ == '__main__':
    main()

