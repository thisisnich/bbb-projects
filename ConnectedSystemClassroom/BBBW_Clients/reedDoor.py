import socketio
import time
import Adafruit_BBIO.GPIO as GPIO

sio = socketio.Client()
GPIO.setup("P8_10", GPIO.IN)

@sio.event
def connect():
    print('Connection established.')

@sio.event
def disconnect():
    print('Disconnected from server')

while True:
    try:
        sio.connect('http://192.168.72.161:5000')
        break
    except:
        print("Try to connect to the server.")
        pass

PreviousDoorDetectionStatus = 0

while True:
    try:
        CurrentDoorDetectionStatus = GPIO.input("P8_10")
        if CurrentDoorDetectionStatus:
            print("Magnet is Detected (Door Closed)")
        else:
            print("No Magnet is Detected (Door Opened)")
        if (abs(CurrentDoorDetectionStatus - PreviousDoorDetectionStatus) > 0):
            sio.emit('BBBW4Event', {'data': CurrentDoorDetectionStatus})
            print('Data sent!')
        PreviousDoorDetectionStatus = CurrentDoorDetectionStatus
    except:
        print('Unable to transmit data.')
        pass
    time.sleep(0.5)
