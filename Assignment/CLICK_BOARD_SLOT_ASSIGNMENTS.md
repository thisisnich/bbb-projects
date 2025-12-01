    # Click Board Slot Assignments for BeagleBone Black Wireless

## BBBW Click Board Slots

The BeagleBone Black Wireless has **4 Click board slots**:
- **Slot 1** (AN) - Analog/GPIO
- **Slot 2** (PWM) - PWM/GPIO  
- **Slot 3** (I2C) - I2C bus
- **Slot 4** (SPI) - SPI bus

## Module 1: Crowd Intelligence Unit

| Slot | Board | Interface | Notes |
|------|-------|-----------|-------|
| **Slot 1 (AN)** | **MIC Click** | Analog/GPIO | Audio input, uses ADC |
| **Slot 2 (PWM)** | **Motion Click** | GPIO | PIR motion sensor, digital input |
| **Slot 3 (I2C)** | **OLED Click** | I2C | Display (128x64), I2C communication |
| **Slot 4 (SPI)** | **Proximity Click** | I2C/SPI | Proximity sensor (check board spec) |

**Alternative (if Proximity uses I2C):**
- Slot 3: OLED Click (I2C)
- Slot 4: Proximity Click (I2C) - Can share I2C bus with OLED

**Note:** USB Webcam connects via USB port (not a Click board slot)

---

## Module 2: Environmental Conditions Station

| Slot | Board | Interface | Notes |
|------|-------|-----------|-------|
| **Slot 1 (AN)** | **Environment Click** | I2C | Temp, humidity, pressure, VOC (I2C) |
| **Slot 2 (PWM)** | **UV 3 Click** | I2C | UV index sensor (I2C) |
| **Slot 3 (I2C)** | **Bar Graph 2 Click** | I2C/SPI | LED bar display (check board spec) |
| **Slot 4 (SPI)** | **OLED Click** | I2C | Display (128x64), I2C communication |

**Note:** Multiple I2C devices can share the I2C bus. If Bar Graph uses SPI, it goes in Slot 4, and OLED can share I2C bus in Slot 3.

---

## Module 3: Feedback Kiosk

| Slot | Board | Interface | Notes |
|------|-------|-----------|-------|
| **Slot 1 (AN)** | **IR Gesture Click** | I2C | Gesture sensor (I2C) |
| **Slot 2 (PWM)** | **LED Matrix Click** | SPI | 8x8 LED matrix display (SPI) |
| **Slot 3 (I2C)** | **OLED Click** | I2C | Display (128x64), I2C communication |
| **Slot 4 (SPI)** | **Buzz 2 Click** | GPIO/PWM | Buzzer, uses GPIO or PWM |

**Alternative:**
- If Buzz 2 uses GPIO: Can go in Slot 1 or 2 (GPIO slots)
- If LED Matrix uses I2C: Swap with OLED positions

---

## Module 4: Security Dashboard

| Slot | Board | Interface | Notes |
|------|-------|-----------|-------|
| **Slot 1 (AN)** | **7-Segment 8x8 Click** | SPI | 8-digit 7-segment display (SPI) |
| **Slot 2 (PWM)** | **LED Matrix Click** | SPI | 8x8 LED matrix (SPI) |
| **Slot 3 (I2C)** | **OLED Click** | I2C | Display (128x64), I2C communication |
| **Slot 4 (SPI)** | **Buzz 2 Click** | GPIO/PWM | Buzzer, uses GPIO or PWM |

**Note:** If both 7-Segment and LED Matrix use SPI, they may need to share SPI bus or use different chip selects.

---

## Module 5: Smart Court Information Display

| Slot | Board | Interface | Notes |
|------|-------|-----------|-------|
| **Slot 1 (AN)** | **Analog Key Click** | ADC | 5-button keypad, uses ADC (P9_40) |
| **Slot 2 (PWM)** | **Bar Graph 2 Click** | I2C/SPI | Hourly pattern display (check board spec) |
| **Slot 3 (I2C)** | **OLED Click** | I2C | Display (128x64), I2C communication |
| **Slot 4 (SPI)** | **Buzz 2 Click** | GPIO/PWM | Buzzer, uses GPIO or PWM |

**Alternative (if using 8x8 LED Matrix instead of Bar Graph):**
- Slot 2: **8x8 LED Matrix Click** (SPI) - Hourly pattern visualization

---

## Important Notes

### I2C Bus Sharing
- Multiple I2C devices can share the same I2C bus (Slot 3)
- Each device needs a unique I2C address
- Common I2C devices: OLED, Environment, UV3, IR Gesture

### SPI Bus Sharing
- SPI devices can share SPI bus but need different chip select (CS) pins
- Common SPI devices: LED Matrix, 7-Segment, Bar Graph (if SPI version)

### ADC/Analog
- Slot 1 (AN) provides ADC access
- Analog Key Click uses ADC pin (typically P9_40)
- MIC Click may use ADC for audio level

### GPIO/PWM
- Slot 2 (PWM) provides GPIO and PWM access
- Motion Click uses GPIO for digital input
- Buzz 2 Click may use GPIO or PWM for audio output

### Verification Steps
1. Check each Click board's datasheet for interface type (I2C/SPI/GPIO/ADC)
2. Verify I2C addresses don't conflict (use `i2cdetect` command)
3. Check SPI chip select pins if using multiple SPI devices
4. Test each board individually before combining

---

## Quick Reference Table

| Module | Slot 1 (AN) | Slot 2 (PWM) | Slot 3 (I2C) | Slot 4 (SPI) |
|--------|-------------|--------------|-------------|--------------|
| **Module 1** | MIC Click | Motion Click | OLED Click | Proximity Click |
| **Module 2** | Environment Click | UV 3 Click | Bar Graph 2 | OLED Click |
| **Module 3** | IR Gesture Click | LED Matrix | OLED Click | Buzz 2 Click |
| **Module 4** | 7-Seg 8x8 Click | LED Matrix | OLED Click | Buzz 2 Click |
| **Module 5** | Analog Key Click | Bar Graph 2 | OLED Click | Buzz 2 Click |

---

## Troubleshooting

### "Device not found" errors
- Check I2C addresses: `sudo i2cdetect -y 1` (or `-y 2` for I2C2)
- Verify board is properly seated in slot
- Check if board requires power jumper configuration

### SPI conflicts
- Ensure different CS pins for each SPI device
- Check SPI mode and speed settings
- Verify SPI bus is enabled in device tree

### ADC not working
- Check ADC is enabled: `cat /sys/bus/iio/devices/iio\:device0/in_voltage0_raw`
- Verify pin configuration for Analog Key Click
- Check voltage levels (should be 0-1.8V for BBBW)

### Multiple I2C devices
- Use `i2cdetect` to find all addresses
- Update code with correct I2C addresses
- Some boards have address jumpers to change address

---

**Last Updated:** 2025-11-17  
**Version:** 1.0

