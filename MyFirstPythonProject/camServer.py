"""
Standalone Camera Server for BBBW
Simple Flask server for webcam streaming only
"""
from flask import Flask, render_template, Response, jsonify, request
import threading
import time
import sys
import os

# Import webcam module
try:
    from webcam_module import WebcamCapture
    webcam = WebcamCapture(device_index=0, width=640, height=480, fps=15, lazy_hw=True)
    print("[WEBCAM] Webcam module loaded successfully")
except Exception as webcam_exc:
    WebcamCapture = None
    webcam = None
    print(f"[ERROR] Webcam import failed: {webcam_exc}")
    print("[ERROR] Make sure OpenCV is installed: pip3 install opencv-python-headless")

app = Flask(__name__)

@app.route('/')
def index():
    """Main webcam page."""
    if webcam is None:
        return render_template('webcam.html', error="Webcam module not available. Please install opencv-python-headless.")
    return render_template('webcam.html')

@app.route('/video_feed')
def video_feed():
    """MJPEG video streaming route."""
    if webcam is None:
        return Response("Webcam not available", status=503, mimetype='text/plain')
    
    # Ensure webcam is open
    if not webcam.is_open:
        if not webcam.open():
            return Response("Failed to open webcam", status=503, mimetype='text/plain')
    
    def generate():
        """Generator function for MJPEG streaming."""
        consecutive_errors = 0
        max_errors = 10
        
        while True:
            try:
                frame = webcam.read_frame()
                if frame is None:
                    consecutive_errors += 1
                    if consecutive_errors > max_errors:
                        # Send error message as text
                        error_msg = b'--frame\r\nContent-Type: text/plain\r\n\r\nWebcam error\r\n'
                        yield error_msg
                        time.sleep(1)
                        consecutive_errors = 0
                    else:
                        time.sleep(0.1)
                    continue
                
                consecutive_errors = 0
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                print(f"[WEBCAM] Stream error: {e}")
                time.sleep(0.5)
                consecutive_errors += 1
                if consecutive_errors > max_errors:
                    break
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/webcam/status')
def webcam_status():
    """Get webcam status."""
    if webcam is None:
        return jsonify({'error': 'Webcam not available'}), 503
    
    status = webcam.get_status()
    return jsonify(status)

@app.route('/api/webcam/config', methods=['POST'])
def webcam_config():
    """Update webcam configuration (frame rate, resolution)."""
    if webcam is None:
        return jsonify({'error': 'Webcam not available'}), 503
    
    try:
        data = request.get_json() or {}
        width = data.get('width')
        height = data.get('height')
        fps = data.get('fps')
        
        # Validate inputs
        if width is not None and (not isinstance(width, int) or width < 160 or width > 1920):
            return jsonify({'error': 'Invalid width (must be 160-1920)'}), 400
        if height is not None and (not isinstance(height, int) or height < 120 or height > 1080):
            return jsonify({'error': 'Invalid height (must be 120-1080)'}), 400
        if fps is not None and (not isinstance(fps, int) or fps < 1 or fps > 30):
            return jsonify({'error': 'Invalid FPS (must be 1-30)'}), 400
        
        success = webcam.update_config(width=width, height=height, fps=fps)
        
        if success:
            return jsonify({'message': 'Configuration updated', 'status': webcam.get_status()})
        else:
            return jsonify({'error': 'Failed to update configuration'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("BBBW Camera Server")
    print("=" * 50)
    
    if webcam is not None:
        print("[WEBCAM] Webcam ready (will open on first access)")
        print("[INFO] Connect your webcam to USB port")
    else:
        print("[ERROR] Webcam module not available!")
        print("[INFO] Install OpenCV: pip3 install opencv-python-headless")
        sys.exit(1)
    
    print("=" * 50)
    print("Starting server on http://0.0.0.0:5000")
    print("Access webcam at: http://<bbbw-ip>:5000")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        if webcam is not None:
            webcam.close()
        print("Camera server stopped. Goodbye!")

