from flask import Flask
from flask import render_template
from flask import request

#https://flask.palletsprojects.com/en/3.0.x/deploying/eventlet/
import eventlet
from eventlet import wsgi

from flask_socketio import SocketIO
from flask_socketio import emit
from datetime import datetime
    
app = Flask(__name__)
#socketio = SocketIO(app)
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*") 

# Track connected boards
connected_boards = {
    'BBBW1': False,
    'BBBW2': False,
    'BBBW3': False,
    'BBBW4': False
}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Client disconnected: {request.sid}')

@socketio.event
def BBBW1Event(RxData):
    connected_boards['BBBW1'] = True
    socketio.emit('Web_BBBW1Event', RxData)
    print(f'[{datetime.now().strftime("%H:%M:%S")}] BBBW1 - Data received: {RxData}')
    socketio.emit('board_status', {'board': 'BBBW1', 'status': True, 'data': RxData})

@socketio.event
def BBBW2Event(RxData):
    connected_boards['BBBW2'] = True
    socketio.emit('Web_BBBW2Event', RxData)
    print(f'[{datetime.now().strftime("%H:%M:%S")}] BBBW2 - Data received: {RxData}')
    socketio.emit('board_status', {'board': 'BBBW2', 'status': True, 'data': RxData})

@socketio.event
def BBBW3Event(RxData):
    connected_boards['BBBW3'] = True
    socketio.emit('Web_BBBW3Event', RxData)
    print(f'[{datetime.now().strftime("%H:%M:%S")}] BBBW3 - Data received: {RxData}')
    socketio.emit('board_status', {'board': 'BBBW3', 'status': True, 'data': RxData})

@socketio.event
def BBBW4Event(RxData):
    connected_boards['BBBW4'] = True
    socketio.emit('Web_BBBW4Event', RxData)
    print(f'[{datetime.now().strftime("%H:%M:%S")}] BBBW4 - Data received: {RxData}')
    socketio.emit('board_status', {'board': 'BBBW4', 'status': True, 'data': RxData})

@socketio.event
def BBBW4VideoFrame(RxData):
    """Handle video frames from BBBW4 webcam."""
    connected_boards['BBBW4'] = True
    # Broadcast video frame to all connected web clients
    socketio.emit('Web_BBBW4VideoFrame', RxData)
    print(f'[{datetime.now().strftime("%H:%M:%S")}] BBBW4 - Video frame received (size: {len(RxData.get("data", ""))} bytes)')

if __name__ == '__main__':
    #app.run(host='192.168.X.X')
    wsgi.server(eventlet.listen(("192.168.72.161", 5000)), app)

