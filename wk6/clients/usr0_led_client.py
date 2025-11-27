import socketio
import random
import time
import requests
import json
import Adafruit_BBIO.GPIO as GPIO

sio = socketio.Client()
GPIO.setup('USR0', GPIO.OUT)



@sio.event
def connect():
    print('Connection established.')

@sio.event
def disconnect():
    print('Disconnected from server.')
    
@sio.event
def ControlUSR0Led(RxData):
    if RxData == 'on':
        GPIO.output('USR0', GPIO.HIGH)
        print('USD0 LED is ON!')
    if RxData == 'off':
        GPIO.output('USR0', GPIO.LOW)
        print('USD0 LED is OFF!')

while True:
    try:
        sio.connect('http://192.168.72.239:5000')
        break
    except:
        print("Try to connect to the server.")
        pass

while True:
    try:
        TxData = requests.get("https://api.data.gov.sg/v1/environment/air-temperature")
        TxDataObject = json.loads(TxData.text)
        TemperatureReading = TxDataObject['items']
        for TemperatureReadings in TemperatureReading:
            TemperatureValue = TemperatureReadings['readings']
        sio.emit('BBBW4Event', {'data': TemperatureValue[0]["value"]})
        print('Data sent!')
    except:
        pass
        print('Unable to transmit data.')
    time.sleep(2)
