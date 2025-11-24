"""
BBBW Web Client for Lab 5b
Connects to Flask-SocketIO server and sends Pot Click sensor readings
"""
import socketio
import time
import sys
from datetime import datetime
import uuid

# Configuration
SERVER_URL = 'http://192.168.7.1:5000'
CLIENT_ID = f'bbbw_{uuid.uuid4().hex[:8]}'
SENSOR_READ_INTERVAL = 0.5  # Read sensor every 0.5 seconds

# Create Socket.IO client
sio = socketio.Client()

# Global state
is_reading = False
reading_active = False

def read_pot_click_sensor():
    """
    Read Pot Click sensor value from ADC
    
    This function tries multiple methods to read the ADC:
    1. First tries sysfs method (no extra libraries needed)
    2. Falls back to Adafruit_BBIO if available
    3. Returns simulated value if neither works (for testing)
    
    To customize:
    - If using sysfs: Check which ADC channel your Pot Click is on
      (usually AIN0 = in_voltage0_raw, AIN1 = in_voltage1_raw, etc.)
    - If using Adafruit_BBIO: Change the pin name (P9_39 = AIN0, P9_40 = AIN1, etc.)
    """
    # Method 1: Try sysfs (Linux kernel ADC interface) - RECOMMENDED
    # Note: P9_37 = AIN2 = in_voltage2_raw (based on pot.py)
    try:
        # Try P9_37 first (AIN2) since that's what pot.py uses
        adc_paths = [
            '/sys/bus/iio/devices/iio:device0/in_voltage2_raw',  # AIN2 (P9_37) - Pot Click
            '/sys/bus/iio/devices/iio:device0/in_voltage0_raw',  # AIN0 (P9_39)
            '/sys/bus/iio/devices/iio:device0/in_voltage1_raw',  # AIN1 (P9_40)
            '/sys/bus/iio/devices/iio:device0/in_voltage3_raw',  # AIN3 (P9_38)
        ]
        
        for path in adc_paths:
            try:
                with open(path, 'r') as f:
                    raw_value = f.read().strip()
                    if raw_value:  # Check if file has content
                        value = int(raw_value)
                        # Read scale to convert properly
                        try:
                            scale_path = path.replace('_raw', '_scale')
                            with open(scale_path, 'r') as scale_f:
                                scale = float(scale_f.read().strip())
                                # Scale is typically 0.001 (mV to V conversion factor)
                                # Raw value is 0-4095, scale converts to voltage
                                # But we want raw 0-4095 value, so just return int
                        except:
                            pass  # Use raw value if scale not available
                        
                        print(f"[DEBUG] Read from {path}: {value}")
                        return value
            except (FileNotFoundError, IOError, ValueError) as e:
                print(f"[DEBUG] Failed to read {path}: {e}")
                continue
    except Exception as e:
        print(f"[DEBUG] Sysfs method error: {e}")
        pass  # Try next method
    
    # Method 2: Try Adafruit_BBIO library (if installed)
    try:
        import Adafruit_BBIO.ADC as ADC
        ADC.setup()
        # Try P9_37 first (based on pot.py), then others
        pins_to_try = ["P9_37", "P9_39", "P9_40", "P9_38"]
        for pin in pins_to_try:
            try:
                value = ADC.read(pin)  # Returns 0.0 to 1.0
                raw_value = int(value * 4095)
                print(f"[DEBUG] Read from {pin}: raw_value={raw_value}, ADC_value={value:.4f}")
                # Return the value even if 0, so we can see what's happening
                return raw_value
            except Exception as e:
                print(f"[DEBUG] Failed to read {pin}: {e}")
                continue
        # If all pins failed, try one more time with P9_37
        value = ADC.read("P9_37")
        raw_value = int(value * 4095)
        print(f"[DEBUG] Final attempt with P9_37: {raw_value}")
        return raw_value
    except ImportError:
        print("[DEBUG] Adafruit_BBIO not available")
        pass  # Try next method
    except Exception as e:
        print(f"[DEBUG] Adafruit_BBIO error: {e}")
        pass  # Try next method
    
    # Method 3: Fallback - simulated value (for testing without hardware)
    # Remove this and add proper error handling once hardware is connected
    import random
    fallback_value = random.randint(100, 4000)  # Use non-zero range for testing
    print(f"[DEBUG] Using fallback simulated value: {fallback_value}")
    return fallback_value

@sio.event
def connect():
    """Called when connected to server"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Connected to server at {SERVER_URL}")
    
    # Register this BBBW client
    sio.emit('bbbw_connect', {
        'client_id': CLIENT_ID,
        'board_type': 'BBBW',
        'timestamp': datetime.now().isoformat()
    })

@sio.event
def disconnect():
    """Called when disconnected from server"""
    global reading_active
    reading_active = False
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Disconnected from server")

@sio.event
def bbbw_ack(data):
    """Acknowledgment from server"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Server acknowledgment: {data.get('message', '')}")

@sio.event
def bbbw_command(data):
    """Receive control command from server"""
    global is_reading, reading_active
    command = data.get('command', '').lower()
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Received command: {command}")
    
    if command == 'start':
        is_reading = True
        reading_active = True
        print("Starting sensor readings...")
        start_sensor_reading()
    elif command == 'stop':
        is_reading = False
        reading_active = False
        print("Stopping sensor readings...")
    elif command == 'reset':
        is_reading = False
        reading_active = False
        print("Reset command received")
    else:
        print(f"Unknown command: {command}")

def start_sensor_reading():
    """Start reading sensor and sending data to server"""
    global is_reading, reading_active
    
    while reading_active and is_reading:
        try:
            # Read Pot Click sensor
            pot_value = read_pot_click_sensor()
            
            # Send sensor data to server
            sio.emit('sensor_data', {
                'client_id': CLIENT_ID,
                'pot_value': pot_value,
                'timestamp': datetime.now().isoformat()
            })
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Sent sensor data: Pot = {pot_value}")
            
            # Wait before next reading
            time.sleep(SENSOR_READ_INTERVAL)
            
        except KeyboardInterrupt:
            print("\nStopping sensor readings...")
            reading_active = False
            is_reading = False
            break
        except Exception as e:
            print(f"Error reading sensor: {e}")
            time.sleep(SENSOR_READ_INTERVAL)

def main():
    """Main function"""
    global reading_active
    
    print("=" * 50)
    print("Lab 5b: BBBW Web Client")
    print("=" * 50)
    print(f"Client ID: {CLIENT_ID}")
    print(f"Server URL: {SERVER_URL}")
    print(f"Sensor Read Interval: {SENSOR_READ_INTERVAL}s")
    print("=" * 50)
    
    try:
        # Connect to server
        print(f"Connecting to server at {SERVER_URL}...")
        sio.connect(SERVER_URL)
        
        # Keep connection alive and handle commands
        print("Connected! Waiting for commands from server...")
        print("Send 'start' command from web interface to begin reading sensor.")
        print("Press Ctrl+C to exit")
        
        # Keep the script running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    except socketio.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
        print("Make sure the server is running and the URL is correct.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if sio.connected:
            sio.emit('bbbw_disconnect', {
                'client_id': CLIENT_ID,
                'timestamp': datetime.now().isoformat()
            })
            sio.disconnect()
        print("Client disconnected. Goodbye!")

if __name__ == '__main__':
    main()

