
import time
import Adafruit_BBIO.GPIO as GPIO

GPIO.setup("P8_18", GPIO.IN)

while True:
    if GPIO.input("P8_18"):
        print("Paper is Detected")
    else:
        print("No Paper is Detected")
    time.sleep(0.3)
