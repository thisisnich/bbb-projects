# Module 5: Smart Court Information Display

## Overview
Displays court information on OLED, Bar Graph (or 8x8 LED Matrix), and handles button navigation. Receives data from cloud server via SocketIO.

## Hardware
- BeagleBone Black Wireless
- OLED Click (128x64) - Main display
- Bar Graph 2 Click OR 8x8 LED Matrix - Hourly pattern visualization
- Analog Key Click (5 buttons) - Navigation
- Buzz 2 Click - Audio feedback

## Files
- `Module5_Display_Client.py` - Main client code

## Setup

### 1. Install Dependencies
```bash
sudo pip3 install python-socketio
```

### 2. Install Hardware Libraries
```bash
# For OLED (example - adjust based on your library)
# sudo pip3 install Adafruit-SSD1306

# For Analog Key Click
# Uses Adafruit_BBIO.ADC (usually pre-installed)
```

### 3. Configuration
Edit `Module5_Display_Client.py` and update:
- `SERVER_URL` - Your cloud server IP address
- `COURT_ID` - Court identifier
- `MODULE_ID` - Module identifier

### 4. Hardware Setup
- Connect OLED Click to I2C bus
- Connect Bar Graph 2 Click or 8x8 LED Matrix
- Connect Analog Key Click to ADC pin (default: P9_40)
- Connect Buzz 2 Click

### 5. Run
```bash
sudo python3 Module5_Display_Client.py
```

## Features

### OLED Views (5 views)
1. **Current Status** (Button 1) - Shows current crowd, weather, rating
2. **Today's Pattern** (Button 2, first press) - Hourly occupancy pattern
3. **Weekly Comparison** (Button 2, second press) - Same time weekly pattern
4. **Weather Details** (Button 3) - Temperature, UV, comfort score
5. **Alternative Courts** (Button 4) - Nearby courts with availability
6. **Court Information** (Button 5) - Facilities, rating, cleaning info

### Button Navigation
- Button 1: Current Status
- Button 2: History (toggles Today/Week)
- Button 3: Weather
- Button 4: Alternatives
- Button 5: Court Info

### Auto-Rotation
- If no button pressed for 60 seconds, automatically cycles through views
- Each view shown for 15 seconds

### Bar Graph/8x8 Display
- Always shows 8-hour window around current time
- Left side: Historical data
- Right side: Predictions
- Updates every 30 seconds with new data

## Data Transmission

### Receives from Server:
- Event: `DisplayUpdate`
- Contains: current status, weather, patterns, recommendations, court info

### Sends to Server:
- Event: `module_register` - On connection
- Event: `registration_ack` - Receives acknowledgment

## Testing from Dashboard

1. Open dashboard in browser
2. Find "Module 5 Display Control" section
3. Click test buttons:
   - **Normal** - 5 people, moderate crowd
   - **Full** - 9 people, full court
   - **Empty** - 0 people, empty court
   - **Busy** - 7 people, busy court
4. Module 5 will receive and display the test data

## TODO: Hardware Implementation

The code includes placeholder functions for hardware control. You need to:

1. **OLED Display:**
   - Implement `init_oled()`
   - Implement `update_oled_display()` with actual drawing functions
   - Use library like Adafruit_SSD1306 or similar

2. **Bar Graph/8x8:**
   - Implement `init_bar_graph()`
   - Implement `update_bar_graph()` to set bar levels
   - Use appropriate library for your hardware

3. **Buttons:**
   - Implement `init_buttons()` - Setup ADC
   - Implement `read_button()` - Read ADC and map to button 1-5
   - Use `Adafruit_BBIO.ADC` for Analog Key Click

4. **Buzzer:**
   - Implement `init_buzz()`
   - Implement `buzz_beep()` - Trigger buzzer
   - Use GPIO or PWM control

## Example Button Reading (Analog Key Click)

```python
import Adafruit_BBIO.ADC as ADC

ADC.setup()
value = ADC.read("P9_40")

if 0.16 < value < 0.18:
    return 1  # Button 1
elif 0.33 < value < 0.35:
    return 2  # Button 2
elif 0.50 < value < 0.52:
    return 3  # Button 3
elif 0.67 < value < 0.69:
    return 4  # Button 4
elif 0.84 < value < 0.86:
    return 5  # Button 5
else:
    return 0  # No button
```

## Troubleshooting

- **Not receiving data:** Check server URL and network connection
- **Buttons not working:** Check ADC pin configuration and thresholds
- **OLED not displaying:** Check I2C connection and library installation
- **Bar graph not updating:** Check hardware initialization

