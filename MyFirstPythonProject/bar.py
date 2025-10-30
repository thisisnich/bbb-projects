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

G_NumberOfBar = 0
G_Spi1 = BarGraph2Init()

while True:
    BarGraph2Display(G_Spi1, G_NumberOfBar)
    G_NumberOfBar += 1
    if G_NumberOfBar == 11:
        G_NumberOfBar = 0
    
    time.sleep(0.3)
