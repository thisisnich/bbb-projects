import time
import Adafruit_BBIO.PWM as PWM

PWM.start("P9_14", 50)

PWM.set_frequency("P9_14", 5000)
time.sleep(1)
PWM.set_frequency("P9_14", 1)
time.sleep(0.1)
PWM.set_frequency("P9_14", 5000)
time.sleep(1)
PWM.set_frequency("P9_14", 1)
time.sleep(0.1)
PWM.set_frequency("P9_14", 5000)
time.sleep(1)
PWM.set_frequency("P9_14", 1)
time.sleep(0.1)

PWM.stop("P9_14")
