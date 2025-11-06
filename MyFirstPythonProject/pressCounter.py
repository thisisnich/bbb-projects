#pressCounter code
from Adafruit_BBIO.SPI import SPI
import Adafruit_BBIO.GPIO as GPIO


def SevenSegInit():
    GPIO.setup("P8_19", GPIO.OUT)
    GPIO.setup("P8_14", GPIO.OUT)
    GPIO.output("P8_19", GPIO.HIGH)
    GPIO.output("P8_14", GPIO.HIGH)
    L_Spi0 = SPI(0,0)
    L_Spi0.mode = 0
    return L_Spi0




def SevenSegDisplay(L_Spi0, L_Number):
    OnesDigit = L_Number % 10
    TensDigit = L_Number / 10
    L_Spi0.writebytes([DigitList[int(OnesDigit)], DigitList[int(TensDigit)]])


G_Number = 0
DigitList = [0x7E, 0x0A, 0xB6, 0x9E, 0xCA, 0xDC, 0xFC, 0x0E, 0xFE, 0xDE]

GPIO.setup("P9_15", GPIO.IN)
G_Spi0 = SevenSegInit()
SevenSegDisplay(G_Spi0, G_Number)

while True:
    PressStatus = GPIO.input("P9_15")
    if PressStatus:
        G_Number += 1
        if G_Number == 100:
            G_Number = 0
        SevenSegDisplay(G_Spi0, G_Number)
        while PressStatus:
            PressStatus = GPIO.input("P9_15")
