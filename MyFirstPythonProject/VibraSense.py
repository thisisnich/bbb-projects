import time
import Adafruit_BBIO.GPIO as GPIO

GPIO.setup("P9_23", GPIO.OUT)
GPIO.setup("P9_41", GPIO.IN)

GPIO.output("P9_23", GPIO.HIGH)

while True:
    if GPIO.input("P9_41"):
        print("Vibration is Detected")
    else:
        print("No Vibration is Detected")
    time.sleep(0.3)
