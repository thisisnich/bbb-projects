import time
import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.PWM as PWM



GPIO.setup("P8_10", GPIO.IN)
PWM.start("P8_19", 50)

while True:
    if GPIO.input("P8_10"):
        PWM.stop("P8_19")
    else:
        PWM.start("P8_19", 50)
        PWM.set_frequency("P8_19", 1000)
        time.sleep(0.1)
        PWM.set_frequency("P8_19", 2000)
        time.sleep(0.1)
    time.sleep(0.3)

