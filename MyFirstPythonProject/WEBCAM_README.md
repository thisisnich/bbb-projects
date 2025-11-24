# BBBW Webcam Streaming

Webcam streaming functionality for BeagleBone Black Wireless (BBBW) using Logitech C615 HD webcam.

## Overview

This project provides webcam streaming capabilities for the BBBW, allowing you to:
- Capture video from a USB webcam (Logitech C615 HD)
- Stream video via MJPEG over HTTP
- View the stream in a web browser
- Adjust resolution and frame rate settings

## Hardware Requirements

- **BeagleBone Black Wireless (BBBW)**
- **USB Webcam**: Logitech C615 HD (or any UVC-compatible webcam)
- **Network**: BBBW connected via WiFi or USB network

## Software Requirements

### Required Packages

```bash
# Install OpenCV (headless version - no GUI dependencies)
pip3 install --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host www.piwheels.org opencv-python-headless==3.4.3.18

# Install fswebcam (for testing)
sudo apt install fswebcam -y
```

**Note**: Due to broken Debian Buster repositories, use pip with trusted-host flags. The 3.4.3.18 version works best on BBBW.

### Python Dependencies

- Flask (already installed)
- opencv-python-headless==3.4.3.18
- numpy (usually pre-installed)

## Files

- **`webcam_module.py`** - Webcam capture module with configurable settings
- **`camServer.py`** - Standalone camera server (webcam only)
- **`WebServer.py`** - Full server (includes webcam + other features)
- **`templates/webcam.html`** - Web interface for viewing stream
- **`test_webcam.py`** - Python test script
- **`test_webcam_v4l2.py`** - Advanced v4l2 test script
- **`simple_cam_test.sh`** - Simple bash test script
- **`test_webcam_better.sh`** - Advanced bash test script

## Quick Start

### 1. Connect Webcam

Plug your Logitech C615 HD webcam into the BBBW USB port.

### 2. Verify Webcam Detection

```bash
# Check USB devices
lsusb | grep Logitech

# Check video device
ls -l /dev/video0
```

### 3. Test Webcam Capture

```bash
cd /var/lib/cloud9/MyFirstPythonProject

# Simple test
chmod +x simple_cam_test.sh
./simple_cam_test.sh

# Or better test (tries multiple settings)
chmod +x test_webcam_better.sh
./test_webcam_better.sh
```

This will create test images (`webcam_test*.jpg`) in the current directory.

### 4. Start Camera Server

```bash
# Standalone camera server (webcam only)
python3 camServer.py

# Or full server (webcam + LED + motion detection)
python3 WebServer.py
```

### 5. Access Webcam Stream

Open your web browser and navigate to:

- **USB Network**: `http://192.168.7.2:5000/webcam`
- **WiFi Network**: `http://<your-bbbw-wifi-ip>:5000/webcam`

To find your WiFi IP:
```bash
hostname -I
```

## Usage

### Standalone Camera Server

```bash
python3 camServer.py
```

Features:
- Webcam streaming only
- Lightweight and fast
- Access at `http://<bbbw-ip>:5000`

### Full Server (with other features)

```bash
python3 WebServer.py
```

Features:
- Webcam streaming
- LED control
- Motion detection
- 8x8 LED matrix control
- Access at `http://<bbbw-ip>:5000`

### Web Interface

The web interface (`/webcam`) provides:
- Live video stream
- Resolution adjustment (320x240 to 1280x720)
- Frame rate adjustment (5-30 fps)
- Status indicators
- Real-time settings display

### API Endpoints

- `GET /webcam` - Web interface
- `GET /video_feed` - MJPEG stream endpoint
- `GET /api/webcam/status` - Get webcam status
- `POST /api/webcam/config` - Update settings (JSON: `{"width": 640, "height": 480, "fps": 15}`)

## Configuration

### Default Settings

- **Resolution**: 640x480
- **Frame Rate**: 15 fps
- **Device**: /dev/video0
- **JPEG Quality**: 85%

### Adjusting Settings

1. **Via Web Interface**: Use the controls on the `/webcam` page
2. **Via API**: POST to `/api/webcam/config` with JSON body
3. **In Code**: Modify `WebcamCapture` initialization in `camServer.py` or `WebServer.py`

## Troubleshooting

### Black/Blank Images

If you get black images:
- Add delay: Use `--skip` and `--delay` options in fswebcam
- Try different resolutions
- Check lighting conditions
- Verify webcam is properly connected

### OpenCV Import Errors

If you see `libavcodec.so.58` or similar errors:
- Use OpenCV 3.4.3.18 (older version with fewer dependencies)
- Install with trusted-host flags (see Software Requirements)

### Webcam Not Detected

```bash
# Check USB
lsusb

# Check video device
ls -l /dev/video*

# Check permissions
ls -l /dev/video0
```

### Port Already in Use

If port 5000 is already in use:
- Stop other Flask servers
- Or modify the port in `camServer.py`: `app.run(host='0.0.0.0', port=5001)`

## Testing

### Basic Test

```bash
# Capture single image
fswebcam -d /dev/video0 -r 640x480 --no-banner --skip 30 --delay 3 webcam_test.jpg
```

### Advanced Test

```bash
# Run comprehensive test
./test_webcam_better.sh
```

This creates multiple test images with different settings.

## Performance Tips

- **Lower resolution** = Less CPU usage (try 320x240 if 640x480 is too slow)
- **Lower frame rate** = Less CPU usage (try 10-15 fps)
- **Close other applications** to free up resources
- **Use standalone server** (`camServer.py`) for best performance

## Network Access

### Local Network

The server listens on `0.0.0.0:5000`, so it's accessible from any device on your local network.

### Public Internet (Future)

To make it accessible from outside your network:
- Set up port forwarding on your router
- Or use a tunneling service like ngrok: `ngrok http 5000`

## Future Enhancements

- Google AI Studio Pro integration for object detection
- Scene analysis
- Face recognition
- Recording/saving video
- Multiple webcam support

## Notes

- OpenCV 3.4.3.18 is used due to compatibility with BBBW's older libraries
- The webcam module uses lazy initialization (opens on first use)
- MJPEG streaming is used for browser compatibility
- All test images are saved in the current working directory

## Support

For issues:
1. Check webcam detection: `lsusb` and `ls -l /dev/video0`
2. Test with fswebcam first
3. Check server logs for errors
4. Verify OpenCV installation: `python3 -c "import cv2; print(cv2.__version__)"`

