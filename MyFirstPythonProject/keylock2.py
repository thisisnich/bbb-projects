#keylock2 code
import time
import Adafruit_BBIO.GPIO as GPIO

GPIO.setup("P8_16", GPIO.IN)
GPIO.setup("P8_13", GPIO.IN)
GPIO.setup("P8_17", GPIO.IN)

while True:
    print(GPIO.input("P8_16"), GPIO.input("P8_13"), GPIO.input("P8_17"))
    time.sleep(0.3)
