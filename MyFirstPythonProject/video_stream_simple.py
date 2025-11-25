"""
Simple Video Streaming Server - No OpenCV needed
Uses fswebcam to capture frames and streams via Flask
"""
from flask import Flask, Response
import subprocess
import threading
import time
import os
import signal
import sys

app = Flask(__name__)

# Global state
streaming = False
capture_process = None

def capture_frame():
    """Capture a single frame using fswebcam."""
    try:
        # Capture to memory (stdout) instead of file
        result = subprocess.run([
            'fswebcam',
            '-d', '/dev/video0',
            '-r', '640x480',
            '--no-banner',
            '--skip', '2',
            '--jpeg', '85',
            '-'
        ], capture_output=True, timeout=3)
        
        if result.returncode == 0 and len(result.stdout) > 0:
            return result.stdout
    except Exception as e:
        print(f"[ERROR] Frame capture failed: {e}")
    return None

def generate_stream():
    """Generator function for MJPEG streaming."""
    global streaming
    streaming = True
    
    print("[STREAM] Starting video stream...")
    
    while streaming:
        try:
            frame = capture_frame()
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                # If capture fails, wait a bit
                time.sleep(0.1)
        except Exception as e:
            print(f"[ERROR] Stream error: {e}")
            time.sleep(0.5)
    
    print("[STREAM] Stream stopped")

@app.route('/')
def index():
    """Simple HTML page for video stream."""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>BBBW Video Stream</title>
        <style>
            body {
                background: #1a1a1a;
                color: white;
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 20px;
            }
            #videoStream {
                max-width: 100%;
                border: 2px solid #333;
                border-radius: 8px;
            }
            .status {
                margin: 20px;
                padding: 10px;
                background: #2a2a2a;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <h1>BBBW Video Stream</h1>
        <div class="status">Streaming from Logitech C615 HD</div>
        <img id="videoStream" src="/video_feed" alt="Video Stream" />
        <div class="status">Refresh page if stream stops</div>
    </body>
    </html>
    '''

@app.route('/video_feed')
def video_feed():
    """MJPEG video streaming route."""
    return Response(generate_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

def signal_handler(sig, frame):
    """Handle shutdown gracefully."""
    global streaming
    print("\n[INFO] Shutting down...")
    streaming = False
    sys.exit(0)

if __name__ == '__main__':
    # Check if webcam exists
    if not os.path.exists('/dev/video0'):
        print("[ERROR] /dev/video0 not found!")
        print("[INFO] Connect your webcam and try again")
        sys.exit(1)
    
    # Check if fswebcam is available
    result = subprocess.run(['which', 'fswebcam'], capture_output=True)
    if result.returncode != 0:
        print("[ERROR] fswebcam not found!")
        print("[INFO] Install with: sudo apt install fswebcam")
        sys.exit(1)
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=" * 50)
    print("BBBW Simple Video Stream Server")
    print("=" * 50)
    print("Using fswebcam (no OpenCV needed)")
    print("Access at: http://<bbbw-ip>:5000")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        pass
    finally:
        streaming = False
        print("\n[INFO] Server stopped")

