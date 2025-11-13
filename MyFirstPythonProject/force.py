import time
import Adafruit_BBIO.ADC as ADC
 
ADC.setup()

while True:
    DigitalValue = ADC.read("P9_39")
    AnalogVoltage = (DigitalValue * 1.8) * (2200 / 1200)
    print("Digital Value: %f, Analog Voltage: %f" % (DigitalValue, AnalogVoltage))
    time.sleep(0.3)
