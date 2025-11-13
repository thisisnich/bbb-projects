
import time
import Adafruit_BBIO.GPIO as GPIO

GPIO.setup("P8_10", GPIO.IN)

while True:
    if GPIO.input("P8_10"):
        print("Magnet is Detected")
    else:
        print("No Magnet is Detected")
    time.sleep(0.3)
