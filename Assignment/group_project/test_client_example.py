"""
Example test client for connecting to the webserver
Group members can use this as a template to test their BBBW modules
"""
import socketio
from datetime import datetime
import time
import random

# Change this to your server IP
SERVER_URL = 'http://192.168.68.73:5000'

sio = socketio.Client()

@sio.event
def connect():
    print(f'[{datetime.now()}] Connected to server!')
    # Register this module
    sio.emit('module_register', {
        'module_id': 'test_module_1',
        'module_type': 'crowd_detection',  # Change to 'environment' or 'feedback' to test other modules
        'timestamp': datetime.now().isoformat()
    })

@sio.event
def disconnect():
    print(f'[{datetime.now()}] Disconnected from server')

# --- EXAMPLE 1: CROWD DETECTION MODULE ---
def test_crowd_module():
    """Test sending crowd detection data"""
    try:
        sio.connect(SERVER_URL)
        print("Sending crowd detection data...")
        
        for i in range(10):
            sio.emit('CrowdDataEvent', {
                'module_id': 'crowd_unit_1',
                'court_id': 'basketball_a',
                'timestamp': datetime.now().isoformat(),
                'data': {
                    'people_count': random.randint(0, 15),
                    'crowd_level': random.choice(['empty', 'light', 'normal', 'busy', 'full']),
                    'noise_db': random.randint(40, 90),
                    'motion_detected': random.choice([True, False]),
                    'proximity_triggered': random.choice([True, False]),
                    'confidence': random.uniform(0.7, 1.0)
                }
            })
            print(f"Sent crowd data #{i+1}")
            time.sleep(2)
        
        sio.disconnect()
    except Exception as e:
        print(f"Error: {e}")

# --- EXAMPLE 2: ENVIRONMENT MODULE ---
def test_environment_module():
    """Test sending environment sensor data"""
    try:
        sio.connect(SERVER_URL)
        print("Sending environment data...")
        
        for i in range(10):
            sio.emit('EnvironmentDataEvent', {
                'module_id': 'environment_unit_2',
                'timestamp': datetime.now().isoformat(),
                'data': {
                    'temperature_c': random.randint(20, 35),
                    'humidity_percent': random.randint(40, 90),
                    'pressure_hpa': random.randint(1000, 1020),
                    'voc_level': random.choice(['good', 'moderate', 'poor']),
                    'voc_reading': random.randint(100, 500),
                    'uv_index': random.randint(0, 11),
                    'comfort_score': round(random.uniform(1.0, 5.0), 1),
                    'playable': True,
                    'warnings': random.choice([[], ['high_uv'], ['high_heat'], ['high_uv', 'high_heat']]),
                    'recommendations': ['use_sunscreen', 'stay_hydrated']
                }
            })
            print(f"Sent environment data #{i+1}")
            time.sleep(2)
        
        sio.disconnect()
    except Exception as e:
        print(f"Error: {e}")

# --- EXAMPLE 3: FEEDBACK MODULE ---
def test_feedback_module():
    """Test sending feedback data"""
    try:
        sio.connect(SERVER_URL)
        print("Sending feedback data...")
        
        # Test rating feedback
        sio.emit('FeedbackDataEvent', {
            'module_id': 'feedback_kiosk_3',
            'court_id': 'basketball_a',
            'timestamp': datetime.now().isoformat(),
            'data': {
                'report_type': 'rating',
                'question_id': 'overall_quality',
                'question_text': 'How would you rate the overall court quality?',
                'rating': random.randint(1, 5),
                'rating_scale': '1-5',
                'interaction_time_seconds': random.randint(5, 15),
                'gesture_used': True
            }
        })
        print("Sent rating feedback")
        time.sleep(2)
        
        # Test text feedback
        sio.emit('FeedbackDataEvent', {
            'module_id': 'feedback_kiosk_3',
            'court_id': 'basketball_a',
            'timestamp': datetime.now().isoformat(),
            'data': {
                'report_type': 'text',
                'question_id': 'maintenance_issue',
                'question_text': 'Report a maintenance issue',
                'text_response': 'Net is broken on the north side',
                'issue_category': 'net_broken',
                'priority': 'medium',
                'interaction_time_seconds': 12,
                'gesture_used': True
            }
        })
        print("Sent text feedback")
        time.sleep(2)
        
        sio.disconnect()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("BBBW Module Test Client")
    print("=" * 60)
    print("\nChoose test module:")
    print("1. Crowd Detection")
    print("2. Environment Sensors")
    print("3. Feedback")
    print("\nOr modify this file to match your module type!")
    print("=" * 60)
    
    choice = input("\nEnter choice (1-3) or press Enter to test all: ").strip()
    
    if choice == '1':
        test_crowd_module()
    elif choice == '2':
        test_environment_module()
    elif choice == '3':
        test_feedback_module()
    else:
        print("\nTesting all modules...")
        test_crowd_module()
        time.sleep(1)
        test_environment_module()
        time.sleep(1)
        test_feedback_module()

