import time
from Adafruit_BBIO.SPI import SPI
import Adafruit_BBIO.GPIO as GPIO

def BarGraph2Init():
    GPIO.setup("P9_14", GPIO.OUT)
    GPIO.setup("P9_12", GPIO.OUT)
    GPIO.output("P9_14", GPIO.HIGH)
    GPIO.output("P9_12", GPIO.HIGH)
    L_Spi1 = SPI(1,0)
    L_Spi1.mode = 0
    return L_Spi1

def SevenSegInit():
    GPIO.setup("P8_19", GPIO.OUT)
    GPIO.setup("P8_14", GPIO.OUT)
    GPIO.output("P8_19", GPIO.HIGH)
    GPIO.output("P8_14", GPIO.HIGH)
    L_Spi0 = SPI(0,0)
    L_Spi0.mode = 0
    return L_Spi0

def BarGraph2Display(L_Spi1, L_NumberOfBar):
    if L_NumberOfBar == 0:
        L_Spi1.writebytes([0x00, 0x00, 0x00])
    if L_NumberOfBar == 1:
        L_Spi1.writebytes([0x00, 0x00, 0x01])
    if L_NumberOfBar == 2:
        L_Spi1.writebytes([0x00, 0x00, 0x03])
    if L_NumberOfBar == 3:
        L_Spi1.writebytes([0x00, 0x00, 0x07])
    if L_NumberOfBar == 4:
        L_Spi1.writebytes([0x00, 0x00, 0x0F])
    if L_NumberOfBar == 5:
        L_Spi1.writebytes([0x00, 0x40, 0x1F])
    if L_NumberOfBar == 6:
        L_Spi1.writebytes([0x00, 0xC0, 0x3F])
    if L_NumberOfBar == 7:
        L_Spi1.writebytes([0x01, 0xC0, 0x7F])
    if L_NumberOfBar == 8:
        L_Spi1.writebytes([0x03, 0xC0, 0xFF])
    if L_NumberOfBar == 9:
        L_Spi1.writebytes([0x07, 0xC0, 0xFF])
    if L_NumberOfBar == 10:
        L_Spi1.writebytes([0x0F, 0xC0, 0xFF])

def SevenSegDisplay(L_Spi0, L_Number):
    OnesDigit = L_Number % 10
    TensDigit = L_Number / 10
    L_Spi0.writebytes([DigitList[int(OnesDigit)], DigitList[int(TensDigit)]])


G_NumberOfBar = 1
G_Number = 0
NumCounter = 0
DigitList = [0x7E, 0x0A, 0xB6, 0x9E, 0xCA, 0xDC, 0xFC, 0x0E, 0xFE, 0xDE]
G_Spi0 = SevenSegInit()
G_Spi1 = BarGraph2Init()

while True:
    SevenSegDisplay(G_Spi0, G_Number)
    BarGraph2Display(G_Spi1, G_NumberOfBar)
    
    G_Number += 1
    if G_Number == 100:
        G_Number = 0
    
    NumCounter += 1
    if NumCounter == 10:
        NumCounter = 0
        G_NumberOfBar += 1
        if G_NumberOfBar == 11:
            G_NumberOfBar = 1
    
    time.sleep(0.3)
