import time
from Adafruit_BBIO.SPI import SPI
import Adafruit_BBIO.GPIO as GPIO
import board
import adafruit_bme680
import adafruit_veml6070
import busio
import digitalio
import adafruit_ssd1306
from board import SCL, SDA
from PIL import Image, ImageDraw, ImageFont

# Socket.IO for server communication
import socketio
from datetime import datetime

# ========== CONFIGURATION ==========
SERVER_URL = 'http://192.168.72.161:5000'  # CHANGE THIS to your server IP
COURT_ID = 'basketball_a'
MODULE_ID = 'environment_unit_2'
SEND_INTERVAL = 30  # Send data every 30 seconds

# ========== SOCKET.IO CLIENT ==========
sio = socketio.Client()
is_connected = False

@sio.event
def connect():
    """Called when connected to server"""
    global is_connected
    is_connected = True
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Module 2 connected to server')
    
    # Register this module
    sio.emit('module_register', {
        'module_id': MODULE_ID,
        'module_type': 'environment',
        'court_id': COURT_ID,
        'timestamp': datetime.now().isoformat()
    })
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Module registered with server')

@sio.event
def disconnect():
    """Called when disconnected from server"""
    global is_connected
    is_connected = False
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Module 2 disconnected from server')

# ========== HARDWARE INITIALIZATION ==========

#Create sensor object, communicating over the board's default I2C bus
i2c = board.I2C()
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c, 0x77)

#Singapore mean pressure (hPa) at sea level
bme680.sea_level_pressure = 1008.5

#Calibrate the temperature sensor value
temperature_offset = -5

#Create sensor object, communicating over the board's default I2C bus
i2c = board.I2C()
uv = adafruit_veml6070.VEML6070(i2c)

def OLEDClickInit():
    Pin_DC = digitalio.DigitalInOut(board.P8_13)
    Pin_DC.direction = digitalio.Direction.OUTPUT
    Pin_DC.value = False
    Pin_RESET = digitalio.DigitalInOut(board.P8_16)
    Pin_RESET.direction = digitalio.Direction.OUTPUT
    Pin_RESET.value = True
    L_I2c = busio.I2C(SCL, SDA)
    return L_I2c

def BarGraph2Init():
    GPIO.setup("P8_19", GPIO.OUT)
    GPIO.setup("P8_14", GPIO.OUT)
    GPIO.output("P8_19", GPIO.HIGH)
    GPIO.output("P8_14", GPIO.HIGH)
    L_Spi1 = SPI(0,0)
    L_Spi1.mode = 0
    return L_Spi1

def BarGraph2DisplayGreen(L_Spi1, L_NumberOfBar):
    L_Spi1.writebytes([0x00, 0x03, 0xFF])

def BarGraph2DisplayYellow(L_Spi1, L_NumberOfBar):
    L_Spi1.writebytes([0x0F, 0xFF, 0xFF])

def BarGraph2DisplayRed(L_Spi1, L_NumberOfBar):
    L_Spi1.writebytes([0x0F, 0xFC, 0x00])

# Initialize SPI for BarGraph
G_Spi1 = BarGraph2Init()

def OledGreen():
    ImageObj = Image.new("1", (Display.width, Display.height))
    Draw = ImageDraw.Draw(ImageObj)
   
    Font = ImageFont.load_default()
    Text = "Temp: %.1f C" % temp
    Draw.text((32, 25), Text, font=Font, fill=1)
    Text = "Humid: %.1f%%" % humidity
    Draw.text((32, 40), Text, font=Font, fill=1)  # Fixed typo: fony -> font
    
    Display.image(ImageObj)
    Display.show()

def OledYel():
    ImageObj = Image.new("1", (Display.width, Display.height))
    Draw = ImageDraw.Draw(ImageObj)
   
    Font = ImageFont.load_default()
    Text = "Temp: %.1f C" % temp
    Draw.text((32, 25), Text, font=Font, fill=1)
    Text = "Humid: %.1f%%" % humidity
    Draw.text((32, 40), Text, font=Font, fill=1)  # Fixed typo: fony -> font
    
    Display.image(ImageObj)
    Display.show()

def OledRed():
    ImageObj = Image.new("1", (Display.width, Display.height))
    Draw = ImageDraw.Draw(ImageObj)
   
    Font = ImageFont.load_default()
    Text = "Temp: %.1f C" % temp
    Draw.text((32, 25), Text, font=Font, fill=1)
    Text = "Humid: %.1f%%" % humidity
    Draw.text((32, 40), Text, font=Font, fill=1)  # Fixed typo: fony -> font
    
    Display.image(ImageObj)
    Display.show()

G_I2c = OLEDClickInit()
Display = adafruit_ssd1306.SSD1306_I2C(128, 64, G_I2c, addr=0x3C)

# ========== DATA PROCESSING FUNCTIONS ==========

def calculate_comfort_score(temp, humidity, uv_index):
    """Calculate comfort score (1.0 to 5.0) based on conditions"""
    # Ensure all inputs are numeric
    temp = float(temp)
    humidity = float(humidity)
    uv_index = int(uv_index) if uv_index is not None else 0
    
    score = 5.0
    
    # Temperature penalty (optimal: 20-25°C)
    if temp < 20:
        score -= (20 - temp) * 0.1
    elif temp > 25:
        score -= (temp - 25) * 0.15
    
    # Humidity penalty (optimal: 40-60%)
    if humidity < 40:
        score -= (40 - humidity) * 0.02
    elif humidity > 60:
        score -= (humidity - 60) * 0.03
    
    # UV penalty
    if uv_index > 7:
        score -= (uv_index - 7) * 0.2
    
    return max(1.0, min(5.0, score))

def determine_voc_level(gas_reading):
    """Determine VOC level based on gas sensor reading"""
    # BME680 gas reading is in ohms (lower = better air quality)
    # Typical range: 5000-500000 ohms
    # Ensure numeric type
    gas_reading = int(gas_reading) if gas_reading is not None else 50000
    
    if gas_reading < 20000:
        return 'good'
    elif gas_reading < 100000:
        return 'moderate'
    else:
        return 'poor'

def generate_warnings(temp, humidity, uv_index):
    """Generate warnings based on sensor readings"""
    # Ensure all inputs are numeric
    temp = float(temp)
    humidity = float(humidity)
    uv_index = int(uv_index) if uv_index is not None else 0
    
    warnings = []
    
    if uv_index > 7:
        warnings.append('High UV - Use sunscreen')
    if temp > 32:
        warnings.append('High temperature - Stay hydrated')
    if humidity > 70:
        warnings.append('High humidity')
    if temp > 35:
        warnings.append('Extreme heat - Avoid outdoor activity')
    
    return warnings

def generate_recommendations(temp, humidity, uv_index):
    """Generate recommendations based on conditions"""
    # Ensure all inputs are numeric
    temp = float(temp)
    humidity = float(humidity)
    uv_index = int(uv_index) if uv_index is not None else 0
    
    recommendations = []
    
    if uv_index > 7:
        recommendations.append('use_sunscreen')
    if temp > 30:
        recommendations.append('stay_hydrated')
    if temp > 32 and uv_index > 7:
        recommendations.append('play_after_6pm')
    if humidity > 70:
        recommendations.append('take_breaks')
    
    return recommendations

# ========== DATA TRANSMISSION FUNCTION ==========

def send_environment_data():
    """Send environment data to server"""
    global is_connected, temp, humidity, uv_raw
    
    if not is_connected:
        return
    
    try:
        # Read sensors
        temp = float(bme680.temperature) + temperature_offset
        humidity = float(bme680.relative_humidity)
        pressure = float(bme680.pressure)
        gas_reading = int(bme680.gas)
        uv_raw = int(uv.uv_raw)
        
        # Get UV index - convert to numeric if needed
        uv_index_value = uv.get_index(uv_raw)
        # uv.get_index() might return a string, so convert to numeric index
        # VEML6070 index mapping: 0-2=Low(0-2), 3-5=Moderate(3-5), 6-7=High(6-7), 8-10=Very High(8-10), 11+=Extreme(11+)
        if isinstance(uv_index_value, str):
            # Convert string risk level to numeric index
            uv_index_map = {
                'Low': 2,
                'Moderate': 5,
                'High': 7,
                'Very High': 10,
                'Extreme': 11
            }
            uv_index = uv_index_map.get(uv_index_value, 5)  # Default to moderate
        else:
            uv_index = int(uv_index_value) if uv_index_value is not None else 0
        
        # Calculate derived values
        comfort_score = calculate_comfort_score(temp, humidity, uv_index)
        voc_level = determine_voc_level(gas_reading)
        warnings = generate_warnings(temp, humidity, uv_index)
        recommendations = generate_recommendations(temp, humidity, uv_index)
        playable = temp < 35 and uv_index < 11  # Safe to play if not extreme conditions
        
        # Send environment data event
        sio.emit('EnvironmentDataEvent', {
            'module_id': MODULE_ID,
            'court_id': COURT_ID,
            'timestamp': datetime.now().isoformat(),
            'data': {
                'temperature_c': round(temp, 1),
                'humidity_percent': round(humidity, 1),
                'pressure_hpa': round(pressure, 2),
                'voc_level': voc_level,
                'voc_reading': gas_reading,
                'uv_index': uv_index,
                'comfort_score': round(comfort_score, 1),
                'playable': playable,
                'warnings': warnings,
                'recommendations': recommendations
            }
        })
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Environment data sent to server")
        
    except Exception as e:
        print(f"[ERROR] Failed to send environment data: {e}")

# ========== MAIN LOOP ==========

if __name__ == "__main__":
    print("=" * 60)
    print("Module 2: Environment Monitoring Unit")
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
            print("Connected! Starting sensor loop...")
            print("Press Ctrl+C to stop.\n")
        else:
            print("[ERROR] Failed to connect to server")
            print("Continuing with local display only...")
            
    except socketio.exceptions.ConnectionError as e:
        print(f"[ERROR] Connection error: {e}")
        print("Make sure the server is running and the URL is correct.")
        print("Continuing with local display only...")
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        print("Continuing with local display only...")
    
    # Main loop
    last_send_time = 0
    
    try:
        while True:
            # Read sensors
            temp = bme680.temperature + temperature_offset
            humidity = bme680.relative_humidity
            uv_raw = uv.uv_raw
            
            # Print sensor readings
            print("\nTemp: %.1f°C | Humidity: %.1f%% | UV: %d" % (temp, humidity, uv_raw))
            print("\n" + "="*50)
            print("Temperature: %0.1f C" % temp)
            print("Air Quality: %d ohm" % bme680.gas)
            print("Humidity: %0.1f %%" % humidity)
            
            bars = min(int((uv_raw / 1500) * 10), 10)
            
            uv_raw = uv.uv_raw
            risk_level = uv.get_index(uv_raw)
            print('Reading: {0} | Risk Level: {1}'.format(uv_raw, risk_level))
            
            # Decide which color based on conditions
            if temp >= 27 and humidity >= 70 and uv_raw > 1000:
                # DANGER - Show RED bars
                BarGraph2DisplayRed(G_Spi1, 10)
                OledRed()
                print("🔴 RED - DANGER! Don't go out!")
                print("   High temp + High humidity + High UV")
                
            elif uv_raw > 500 and uv_raw <= 1000 and humidity <= 70 and humidity >= 70:
                # MODERATE - Show YELLOW bars
                BarGraph2DisplayYellow(G_Spi1, 10)
                OledYel()
                print("🟡 YELLOW - MODERATE! Be careful")
                print("   Moderate UV + OK humidity")
                
            elif temp < 27 and humidity < 70 and uv_raw <= 500:
                # SAFE - Show GREEN bars
                BarGraph2DisplayGreen(G_Spi1, 10)
                OledGreen()
                print("🟢 GREEN - SAFE! Good to go out")
                print("   Cool temp + Low humidity + Low UV")
                
            else:
                # DEFAULT - Show YELLOW bars for mixed conditions
                BarGraph2DisplayYellow(G_Spi1, 10)
                OledYel()
                print("🟡 YELLOW - MODERATE! Mixed conditions")
            
            print("="*50)
            
            # Send data to server at specified interval
            current_time = time.time()
            if current_time - last_send_time >= SEND_INTERVAL:
                send_environment_data()
                last_send_time = current_time
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        # Cleanup
        if sio.connected:
            sio.disconnect()
