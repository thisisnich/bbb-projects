import time
import Adafruit_BBIO.ADC as ADC
 
ADC.setup()

while True:
    DigitalValue = ADC.read("P9_38")
    if DigitalValue != 0:
        AnalogVoltage = (DigitalValue * 1.8) * (2200 / 1200)
        DistanceCM = 29.988 * pow(AnalogVoltage , -1.173)
        print("Distance(cm): %f" % DistanceCM)
    time.sleep(0.3)
