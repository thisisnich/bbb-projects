#tamper code

import time
import Adafruit_BBIO.GPIO as GPIO

GPIO.setup("P9_15", GPIO.IN)

while True:
    if GPIO.input("P9_15"):
        print("Push Button is Pressed")
    else:
        print("Push Button is Not Pressed")
    time.sleep(0.3)
