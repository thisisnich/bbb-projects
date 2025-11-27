import socketio
import time
import Adafruit_BBIO.ADC as ADC

# IMPORTANT: Update the IP address below to match your PC's IP address
# Run 'ipconfig' on Windows to find your PC's IP address
SERVER_IP = '192.168.7.1'  # Change this to your PC's IP address

sio = socketio.Client()
ADC.setup()

@sio.event
def connect():
    print('Connection established.')

@sio.event
def disconnect():
    print('Disconnected from server.')

while True:
    try:
        sio.connect(f'http://{SERVER_IP}:5000')
        break
    except:
        print("Try to connect to the server.")
        pass
    
OldDigitalValue = 0

while True:
    try:
        NewDigitalValue = ADC.read("P9_37")
        print("Digital Value: %f" % (NewDigitalValue))
        if(abs(NewDigitalValue - OldDigitalValue) > 0.1):
            sio.emit('BBBW2Event', {'data': NewDigitalValue})
            print('Data sent!')
        OldDigitalValue = NewDigitalValue
    except:
        print('Unable to transmit data.')
        pass
    time.sleep(0.5)

