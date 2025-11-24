"""
Direct v4l2 webcam test - no OpenCV needed
Uses v4l2 directly via Python
"""
import subprocess
import os
import time

def test_v4l2_capture():
    """Test webcam capture using v4l2 directly."""
    print("=" * 50)
    print("V4L2 Direct Webcam Test")
    print("=" * 50)
    
    if not os.path.exists('/dev/video0'):
        print("✗ /dev/video0 not found")
        return False
    
    print("\n1. Checking device info...")
    try:
        result = subprocess.run(['v4l2-ctl', '--device=/dev/video0', '--all'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("⚠ v4l2-ctl not available or device not responding")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n2. Testing fswebcam with different settings...")
    
    # Try with skip frames (let camera initialize)
    for i, settings in enumerate([
        {'size': '640x480', 'skip': 10, 'delay': 2},
        {'size': '320x240', 'skip': 10, 'delay': 2},
        {'size': '640x480', 'skip': 30, 'delay': 3},
    ]):
        filename = f'webcam_test_v4l2_{i+1}.jpg'
        print(f"\n  Trying {settings['size']} with {settings['skip']} skip frames...")
        
        try:
            cmd = [
                'fswebcam',
                '-d', '/dev/video0',
                '-r', settings['size'],
                '--no-banner',
                '--skip', str(settings['skip']),
                '--delay', str(settings['delay']),
                filename
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if os.path.exists(filename):
                size = os.path.getsize(filename)
                print(f"  ✓ Captured {filename} ({size} bytes)")
                
                # Check if image is not just black (basic check)
                if size > 5000:  # Reasonable size for a real image
                    print(f"  ✓ Image size looks reasonable")
                else:
                    print(f"  ⚠ Image might be blank (very small size)")
            else:
                print(f"  ✗ Failed to create {filename}")
                if result.stderr:
                    print(f"  Error: {result.stderr}")
        except subprocess.TimeoutExpired:
            print(f"  ✗ Timeout")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print("\n" + "=" * 50)
    print("Check the webcam_test_v4l2_*.jpg files")
    print("=" * 50)
    return True

if __name__ == '__main__':
    test_v4l2_capture()

