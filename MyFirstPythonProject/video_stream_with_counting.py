"""
Video Streaming Server with Person Counting
Integrates person counting API with video stream
"""
from flask import Flask, Response, jsonify
import subprocess
import threading
import time
import os
import signal
import sys
import site
import base64
import requests
from typing import Optional

# Ensure user site-packages (where pip installs to) are on sys.path
USER_SITE = os.path.expanduser("~/.local/lib/python3.7/site-packages")
if os.path.isdir(USER_SITE):
    site.addsitedir(USER_SITE)

try:
    from google.cloud import vision
    from google.oauth2 import service_account
except ImportError:
    vision = None  # type: ignore
    service_account = None  # type: ignore

app = Flask(__name__)

# Global state
streaming = False
capture_process = None
current_count = 0
last_count_update = 0

# ===== API CONFIGURATION =====
# Choose ONE of these APIs and configure it:

# Option 1: Google Vision API (Recommended)
GOOGLE_VISION_API_KEY = os.getenv('GOOGLE_VISION_API_KEY', 'YOUR_API_KEY_HERE')
USE_GOOGLE_VISION = True

# Option 2: Hugging Face (Free tier available)
HUGGINGFACE_API_TOKEN = os.getenv('HUGGINGFACE_API_TOKEN', 'YOUR_TOKEN_HERE')
USE_HUGGINGFACE = False

# Option 3: Azure Vision
AZURE_ENDPOINT = os.getenv('AZURE_ENDPOINT', '')
AZURE_KEY = os.getenv('AZURE_KEY', '')
USE_AZURE = False

# Analysis settings
ANALYZE_EVERY_N_FRAMES = 30  # Analyze every 30th frame (reduce API calls)
FRAME_COUNTER = 0

# Google Vision service account path discovery
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SA_PATH = os.path.join(PROJECT_ROOT, 'keys', 'sa-key.json')
GOOGLE_SERVICE_ACCOUNT_PATH = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
if not GOOGLE_SERVICE_ACCOUNT_PATH and os.path.exists(DEFAULT_SA_PATH):
    GOOGLE_SERVICE_ACCOUNT_PATH = DEFAULT_SA_PATH

VISION_CLIENT = None
GOOGLE_VISION_MODE = None  # service_account | api_key | None

if USE_GOOGLE_VISION:
    if GOOGLE_SERVICE_ACCOUNT_PATH:
        if vision is None or service_account is None:
            print("[WARNING] google-cloud-vision not installed. Install with: pip install google-cloud-vision google-auth")
        else:
            try:
                credentials = service_account.Credentials.from_service_account_file(GOOGLE_SERVICE_ACCOUNT_PATH)
                VISION_CLIENT = vision.ImageAnnotatorClient(credentials=credentials)
                GOOGLE_VISION_MODE = 'service_account'
                print(f"[INFO] Google Vision using service account at {GOOGLE_SERVICE_ACCOUNT_PATH}")
            except Exception as e:
                print(f"[WARNING] Failed to initialize Google Vision service account client: {e}")

    if GOOGLE_VISION_MODE is None and GOOGLE_VISION_API_KEY != 'YOUR_API_KEY_HERE':
        GOOGLE_VISION_MODE = 'api_key'
        print("[INFO] Google Vision falling back to API key mode")

    if GOOGLE_VISION_MODE is None:
        print("[WARNING] Google Vision is enabled but no credentials were found. Provide a service account JSON file or set GOOGLE_VISION_API_KEY.")

def count_people_google_vision(image_bytes: bytes, return_debug=False):
    """Count people using Google Vision API via service account or API key."""
    if GOOGLE_VISION_MODE is None:
        message = 'Google Vision not configured (missing service account or API key)'
        if return_debug:
            return -2, {'api': 'Google Vision', 'error': message}
        return -2

    if GOOGLE_VISION_MODE == 'service_account':
        if VISION_CLIENT is None or vision is None:
            message = 'google-cloud-vision client not initialized'
            if return_debug:
                return -2, {'api': 'Google Vision', 'error': message}
            return -2
        try:
            image = vision.Image(content=image_bytes)
            response = VISION_CLIENT.object_localization(image=image)
            objects = response.localized_object_annotations
            person_objects = [obj for obj in objects if obj.name.lower() == 'person']
            person_count = len(person_objects)

            if return_debug:
                return person_count, {
                    'api': 'Google Vision (service account)',
                    'status_code': 200,
                    'objects_found': len(objects),
                    'all_objects': [{'name': obj.name, 'score': obj.score} for obj in objects],
                    'person_objects': [{'name': obj.name, 'score': obj.score} for obj in person_objects]
                }
            return person_count
        except Exception as e:
            print(f"[ERROR] Google Vision (service account): {e}")
            if return_debug:
                return -1, {
                    'api': 'Google Vision (service account)',
                    'error': str(e)
                }
            return -1

    # API key fallback
    try:
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        payload = {
            'requests': [{
                'image': {'content': image_base64},
                'features': [{
                    'type': 'OBJECT_LOCALIZATION',
                    'maxResults': 50
                }]
            }]
        }

        response = requests.post(
            f'https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_VISION_API_KEY}',
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        response.raise_for_status()

        data = response.json()
        objects = data.get('responses', [{}])[0].get('localizedObjectAnnotations', [])
        person_count = sum(1 for obj in objects if obj['name'].lower() == 'person')

        if return_debug:
            return person_count, {
                'api': 'Google Vision (API key)',
                'status_code': response.status_code,
                'objects_found': len(objects),
                'all_objects': [{'name': obj['name'], 'score': obj.get('score', 0)} for obj in objects],
                'person_objects': [{'name': obj['name'], 'score': obj.get('score', 0)} for obj in objects if obj['name'].lower() == 'person'],
                'raw_response': data
            }

        return person_count
    except requests.exceptions.RequestException as e:
        error_msg = f"Request error: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_msg += f" | Response: {e.response.text}"
            except Exception:
                pass
        print(f"[ERROR] Google Vision (API key): {error_msg}")
        if return_debug:
            return -1, {'api': 'Google Vision (API key)', 'error': error_msg, 'status_code': getattr(e.response, 'status_code', None)}
        return -1
    except Exception as e:
        print(f"[ERROR] Google Vision (API key): {e}")
        if return_debug:
            return -1, {'api': 'Google Vision (API key)', 'error': str(e)}
        return -1

def count_people_huggingface(image_bytes: bytes, return_debug=False):
    """Count people using Hugging Face API"""
    try:
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
        
        response = requests.post(
            "https://api-inference.huggingface.co/models/facebook/detr-resnet-50",
            headers=headers,
            data=image_bytes,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        if isinstance(data, list):
            person_count = sum(
                1 for item in data 
                if isinstance(item, dict) and 
                item.get('label', '').lower() in ['person', 'people']
            )
            if return_debug:
                return person_count, {
                    'api': 'Hugging Face',
                    'status_code': response.status_code,
                    'detections': len(data),
                    'all_detections': data,
                    'person_detections': [item for item in data if isinstance(item, dict) and item.get('label', '').lower() in ['person', 'people']],
                    'raw_response': data
                }
            return person_count
        if return_debug:
            return 0, {'api': 'Hugging Face', 'status_code': response.status_code, 'message': 'No detections found', 'raw_response': data}
        return 0
    except Exception as e:
        error_msg = f"Request error: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_msg += f" | Response: {e.response.text}"
            except:
                pass
        print(f"[ERROR] Hugging Face: {error_msg}")
        if return_debug:
            return -1, {'api': 'Hugging Face', 'error': error_msg, 'status_code': getattr(e.response, 'status_code', None)}
        return -1

def count_people_azure(image_bytes: bytes, return_debug=False):
    """Count people using Azure Computer Vision"""
    try:
        url = f"{AZURE_ENDPOINT}/vision/v3.2/detect"
        headers = {
            'Ocp-Apim-Subscription-Key': AZURE_KEY,
            'Content-Type': 'application/octet-stream'
        }
        
        response = requests.post(url, headers=headers, data=image_bytes, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        objects = data.get('objects', [])
        person_count = sum(1 for obj in objects if obj.get('object', '').lower() == 'person')
        
        if return_debug:
            return person_count, {
                'api': 'Azure Vision',
                'status_code': response.status_code,
                'objects_found': len(objects),
                'all_objects': objects,
                'person_objects': [obj for obj in objects if obj.get('object', '').lower() == 'person'],
                'raw_response': data
            }
        
        return person_count
    except Exception as e:
        error_msg = f"Request error: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_msg += f" | Response: {e.response.text}"
            except:
                pass
        print(f"[ERROR] Azure Vision: {error_msg}")
        if return_debug:
            return -1, {'api': 'Azure Vision', 'error': error_msg, 'status_code': getattr(e.response, 'status_code', None)}
        return -1

def count_people(image_bytes: bytes, return_debug=False):
    """Count people using the configured API"""
    if USE_GOOGLE_VISION and GOOGLE_VISION_MODE is not None:
        return count_people_google_vision(image_bytes, return_debug)
    elif USE_HUGGINGFACE and HUGGINGFACE_API_TOKEN != 'YOUR_TOKEN_HERE':
        return count_people_huggingface(image_bytes, return_debug)
    elif USE_AZURE and AZURE_ENDPOINT and AZURE_KEY:
        return count_people_azure(image_bytes, return_debug)
    else:
        if return_debug:
            return -2, {'error': 'No API configured', 'configured_apis': {
                'google_vision_enabled': USE_GOOGLE_VISION,
                'google_vision_mode': GOOGLE_VISION_MODE,
                'huggingface': USE_HUGGINGFACE,
                'azure': USE_AZURE
            }}
        return -2  # Not configured

def capture_frame():
    """Capture a single frame using fswebcam."""
    try:
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
    """Generator function for MJPEG streaming with person counting."""
    global streaming, current_count, last_count_update, FRAME_COUNTER
    
    streaming = True
    print("[STREAM] Starting video stream with person counting...")
    
    while streaming:
        try:
            frame = capture_frame()
            if frame:
                # Periodically analyze frame for person counting
                FRAME_COUNTER += 1
                if FRAME_COUNTER >= ANALYZE_EVERY_N_FRAMES:
                    FRAME_COUNTER = 0
                    # Run counting in background to not block stream
                    def analyze_frame():
                        global current_count, last_count_update
                        result = count_people(frame, return_debug=False)
                        if isinstance(result, tuple):
                            count = result[0]
                        else:
                            count = result
                        if count >= 0:  # Valid count (not error)
                            current_count = count
                            last_count_update = time.time()
                            print(f"[INFO] People detected: {count}")
                    
                    # Run in thread to avoid blocking stream
                    threading.Thread(target=analyze_frame, daemon=True).start()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                time.sleep(0.1)
        except Exception as e:
            print(f"[ERROR] Stream error: {e}")
            time.sleep(0.5)
    
    print("[STREAM] Stream stopped")

@app.route('/')
def index():
    """HTML page with video stream and person count."""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>BBBW Video Stream - Person Counter</title>
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
                padding: 15px;
                background: #2a2a2a;
                border-radius: 4px;
            }
            .count-display {
                font-size: 48px;
                font-weight: bold;
                color: #4CAF50;
                margin: 10px 0;
            }
            .count-label {
                font-size: 18px;
                color: #aaa;
            }
            button {
                background: #4CAF50;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 16px;
                border-radius: 4px;
                cursor: pointer;
                margin: 10px;
            }
            button:hover {
                background: #45a049;
            }
            button:disabled {
                background: #666;
                cursor: not-allowed;
            }
            #debugOutput {
                margin: 20px;
                padding: 15px;
                background: #1a1a1a;
                border: 1px solid #333;
                border-radius: 4px;
                text-align: left;
                max-height: 400px;
                overflow-y: auto;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                display: none;
            }
            #debugOutput pre {
                margin: 0;
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            .debug-header {
                color: #4CAF50;
                font-weight: bold;
                margin-bottom: 10px;
            }
        </style>
        <script>
            function updateCount() {
                fetch('/person_count')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('personCount').textContent = data.count;
                        document.getElementById('lastUpdate').textContent = 
                            'Last updated: ' + (data.last_update || 'Never');
                    })
                    .catch(err => console.error('Error:', err));
            }
            
            function analyzeManual() {
                const button = document.getElementById('analyzeBtn');
                const debugOutput = document.getElementById('debugOutput');
                const debugContent = document.getElementById('debugContent');
                
                button.disabled = true;
                button.textContent = 'Analyzing...';
                debugOutput.style.display = 'block';
                debugContent.textContent = 'Capturing frame and sending to API...';
                
                fetch('/analyze_manual')
                    .then(response => response.json())
                    .then(data => {
                        button.disabled = false;
                        button.textContent = 'Analyze Frame Now';
                        
                        let output = '=== ANALYSIS RESULT ===\\n';
                        output += 'Timestamp: ' + new Date().toLocaleString() + '\\n';
                        output += 'People Count: ' + data.count + '\\n';
                        output += 'API Used: ' + (data.debug_info?.api || 'Unknown') + '\\n';
                        output += 'Status Code: ' + (data.debug_info?.status_code || 'N/A') + '\\n\\n';
                        
                        if (data.debug_info?.error) {
                            output += 'ERROR: ' + data.debug_info.error + '\\n\\n';
                        }
                        
                        if (data.debug_info?.objects_found !== undefined) {
                            output += 'Total Objects Found: ' + data.debug_info.objects_found + '\\n';
                            output += 'Person Objects: ' + data.debug_info.person_objects?.length + '\\n\\n';
                        }
                        
                        if (data.debug_info?.all_objects) {
                            output += '=== ALL OBJECTS DETECTED ===\\n';
                            data.debug_info.all_objects.forEach((obj, idx) => {
                                output += (idx + 1) + '. ' + obj.name + ' (score: ' + (obj.score || 'N/A') + ')\\n';
                            });
                            output += '\\n';
                        }
                        
                        if (data.debug_info?.person_objects && data.debug_info.person_objects.length > 0) {
                            output += '=== PERSON OBJECTS ===\\n';
                            data.debug_info.person_objects.forEach((obj, idx) => {
                                output += (idx + 1) + '. ' + obj.name + ' (score: ' + (obj.score || 'N/A') + ')\\n';
                            });
                            output += '\\n';
                        }
                        
                        if (data.debug_info?.raw_response) {
                            output += '=== RAW API RESPONSE ===\\n';
                            output += JSON.stringify(data.debug_info.raw_response, null, 2);
                        }
                        
                        debugContent.textContent = output;
                        
                        // Update the count display
                        if (data.count >= 0) {
                            document.getElementById('personCount').textContent = data.count;
                            document.getElementById('lastUpdate').textContent = 
                                'Last updated: ' + new Date().toLocaleTimeString();
                        }
                    })
                    .catch(err => {
                        button.disabled = false;
                        button.textContent = 'Analyze Frame Now';
                        debugContent.textContent = 'ERROR: ' + err.message;
                        console.error('Error:', err);
                    });
            }
            
            // Update count every 2 seconds
            setInterval(updateCount, 2000);
            updateCount(); // Initial update
        </script>
    </head>
    <body>
        <h1>BBBW Video Stream - Person Counter</h1>
        <div class="status">
            <div class="count-label">People Detected</div>
            <div class="count-display" id="personCount">-</div>
            <div class="count-label" id="lastUpdate">Loading...</div>
        </div>
        <button id="analyzeBtn" onclick="analyzeManual()">Analyze Frame Now</button>
        <div id="debugOutput">
            <div class="debug-header">Debug Output:</div>
            <pre id="debugContent">Click "Analyze Frame Now" to see debug information...</pre>
        </div>
        <img id="videoStream" src="/video_feed" alt="Video Stream" />
        <div class="status">Streaming from Logitech C615 HD</div>
    </body>
    </html>
    '''

@app.route('/video_feed')
def video_feed():
    """MJPEG video streaming route."""
    return Response(generate_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/person_count')
def person_count():
    """API endpoint to get current person count."""
    global current_count, last_count_update
    return jsonify({
        'count': current_count if current_count >= 0 else 'N/A',
        'last_update': time.strftime('%H:%M:%S', time.localtime(last_count_update)) if last_count_update > 0 else None,
        'status': 'active' if streaming else 'inactive'
    })

@app.route('/analyze_manual')
def analyze_manual():
    """Manual analysis endpoint with full debug output."""
    try:
        # Capture a fresh frame
        frame = capture_frame()
        if not frame:
            return jsonify({
                'count': -1,
                'error': 'Failed to capture frame',
                'debug_info': {'error': 'Frame capture returned None'}
            }), 500
        
        # Analyze with debug info
        result = count_people(frame, return_debug=True)
        
        if isinstance(result, tuple):
            count, debug_info = result
        else:
            count = result
            debug_info = {'message': 'No debug info available'}
        
        # Update global state if successful
        global current_count, last_count_update
        if count >= 0:
            current_count = count
            last_count_update = time.time()
        
        return jsonify({
            'count': count,
            'debug_info': debug_info,
            'frame_size': len(frame),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({
            'count': -1,
            'error': str(e),
            'debug_info': {'error': f'Exception: {str(e)}', 'type': type(e).__name__}
        }), 500

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
    
    # Check API configuration
    if USE_GOOGLE_VISION and GOOGLE_VISION_MODE is None:
        print("[WARNING] Google Vision credentials not configured!")
        print("[INFO] Provide a service account JSON (GOOGLE_APPLICATION_CREDENTIALS or keys/sa-key.json) or set GOOGLE_VISION_API_KEY.")
    elif USE_HUGGINGFACE and HUGGINGFACE_API_TOKEN == 'YOUR_TOKEN_HERE':
        print("[WARNING] Hugging Face API token not configured!")
        print("[INFO] Set HUGGINGFACE_API_TOKEN environment variable or edit this file")
    elif USE_AZURE and (not AZURE_ENDPOINT or not AZURE_KEY):
        print("[WARNING] Azure credentials not configured!")
    else:
        print("[INFO] Person counting API configured")
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=" * 50)
    print("BBBW Video Stream Server with Person Counting")
    print("=" * 50)
    print("Access at: http://<bbbw-ip>:5000")
    print("Person count API: http://<bbbw-ip>:5000/person_count")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        pass
    finally:
        streaming = False
        print("\n[INFO] Server stopped")

