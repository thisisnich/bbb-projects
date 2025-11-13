import time
import Adafruit_BBIO.PWM as PWM

PWM.start("P8_19", 50)

PWM.set_frequency("P8_19", 523)
time.sleep(0.5)
PWM.set_frequency("P8_19", 587)
time.sleep(0.5)
PWM.set_frequency("P8_19", 659)
time.sleep(0.5)

PWM.stop("P8_19")
