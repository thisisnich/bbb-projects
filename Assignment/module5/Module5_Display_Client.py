"""
Module 5: Smart Court Information Display - Client
Displays court information on OLED, Bar Graph, and handles button navigation
Receives data from cloud server via SocketIO

Click Board Slot Assignments:
- Slot 1 (I2C): OLED Click (I2C address 0x3C) - main display
- Slot 2 (ADC): Potentiometer (P9_37) - scrolling control (range: 0.0-0.545)
- Slot 3 (SPI): 8x8 LED Matrix Click (SPI0: CS=P9_17, SCK=P9_22, MISO=P9_29, MOSI=P9_18) - infographics
- Slot 4 (ADC): Analog Key Click (P9_39) - 6-button keypad for navigation
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
OLED_WIDTH = 64  # Actual OLED display is 64x32
OLED_HEIGHT = 32
AUTO_ROTATION_IDLE_SECONDS = 60  # Auto-rotate after 60 seconds idle

# ========== GLOBAL VARIABLES ==========
sio = socketio.Client()
current_view = 'status'  # 'status', 'history_today', 'history_week', 'weather', 'alternatives', 'info'
current_data = None
last_interaction_time = time.time()
auto_rotation_enabled = True
rotation_index = 0
last_button_state = 0  # Track last button state for edge detection
last_oled_update_time = 0  # Track last OLED update time for debouncing
OLED_UPDATE_DEBOUNCE_MS = 100  # Minimum time between OLED updates (100ms)
oled_update_lock = threading.Lock()  # Lock to prevent concurrent OLED updates

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

# Import 8x8 LED Matrix (from MyFirstPythonProject) - using importlib since module name starts with number
try:
    import importlib.util
    import os
    import sys
    
    # Find MyFirstPythonProject directory (already computed above)
    eightx8_file = os.path.join(myproject_dir, '8x8.py')
    alt_eightx8_file = os.path.join(assignment_dir, 'MyFirstPythonProject', '8x8.py')
    
    if os.path.exists(eightx8_file):
        spec = importlib.util.spec_from_file_location("ledmatrix8x8", eightx8_file)
        ledmatrix_module = importlib.util.module_from_spec(spec)
        sys.modules["ledmatrix8x8"] = ledmatrix_module
        spec.loader.exec_module(ledmatrix_module)
        LedMatrix8x8 = ledmatrix_module.LedMatrix8x8
        LEDMATRIX_AVAILABLE = True
        print(f"[LEDMATRIX] 8x8 LED matrix library found at {eightx8_file}")
    elif os.path.exists(alt_eightx8_file):
        spec = importlib.util.spec_from_file_location("ledmatrix8x8", alt_eightx8_file)
        ledmatrix_module = importlib.util.module_from_spec(spec)
        sys.modules["ledmatrix8x8"] = ledmatrix_module
        spec.loader.exec_module(ledmatrix_module)
        LedMatrix8x8 = ledmatrix_module.LedMatrix8x8
        LEDMATRIX_AVAILABLE = True
        print(f"[LEDMATRIX] 8x8 LED matrix library found at {alt_eightx8_file}")
    else:
        print(f"[WARNING] 8x8 LED matrix library not found")
        print(f"[WARNING] Tried: {eightx8_file}")
        print(f"[WARNING] Tried: {alt_eightx8_file}")
        LEDMATRIX_AVAILABLE = False
        LedMatrix8x8 = None
except ImportError as e:
    print(f"[WARNING] 8x8 LED matrix library import failed: {e}")
    import traceback
    traceback.print_exc()
    LEDMATRIX_AVAILABLE = False
    LedMatrix8x8 = None
except Exception as e:
    print(f"[WARNING] Error setting up 8x8 LED matrix import: {e}")
    import traceback
    traceback.print_exc()
    LEDMATRIX_AVAILABLE = False
    LedMatrix8x8 = None

# Global hardware objects
oled_display = None
analogue_keypad = None
pot_adc = None  # Potentiometer ADC
POT_AVAILABLE = False
led_matrix = None  # 8x8 LED Matrix

def init_oled():
    """Initialize OLED display - Slot 1 (I2C) - using same pattern as WebServer.py"""
    global oled_display
    print("[OLED] Initializing OLED display (Slot 1 - I2C)...")
    
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
    """Initialize 8x8 LED Matrix (Slot 3 - SPI)"""
    global led_matrix
    print("[LEDMATRIX] Initializing 8x8 LED matrix (Slot 3 - SPI)...")
    
    if not LEDMATRIX_AVAILABLE:
        print("[LEDMATRIX] 8x8 LED matrix library not available - matrix disabled")
        return
    
    try:
        # Use same pattern as OLED: lazy_hw=True, then open()
        # Slot 3 SPI configuration: CS=P9_17, SCK=P9_22, MISO=P9_29, MOSI=P9_18
        # These pins correspond to SPI0 (bus 0) on BeagleBone
        print("[LEDMATRIX] Creating LedMatrix8x8 with lazy_hw=True...")
        print("[LEDMATRIX] Slot 3 SPI pins: CS=P9_17, SCK=P9_22, MISO=P9_29, MOSI=P9_18")
        led_matrix = LedMatrix8x8(bus=0, device=0, lazy_hw=True)  # SPI0, device 0
        print("[LEDMATRIX] Calling open()...")
        led_matrix.open()
        print("[LEDMATRIX] 8x8 LED matrix initialized successfully")
        
        # Test display with a simple pattern
        led_matrix.set_preset("smiley")
        time.sleep(0.5)
        led_matrix.clear()
    except Exception as e:
        print(f"[LEDMATRIX] Error initializing 8x8 LED matrix: {e}")
        print(f"[LEDMATRIX] Error details: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        led_matrix = None

def init_buttons():
        """Initialize Analog Key Click (6 buttons via AnalogueKeypad) - Slot 4 (ADC)"""
        global analogue_keypad
        print("[BUTTONS] Initializing analogue keypad (6 buttons) - Slot 4 (ADC)...")
        
        if not KEYPAD_AVAILABLE:
            print("[BUTTONS] Analogue keypad library not available - buttons disabled")
            return
        
        try:
            # Use same pattern as OLED: lazy_hw=True, then open()
            # Slot 4 ADC pin: P9_39
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
            print("[BUTTONS] Slot 4 ADC pin: P9_39")
            analogue_keypad = AnalogueKeypad(pin="P9_39", lazy_hw=True, thresholds=thresholds, debounce_ms=50)
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
    """Initialize potentiometer on P9_37 (Slot 2 ADC) for scrolling control"""
    global pot_adc, POT_AVAILABLE
    print("[POT] Initializing potentiometer (P9_37, Slot 2 ADC) for scrolling...")
    
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
    
    Maps actual pot range (0.0-0.545) to full range (0.0-1.0)
    Returns: (mapped_value, raw_value) tuple for debugging
    """
    global pot_adc, POT_AVAILABLE
    
    if not POT_AVAILABLE or not pot_adc:
        return (0.0, 0.0)
    
    try:
        raw_digital = pot_adc.read("P9_37")
        raw_voltage = raw_digital * 1.8
        
        # Map pot range (0.0-0.545) to full range (0.0-1.0)
        # Pot range is from 0.0 to 0.545, so map it so 0.0 -> 0.0 and 0.545 -> 1.0
        POT_MIN = 0.0   # Minimum value the pot actually reaches
        POT_MAX = 0.545  # Maximum value the pot reaches
        
        if raw_digital <= POT_MIN:
            mapped_value = 0.0
        elif raw_digital >= POT_MAX:
            mapped_value = 1.0
        else:
            # Linear mapping: (value - min) / (max - min)
            mapped_value = (raw_digital - POT_MIN) / (POT_MAX - POT_MIN)
        
        return (mapped_value, raw_digital)  # Returns (mapped 0.0-1.0, raw 0.0-0.545)
    except Exception as e:
        print(f"[POT] Error reading potentiometer: {e}")
        return (0.0, 0.0)

# def init_buzz():
#     """Initialize Buzz 2 Click - NOT AVAILABLE"""
#     print("[BUZZ] Buzzer not available - skipping")
#     pass

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
        """Display 'Connecting...' message on OLED and loading animation on 8x8 matrix"""
        global oled_display, led_matrix
        if oled_display:
            try:
                oled_display.clear()  # clear() calls show()
                oled_display.draw_centered_text("Connecting", 8)  # draw_centered_text() calls show()
                oled_display.draw_centered_text("...", 20)  # draw_centered_text() calls show()
                # No need to call show() again - draw_centered_text() already does it
            except Exception as e:
                print(f"[OLED] Error showing connecting: {e}")
        
        # Show loading animation on 8x8 LED matrix
        if led_matrix:
            try:
                # Start a spinning loading animation
                show_matrix_loading()
            except Exception as e:
                print(f"[LEDMATRIX] Error showing loading: {e}")

# Global variable to control loading animation
_loading_animation_active = False
_loading_thread = None

def show_matrix_loading():
        """Display a spinning loading animation on 8x8 LED matrix"""
        global led_matrix, _loading_animation_active, _loading_thread
        if not led_matrix:
            return
        
        try:
            # Stop any existing animation
            stop_matrix_loading()
            
            # Create a spinning pattern - rotating around the center
            spinning_patterns = [
                # Rotating cross pattern (4 frames)
                [0b00000000, 0b00000000, 0b00011000, 0b00011000, 0b00011000, 0b00011000, 0b00000000, 0b00000000],  # |
                [0b00000000, 0b00000000, 0b00001100, 0b00001100, 0b00110000, 0b00110000, 0b00000000, 0b00000000],  # /
                [0b00000000, 0b00000000, 0b00111100, 0b00000000, 0b00000000, 0b00111100, 0b00000000, 0b00000000],  # -
                [0b00000000, 0b00000000, 0b00110000, 0b00110000, 0b00001100, 0b00001100, 0b00000000, 0b00000000],  # \
            ]
            
            def loading_animation():
                """Animate a spinning loading pattern"""
                global _loading_animation_active
                frame = 0
                while _loading_animation_active:
                    try:
                        pattern = spinning_patterns[frame % len(spinning_patterns)]
                        if led_matrix:
                            led_matrix.set_pattern(pattern)
                        frame += 1
                        time.sleep(0.2)  # 200ms per frame
                    except:
                        break
            
            # Start animation in background thread
            _loading_animation_active = True
            _loading_thread = threading.Thread(target=loading_animation, daemon=True)
            _loading_thread.start()
            print("[LEDMATRIX] Loading animation started")
        except Exception as e:
            print(f"[LEDMATRIX] Error starting loading animation: {e}")

def stop_matrix_loading():
        """Stop the loading animation on 8x8 LED matrix"""
        global led_matrix, _loading_animation_active, _loading_thread
        try:
            _loading_animation_active = False
            if _loading_thread and _loading_thread.is_alive():
                # Wait a bit for thread to stop
                time.sleep(0.3)
            if led_matrix:
                led_matrix.clear()
            print("[LEDMATRIX] Loading animation stopped")
        except Exception as e:
            print(f"[LEDMATRIX] Error stopping loading animation: {e}")

def show_connected():
        """Display 'Connected' message on OLED and stop loading animation on 8x8 matrix"""
        global oled_display
        if oled_display:
            try:
                oled_display.clear()  # clear() calls show()
                oled_display.draw_centered_text("Connected", 8)  # draw_centered_text() calls show()
                oled_display.draw_centered_text("Waiting...", 20)  # draw_centered_text() calls show()
                # No need to call show() again - draw_centered_text() already does it
            except Exception as e:
                print(f"[OLED] Error showing connected: {e}")
        
        # Stop loading animation and show checkmark briefly
        stop_matrix_loading()
        if led_matrix:
            try:
                # Show checkmark to indicate successful connection
                led_matrix.set_preset("check")
                time.sleep(0.5)
                led_matrix.clear()
            except Exception as e:
                print(f"[LEDMATRIX] Error showing connected indicator: {e}")

def show_connection_error():
        """Display connection error on OLED and stop loading animation on 8x8 matrix"""
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
        
        # Stop loading animation and show X to indicate error
        stop_matrix_loading()
        if led_matrix:
            try:
                # Show X to indicate connection error
                led_matrix.set_preset("x")
            except Exception as e:
                print(f"[LEDMATRIX] Error showing error indicator: {e}")

def update_oled_display(view, data):
        """Update OLED display and 8x8 LED matrix with current view"""
        global oled_display, last_oled_update_time, oled_update_lock
        
        if not data:
            print("[OLED] No data to display")
            return
        
        if not oled_display:
            print("[OLED] OLED display not initialized - skipping update")
        else:
            print(f"[OLED] Updating view: {view}, OLED available: {oled_display is not None}")
        
        # Use lock to prevent concurrent updates
        with oled_update_lock:
            # Debounce: prevent rapid updates (minimum 100ms between updates)
            current_time = time.time() * 1000  # Convert to milliseconds
            time_since_last_update = current_time - last_oled_update_time
            if time_since_last_update < OLED_UPDATE_DEBOUNCE_MS:
                # Too soon, skip this update
                print(f"[OLED] Update debounced (last update {time_since_last_update:.1f}ms ago)")
                return
            
            last_oled_update_time = current_time
            
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
        
        # Also update 8x8 LED matrix (outside the lock to avoid blocking)
        # Pass scroll offset for scrolling views (today pattern and alternatives)
        scroll_offset = 0
        if view == 'history_today':
            # Calculate scroll offset same way as in show_today_pattern
            patterns = data.get('patterns', {})
            hourly = patterns.get('today_hourly', [])
            pot_value, _ = read_potentiometer()
            max_items = len(hourly)
            max_scroll = max(0, max_items - 3)
            scroll_offset = int(pot_value * max_scroll)
        elif view == 'alternatives':
            # Calculate scroll offset same way as in show_alternatives
            recommendations = data.get('recommendations', {})
            alternatives = recommendations.get('nearby_alternatives', [])
            pot_value, _ = read_potentiometer()
            max_items = len(alternatives)
            max_scroll = max(0, max_items - 1)
            scroll_offset = int(pot_value * max_scroll)
        update_led_matrix(view, data, scroll_offset)

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
                
                # Show once at the end - add small delay to ensure display is ready
                time.sleep(0.01)  # 10ms delay before show()
                oled_display.show()
                time.sleep(0.01)  # 10ms delay after show() to ensure update completes
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
                
                # Show once at the end - add small delay to ensure display is ready
                time.sleep(0.01)  # 10ms delay before show()
                oled_display.show()
                time.sleep(0.01)  # 10ms delay after show() to ensure update completes
            except Exception as e:
                print(f"[OLED] Error drawing pattern: {e}")
        
        # Also print to console with real hourly data
        recommendations = data.get('recommendations', {})
        best_times = recommendations.get('best_times_today', [])
        avoid_times = recommendations.get('avoid_times', [])
        
        # Build pattern display from actual hourly data
        pattern_lines = []
        current_hour = datetime.now().hour
        for hour_data in hourly[:8]:  # Show first 8 hours
            hour_24 = hour_data.get('hour', 0)
            occ = hour_data.get('occupancy', 0)
            
            # Convert to 12-hour format
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
            
            # Determine level
            if occ >= 0.8:
                level = "Full"
                bars = "█████"
            elif occ >= 0.6:
                level = "Busy"
                bars = "████░"
            elif occ >= 0.4:
                level = "Normal"
                bars = "███░░"
            elif occ >= 0.2:
                level = "Light"
                bars = "██░░░"
            else:
                level = "Empty"
                bars = "░░░░░"
            
            marker = " ←" if hour_24 == current_hour else ""
            pattern_lines.append(f"│ {hour_12:2d}{am_pm}  {bars} {level:<7}{marker}│")
        
        pattern_display = "\n".join(pattern_lines)
        best_times_text = ", ".join(best_times[:2]) if best_times else "N/A"
        avoid_times_text = ", ".join(avoid_times[:1]) if avoid_times else "None"
        
        print(f"""
        ┌─────────────────────┐
        │ TODAY'S PATTERN     │
        │ ═══════════════════ │
        │                     │
{pattern_display}
        │                     │
        │ 💡 Best: {best_times_text[:15]:<15}│
        │ ⚠ Avoid: {avoid_times_text[:15]:<15}│
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
                
                # Show once at the end - add small delay to ensure display is ready
                time.sleep(0.01)  # 10ms delay before show()
                oled_display.show()
                time.sleep(0.01)  # 10ms delay after show() to ensure update completes
            except Exception as e:
                print(f"[OLED] Error drawing weekly: {e}")
        
        # Also print to console with real weekly data
        current_hour = datetime.now().hour
        current_day = datetime.now().strftime('%a')
        
        # Build weekly display from actual data
        weekly_lines = []
        for day_data in weekly:
            day_name = day_data.get('day', '')[:3]  # Mon, Tue, etc
            occ = day_data.get('occupancy', 0)
            occ_percent = int(occ * 100)
            
            # Visual bars (5 bars)
            bars = int(occ * 5)
            bar_display = "█" * bars + "░" * (5 - bars)
            
            marker = " ←" if day_name.upper() == current_day.upper()[:3] else ""
            weekly_lines.append(f"│ {day_name:<3}  {bar_display} {occ_percent:2d}%{marker:<6}│")
        
        weekly_display = "\n".join(weekly_lines)
        
        # Find quietest day
        quietest_day = min(weekly, key=lambda x: x.get('occupancy', 1.0))
        quietest_name = quietest_day.get('day', 'Unknown')
        
        print(f"""
        ┌─────────────────────┐
        │ THIS TIME WEEKLY    │
        │ ═══════════════════ │
        │ {current_hour}:00 Comparison:     │
        │                     │
{weekly_display}
        │                     │
        │ 💡 {quietest_name} quietest!      │
        │ Press [1] for now → │
        └─────────────────────┘
        """)

def show_weather_details(data):
    """Display View 3: Weather Details"""
    global oled_display
    
    weather = data.get('weather', {})
    recommendations = data.get('recommendations', {})
    
    temp = weather.get('temp_c', 0)
    humidity = weather.get('humidity_percent', 0)
    uv = weather.get('uv_index', 0)
    comfort = weather.get('comfort_score', 0)
    air_quality = weather.get('voc_level', 'unknown')  # Air quality from server
    warnings = weather.get('warnings', [])  # Warnings from server
    weather_tips = weather.get('recommendations', [])  # Tips from server
    best_times = recommendations.get('best_times_today', [])  # Best times from recommendations
    
    # UV level description
    if uv >= 8:
        uv_desc = "Very High"
    elif uv >= 6:
        uv_desc = "High"
    elif uv >= 3:
        uv_desc = "Moderate"
    else:
        uv_desc = "Low"
    
    # Air quality display
    aq_display = air_quality.upper() if isinstance(air_quality, str) else "Unknown"
    aq_icon = "✓" if air_quality in ['good', 'excellent'] else "⚠" if air_quality in ['moderate', 'fair'] else "✗"
    
    # Comfort bar visualization (5 bars)
    comfort_bars = int(comfort)
    bar_display = "█" * comfort_bars + "░" * (5 - comfort_bars)
    
    # Draw on OLED - Page 4: Weather (compact, 3 lines)
    if oled_display:
        try:
            # Batch all drawing operations, then show() once to avoid corruption
            if oled_display._draw is None:
                oled_display.open()
            oled_display._draw.rectangle((0, 0, OLED_WIDTH - 1, OLED_HEIGHT - 1), outline=0, fill=0)
            
            # Line 1: Title
            oled_display._draw.text((0, 0), "WEATHER", font=oled_display._font, fill=1)
            # Line 2: Temperature and Humidity
            oled_display._draw.text((0, 8), f"T:{temp}C H:{humidity}%", font=oled_display._font, fill=1)
            # Line 3: UV and Comfort (compact to fit)
            oled_display._draw.text((0, 16), f"UV:{uv} C:{comfort}/5", font=oled_display._font, fill=1)
            # Line 4: Air Quality (if OLED_HEIGHT >= 32, which it is - 64x32)
            aq_short = aq_display[:4] if len(aq_display) > 4 else aq_display
            oled_display._draw.text((0, 24), f"AQ:{aq_short}", font=oled_display._font, fill=1)
            
            # Show once at the end - add small delay to ensure display is ready
            time.sleep(0.01)  # 10ms delay before show()
            oled_display.show()
            time.sleep(0.01)  # 10ms delay after show() to ensure update completes
        except Exception as e:
            print(f"[OLED] Error drawing weather: {e}")
    
    # Also print to console with real data
    warning_text = ", ".join(warnings) if warnings else "None"
    tips_text = " • ".join(weather_tips[:3]) if weather_tips else "None"
    best_times_text = ", ".join(best_times[:2]) if best_times else "N/A"
    
    print(f"""
        ┌─────────────────────┐
        │ WEATHER CONDITIONS  │
        │ ═══════════════════ │
        │ Temp: {temp}°C ☀️       │
        │ Humidity: {humidity}%       │
        │ UV: {uv} ({uv_desc})⚠️ │
        │ Air Quality: {aq_display} {aq_icon} │
        │                     │
        │ Comfort: {comfort}/5        │
        │ [Bar: {bar_display}]  │
        │                     │
        │ Warnings: {warning_text[:18]:<18}│
        │ Tips: {tips_text[:18]:<19}│
        │ Best: {best_times_text[:18]:<19}│
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
            
            # Show once at the end - add small delay to ensure display is ready
            time.sleep(0.01)  # 10ms delay before show()
            oled_display.show()
            time.sleep(0.01)  # 10ms delay after show() to ensure update completes
        except Exception as e:
            print(f"[OLED] Error drawing alternatives: {e}")
    
        # Also print to console with real alternatives data
        current = data.get('current', {})
        current_level = current.get('crowd_level', 'unknown')
        current_people = current.get('people_count', 0)
        
        # Level emoji
        level_emoji = get_level_emoji(current_level)
        
        # Build alternatives display
        if alternatives:
            alt_lines = []
            for alt in alternatives[:3]:  # Show up to 3 alternatives
                alt_name = alt.get('name', 'Court')
                alt_distance = alt.get('distance_m', 0)
                alt_people = alt.get('people', 0)
                alt_status = alt.get('status', 'unknown')
                alt_emoji = get_level_emoji(alt_status)
                
                alt_lines.append(f"│ {alt_name} ({alt_distance}m)    │")
                alt_lines.append(f"│ → {alt_emoji} {alt_status.title()} ({alt_people} ppl)  │")
                alt_lines.append("│                     │")
            
            alt_display = "\n".join(alt_lines)
            
            # Find best alternative (lowest occupancy)
            if alternatives:
                best_alt = min(alternatives, key=lambda x: x.get('occupancy', 1.0))
                best_name = best_alt.get('name', 'Unknown')
            else:
                best_name = "None"
        else:
            alt_display = "│ No alternatives      │\n│ available             │"
            best_name = "None"
        
        print(f"""
        ┌─────────────────────┐
        │ OTHER COURTS NEARBY │
        │ ═══════════════════ │
        │                     │
        │ THIS: {level_emoji} {current_level.upper():<6} ({current_people})   │
        │                     │
{alt_display}
        │ 💡 {best_name} best now!    │
        │                     │
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
            
            # Show once at the end - add small delay to ensure display is ready
            time.sleep(0.01)  # 10ms delay before show()
            oled_display.show()
            time.sleep(0.01)  # 10ms delay after show() to ensure update completes
        except Exception as e:
            print(f"[OLED] Error drawing info: {e}")
    
    # Also print to console with real data
    court_name = info.get('court_name', 'Court')
    size = info.get('size', 'Full court')
    capacity = info.get('capacity', 'N/A')
    rating_count = info.get('rating_count', 0)
    last_cleaned = info.get('last_cleaned', 'Unknown')
    
    # Format facilities list
    facilities_display = []
    if facilities:
        for facility in facilities[:4]:  # Show up to 4
            # Format facility name nicely
            facility_name = facility.replace('_', ' ').title()
            facilities_display.append(f"│ ✓ {facility_name:<17}│")
    else:
        facilities_display.append("│ ✓ None listed        │")
    
    facilities_text = "\n".join(facilities_display)
    
    # Format last cleaned
    if isinstance(last_cleaned, str):
        if last_cleaned.lower() == 'today':
            cleaned_display = "Today"
        elif 'T' in last_cleaned:  # ISO format
            try:
                cleaned_dt = datetime.fromisoformat(last_cleaned.replace('Z', '+00:00'))
                cleaned_display = cleaned_dt.strftime("%b %d, %I%p")
            except:
                cleaned_display = last_cleaned[:10]
        else:
            cleaned_display = last_cleaned[:15]
    else:
        cleaned_display = str(last_cleaned)[:15]
    
    print(f"""
        ┌─────────────────────┐
        │ COURT INFORMATION   │
        │ ═══════════════════ │
        │ {court_name[:20]:<20}│
        │                     │
        │ Surface: {surface:<12}│
        │ Lights: {lights:<13}│
        │ Size: {size:<15}│
        │ Capacity: {capacity:<11}│
        │                     │
        │ FACILITIES:         │
{facilities_text}
        │                     │
        │ Rating: {'⭐' * int(rating)} ({rating:.1f})│
        │ Reviews: {rating_count:<13}│
        │ Cleaned: {cleaned_display:<13}│
        └─────────────────────┘
        """)

# ========== 8x8 LED MATRIX VISUALIZATIONS ==========

def show_matrix_status(data):
    """Display crowd level on 8x8 matrix for Status view"""
    global led_matrix
    if not led_matrix:
        return
    
    try:
        current = data.get('current', {})
        level = current.get('crowd_level', 'unknown').lower()
        occupancy = current.get('occupancy', 0)
        
        # Create pattern based on crowd level
        # Show vertical bars representing occupancy (0-100%)
        pattern = [0] * 8
        bars = int(occupancy * 8)  # 0-8 bars
        
        # Fill from bottom up (row 7 is bottom)
        for row in range(7, 7 - bars, -1):
            if row >= 0:
                # Fill entire row (all 8 columns)
                pattern[row] = 0xFF
        
        # Add level indicator: different patterns for different levels
        if level == 'empty':
            # Green - show checkmark
            led_matrix.set_preset("check")
        elif level == 'light':
            # Yellow - show 1-2 bars
            led_matrix.set_pattern(pattern)
        elif level == 'normal':
            # Orange - show 3-4 bars
            led_matrix.set_pattern(pattern)
        elif level == 'busy':
            # Red - show 5-6 bars
            led_matrix.set_pattern(pattern)
        elif level == 'full':
            # Red - show full or X
            led_matrix.set_preset("x")
        else:
            # Unknown - show pattern based on occupancy
            led_matrix.set_pattern(pattern)
    except Exception as e:
        print(f"[LEDMATRIX] Error showing status: {e}")

def show_matrix_today_pattern(data, scroll_offset=0):
    """Display hourly occupancy pattern on 8x8 matrix for Today view
    
    Args:
        data: Display data containing patterns
        scroll_offset: Offset into the hourly array to show (for scrolling with OLED)
    """
    global led_matrix
    if not led_matrix:
        return
    
    try:
        patterns = data.get('patterns', {})
        hourly = patterns.get('today_hourly', [])
        
        # Show 8 hours as 8 vertical bars (one column per hour)
        # Each bar height represents occupancy (0-100%)
        pattern = [0] * 8
        
        # Get 8 hours starting from scroll_offset (to match OLED scrolling)
        for col in range(8):  # 8 columns
            idx = scroll_offset + col
            if idx < len(hourly):
                hour_data = hourly[idx]
                occupancy = hour_data.get('occupancy', 0)
                bars = int(occupancy * 8)  # 0-8 bars high
                
                # Set bits from bottom up for this column
                # Column col (0-7) maps to bit position (7-col) in each row
                bit_pos = 7 - col
                for row in range(7, 7 - bars, -1):
                    if row >= 0:
                        pattern[row] |= (1 << bit_pos)
        
        led_matrix.set_pattern(pattern)
    except Exception as e:
        print(f"[LEDMATRIX] Error showing today pattern: {e}")

def show_matrix_weekly_comparison(data):
    """Display weekly comparison on 8x8 matrix for Weekly view"""
    global led_matrix
    if not led_matrix:
        return
    
    try:
        patterns = data.get('patterns', {})
        weekly = patterns.get('week_same_time', [])
        
        # Show 7 days as 7 vertical bars (one column per day, skip column 0 or 7)
        # Each bar height represents occupancy (0-100%)
        pattern = [0] * 8
        
        # Map 7 days to 7 columns (columns 1-7, skip 0)
        for day_idx in range(min(7, len(weekly))):
            col = day_idx + 1  # Columns 1-7
            day_data = weekly[day_idx]
            occupancy = day_data.get('occupancy', 0)
            bars = int(occupancy * 8)  # 0-8 bars high
            
            # Set bits from bottom up for this column
            bit_pos = 7 - col
            for row in range(7, 7 - bars, -1):
                if row >= 0:
                    pattern[row] |= (1 << bit_pos)
        
        led_matrix.set_pattern(pattern)
    except Exception as e:
        print(f"[LEDMATRIX] Error showing weekly comparison: {e}")

def show_matrix_weather(data):
    """Display weather indicator on 8x8 matrix for Weather view"""
    global led_matrix
    if not led_matrix:
        return
    
    try:
        weather = data.get('weather', {})
        temp = weather.get('temp_c', 20)
        uv = weather.get('uv_index', 0)
        comfort = weather.get('comfort_score', 0)
        
        # Show weather icon based on conditions
        # Temperature indicator: show as bars (cold = few bars, hot = many bars)
        # Or show sun icon for good weather, cloud for bad
        
        if temp > 25 and uv > 5:
            # Hot and sunny - show sun (filled circle)
            led_matrix.set_preset("circle")
        elif temp < 10:
            # Cold - show arrow down
            led_matrix.set_preset("arrow_down")
        elif comfort >= 4:
            # Good comfort - show smiley
            led_matrix.set_preset("smiley")
        elif comfort <= 2:
            # Poor comfort - show sad
            led_matrix.set_preset("sad")
        else:
            # Moderate - show temperature as bars
            # Map temp (0-40C) to 0-8 bars
            bars = int((temp / 40.0) * 8)
            bars = max(1, min(8, bars))  # Clamp to 1-8
            pattern = [0] * 8
            for row in range(7, 7 - bars, -1):
                if row >= 0:
                    pattern[row] = 0xFF
            led_matrix.set_pattern(pattern)
    except Exception as e:
        print(f"[LEDMATRIX] Error showing weather: {e}")

def show_matrix_alternatives(data, scroll_offset=0):
    """Display alternatives indicator on 8x8 matrix for Alternatives view
    
    Shows different patterns based on the currently selected alternative's recommendation level:
    - Empty/Light: Checkmark or smiley (good choice)
    - Normal: Circle or moderate bars
    - Busy: Warning pattern or busy indicator
    - Full: X (not recommended)
    
    Args:
        data: Display data containing recommendations
        scroll_offset: Index of currently selected alternative
    """
    global led_matrix
    if not led_matrix:
        return
    
    try:
        recommendations = data.get('recommendations', {})
        alternatives = recommendations.get('nearby_alternatives', [])
        
        # Show indicator based on alternatives
        if len(alternatives) == 0:
            # No alternatives - show X
            led_matrix.set_preset("x")
        else:
            # Get the currently selected alternative based on scroll_offset
            if scroll_offset < len(alternatives):
                alt = alternatives[scroll_offset]
                status = alt.get('status', 'unknown').lower()
                occupancy = alt.get('occupancy', 1.0)
                people = alt.get('people', 0)
                
                # Show different patterns based on recommendation level
                if status == 'empty' or (occupancy <= 0.2 and people == 0):
                    # Excellent - show checkmark (best choice)
                    led_matrix.set_preset("check")
                elif status == 'light' or (occupancy <= 0.4 and people <= 2):
                    # Good - show smiley (recommended)
                    led_matrix.set_preset("smiley")
                elif status == 'normal' or (occupancy <= 0.6 and people <= 5):
                    # Moderate - show circle (acceptable)
                    led_matrix.set_preset("circle")
                elif status == 'busy' or (occupancy <= 0.8 and people <= 7):
                    # Busy - show diamond (not ideal)
                    led_matrix.set_preset("diamond")
                elif status == 'full' or occupancy >= 0.8 or people >= 8:
                    # Full - show X (not recommended)
                    led_matrix.set_preset("x")
                else:
                    # Unknown - show occupancy as bars
                    bars = int(occupancy * 8)
                    bars = max(1, min(8, bars))
                    pattern = [0] * 8
                    for row in range(7, 7 - bars, -1):
                        if row >= 0:
                            pattern[row] = 0xFF
                    led_matrix.set_pattern(pattern)
            else:
                # Invalid scroll offset - show arrow right
                led_matrix.set_preset("arrow_right")
    except Exception as e:
        print(f"[LEDMATRIX] Error showing alternatives: {e}")

def show_matrix_info(data):
    """Display info indicator on 8x8 matrix for Info view"""
    global led_matrix
    if not led_matrix:
        return
    
    try:
        info = data.get('info', {})
        rating = info.get('rating_avg', 0)
        
        # Show info icon - use circle or diamond
        # Or show rating as stars (1-5 stars as bars)
        if rating >= 4.5:
            # Excellent - show heart
            led_matrix.set_preset("heart")
        elif rating >= 3.5:
            # Good - show circle
            led_matrix.set_preset("circle")
        elif rating >= 2.5:
            # Fair - show diamond
            led_matrix.set_preset("diamond")
        else:
            # Poor - show square
            led_matrix.set_preset("square")
    except Exception as e:
        print(f"[LEDMATRIX] Error showing info: {e}")

def update_led_matrix(view, data, scroll_offset=0):
    """Update 8x8 LED matrix based on current view
    
    Args:
        view: Current view name
        data: Display data
        scroll_offset: Scroll offset for scrolling views (e.g., today pattern)
    """
    global led_matrix
    
    if not led_matrix or not data:
        return
    
    try:
        if view == 'status':
            show_matrix_status(data)
        elif view == 'history_today':
            show_matrix_today_pattern(data, scroll_offset)
        elif view == 'history_week':
            show_matrix_weekly_comparison(data)
        elif view == 'weather':
            show_matrix_weather(data)
        elif view == 'alternatives':
            show_matrix_alternatives(data, scroll_offset)
        elif view == 'info':
            show_matrix_info(data)
        else:
            # Unknown view - clear matrix
            led_matrix.clear()
    except Exception as e:
        print(f"[LEDMATRIX] Error updating matrix: {e}")
        import traceback
        traceback.print_exc()

def update_bar_graph(data):
    """Update Bar Graph 2 Click or 8x8 LED Matrix with hourly pattern
    
    Note: This function is kept for compatibility but now uses update_led_matrix()
    """
    # Delegate to update_led_matrix with current view
    if current_view and current_data:
        update_led_matrix(current_view, current_data)

def buzz_beep(count=1):
    """Play buzzer beep - NOT AVAILABLE (buzzer not connected)"""
    # Buzzer not available - just log for debugging
    # print(f"[BUZZ] Beep x{count} (buzzer not available)")
    pass

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
        
        # Update OLED and 8x8 LED matrix based on current view
        # (update_oled_display now also calls update_led_matrix internally)
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
        init_bar_graph()  # Initialize 8x8 LED matrix (Slot 3)
        # init_buzz()        # Not available - buzzer not connected
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
        if led_matrix:
            print("[OK] 8x8 LED matrix initialized successfully (Slot 3)")
        else:
            print("[WARNING] 8x8 LED matrix not initialized - matrix disabled")
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
        if led_matrix:
            try:
                led_matrix.close()
                print("[LEDMATRIX] 8x8 LED matrix closed")
            except Exception as e:
                print(f"[LEDMATRIX] Error closing matrix: {e}")
        print("Client disconnected. Goodbye!")

if __name__ == '__main__':
    main()

