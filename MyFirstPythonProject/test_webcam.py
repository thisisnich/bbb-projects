"""
Simple Webcam Test - Just verify BBBW can see the webcam
Uses v4l2 (Video4Linux2) directly - no OpenCV needed
"""
import subprocess
import sys
import os

def test_webcam_detection():
    """Test if webcam is detected via USB."""
    print("=" * 50)
    print("Testing Webcam Detection")
    print("=" * 50)
    
    # Check USB devices
    print("\n1. Checking USB devices...")
    try:
        result = subprocess.run(['lsusb'], capture_output=True, text=True)
        print(result.stdout)
        if 'Logitech' in result.stdout or '046d' in result.stdout:
            print("✓ Logitech webcam detected!")
        else:
            print("✗ Logitech webcam not found in USB devices")
    except Exception as e:
        print(f"Error: {e}")
    
    # Check video devices
    print("\n2. Checking video devices...")
    try:
        if os.path.exists('/dev/video0'):
            print("✓ /dev/video0 exists")
            
            # Get device info
            result = subprocess.run(['v4l2-ctl', '--device=/dev/video0', '--info'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✓ Video device info:")
                print(result.stdout)
            else:
                print("⚠ Could not get device info (v4l2-ctl may not be installed)")
        else:
            print("✗ /dev/video0 not found")
    except Exception as e:
        print(f"Error: {e}")
    
    # Try to capture a test frame using v4l2
    print("\n3. Testing frame capture...")
    try:
        # Use fswebcam if available (simple, no dependencies)
        result = subprocess.run(['which', 'fswebcam'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ fswebcam found - trying to capture test image...")
            test_image = 'webcam_test.jpg'
            result = subprocess.run(['fswebcam', '-r', '640x480', '--no-banner', test_image], 
                                  capture_output=True, text=True, timeout=5)
            if os.path.exists(test_image):
                size = os.path.getsize(test_image)
                print(f"✓ Successfully captured test image! ({size} bytes)")
                print(f"  Image saved to: {os.path.abspath(test_image)}")
                return True
            else:
                print("✗ Failed to capture image")
        else:
            print("⚠ fswebcam not installed")
            print("  Install with: sudo apt install fswebcam")
    except subprocess.TimeoutExpired:
        print("✗ Timeout while capturing image")
    except Exception as e:
        print(f"Error: {e}")
    
    # Try Python with v4l2 if available
    print("\n4. Testing Python v4l2 access...")
    try:
        import fcntl
        import struct
        
        # Try to open video device
        with open('/dev/video0', 'rb') as v4l2:
            # Try to query capabilities
            print("✓ Can open /dev/video0")
            print("  Webcam is accessible!")
            return True
    except FileNotFoundError:
        print("✗ /dev/video0 not found")
    except PermissionError:
        print("⚠ Permission denied - try running with sudo")
    except Exception as e:
        print(f"Error: {e}")
    
    return False

if __name__ == '__main__':
    success = test_webcam_detection()
    print("\n" + "=" * 50)
    if success:
        print("✓ Webcam test PASSED - BBBW can see the webcam!")
    else:
        print("✗ Webcam test had issues - check output above")
    print("=" * 50)

