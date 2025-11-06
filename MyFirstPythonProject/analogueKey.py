#analogue key code 
import time
import Adafruit_BBIO.ADC as ADC

ADC.setup()

while True:
    DigitalValue = ADC.read("P9_40")
    if DigitalValue >= 0.00 and DigitalValue < 0.10:
        print("No Key is Pressed")
    elif DigitalValue > 0.16 and DigitalValue < 0.18:
        print("T6 Key is Pressed")
    elif DigitalValue > 0.33 and DigitalValue < 0.35:
        print("T5 Key is Pressed")
    elif DigitalValue > 0.50 and DigitalValue < 0.52:
        print("T4 Key is Pressed")
    elif DigitalValue > 0.67 and DigitalValue < 0.69:
        print("T3 Key is Pressed")
    elif DigitalValue > 0.84 and DigitalValue < 0.86:
        print("T2 Key is Pressed")
    elif DigitalValue > 0.90 and DigitalValue < 1.10:
        print("T1 Key is Pressed")
    time.sleep(0.3)
