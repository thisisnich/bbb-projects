import time
import socketio

# --- Hardware Imports ---
import Adafruit_BBIO.ADC as ADC
import Adafruit_BBIO.GPIO as GPIO
from Adafruit_BBIO.SPI import SPI

# --- OLED Imports ---
import board
import busio
import digitalio
import adafruit_ssd1306
from board import SCL, SDA
from PIL import Image, ImageDraw, ImageFont

# --- 1. SETUP SOCKETIO ---
sio = socketio.Client()
try:
    sio.connect('http://192.168.68.73:5000')
    print("Connected to Server!")
except:
    print("Connection Failed - Running Offline Mode")

# --- 2. SETUP HARDWARE ---
ADC.setup()  # For IR (P9_37) and Mic (P9_40)

# OLED Setup Function
def OLEDClickInit():
    Pin_DC = digitalio.DigitalInOut(board.P9_14)
    Pin_DC.direction = digitalio.Direction.OUTPUT
    Pin_DC.value = False
    
    Pin_RESET = digitalio.DigitalInOut(board.P9_12)
    Pin_RESET.direction = digitalio.Direction.OUTPUT
    Pin_RESET.value = True
    
    L_I2c = busio.I2C(SCL, SDA)
    return L_I2c

# Init OLED
i2c = OLEDClickInit()
display = adafruit_ssd1306.SSD1306_I2C(64, 32, i2c, addr=0x3C)
image = Image.new("1", (display.width, display.height))
draw = ImageDraw.Draw(image)
font = ImageFont.load_default()

# Bar Graph Setup Function
def BarGraph2Init():
    GPIO.setup("P8_19", GPIO.OUT)
    GPIO.setup("P8_14", GPIO.OUT)
    GPIO.output("P8_19", GPIO.HIGH)
    GPIO.output("P8_14", GPIO.HIGH)
    L_Spi1 = SPI(1, 0)
    L_Spi1.mode = 0
    return L_Spi1

def BarGraph2Display(L_Spi1, L_NumberOfBar):
    # Your provided hex logic
    if L_NumberOfBar == 0:
        L_Spi1.writebytes([0x00, 0x00, 0x00])
    if L_NumberOfBar == 1:
        L_Spi1.writebytes([0x00, 0x00, 0x01])
    if L_NumberOfBar == 2:
        L_Spi1.writebytes([0x00, 0x00, 0x03])
    if L_NumberOfBar == 3:
        L_Spi1.writebytes([0x00, 0x00, 0x07])
    if L_NumberOfBar == 4:
        L_Spi1.writebytes([0x00, 0x00, 0x0F])
    if L_NumberOfBar == 5:
        L_Spi1.writebytes([0x00, 0x40, 0x1F])
    if L_NumberOfBar == 6:
        L_Spi1.writebytes([0x00, 0xC0, 0x3F])
    if L_NumberOfBar == 7:
        L_Spi1.writebytes([0x01, 0xC0, 0x7F])
    if L_NumberOfBar == 8:
        L_Spi1.writebytes([0x03, 0xC0, 0xFF])
    if L_NumberOfBar == 9:
        L_Spi1.writebytes([0x07, 0xC0, 0xFF])
    if L_NumberOfBar >= 10:
        L_Spi1.writebytes([0x0F, 0xC0, 0xFF])

# Init Bar Graph
spi_bus = BarGraph2Init()

# Global Variables
usage_count = 0
bar_level = 0

# --- 3. MAIN LOOP ---
while True:
    # --- A. READ SENSORS ---
    
    # 1. IR Sensor (P9_37)
    ir_val = ADC.read("P9_37")
    dist_cm = 0
    if ir_val != 0:
        analog_volt = (ir_val * 1.8) * (2200 / 1200)
        dist_cm = 29.988 * pow(analog_volt, -1.173)
    
    # 2. Mic Sensor (P9_40)
    mic_val = ADC.read("P9_40")
    mic_volt = (mic_val * 1.8) * (2200 / 1200)
    
    # --- B. LOGIC ---
    # Logic: If object is close (< 10cm), increase count
    # (Simple logic: increments continuously if hand is there. 
    # In real life you'd add a "flag" to count only once per lift)
    if dist_cm < 10 and dist_cm > 0: 
        usage_count += 1
        time.sleep(0.2)  # Debounce
    
    # Map Usage Count to Bar Graph (0 to 10 scale)
    # Just a simple math division for demo
    bar_level = int(usage_count / 2) 
    if bar_level > 10:
        bar_level = 10
    
    # Update Hardware Bar Graph
    BarGraph2Display(spi_bus, bar_level)
    
    # Send Usage Data to Server
    if sio.connected:
        sio.emit('usage_data', {'count': usage_count})
    
    # Logic: Mic Volume Check
    is_loud = False
    if mic_volt > 1.5:  # Adjust this threshold based on testing
        is_loud = True
        
        # Send Alert to Server
        if sio.connected:
            sio.emit('volume_data', {'isLoud': True})
    
    # --- C. OLED DISPLAY ---
    # Clear image
    draw.rectangle((0, 0, display.width, display.height), outline=0, fill=0)
    if is_loud:
        draw.text((5, 10), "SLAM WARNING!", font=font, fill=1)
    else:
        draw.text((5, 5), f"Count: {usage_count}", font=font, fill=1)
        if usage_count < 10:
            draw.text((5, 15), "Status: GOOD", font=font, fill=1)
        elif usage_count < 18:
            draw.text((5, 15), "Status: MAINTAIN", font=font, fill=1)
        else:
            draw.text((5, 15), "Status: CRITICAL", font=font, fill=1)
    
    display.image(image)
    display.show()
    
    time.sleep(0.3)

