import time
import Adafruit_BBIO.GPIO as GPIO

GPIO.setup("USR0", GPIO.OUT)
while True:
    GPIO.output("USR0", GPIO.HIGH)
    time.sleep(.5)
    GPIO.output("USR0", GPIO.LOW)
    time.sleep(.5)