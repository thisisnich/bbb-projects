#!/bin/bash
# Better webcam test - tries different settings

echo "=========================================="
echo "Better Webcam Test"
echo "=========================================="

if [ ! -e /dev/video0 ]; then
    echo "✗ /dev/video0 not found"
    exit 1
fi

echo ""
echo "1. Checking video device capabilities..."
if command -v v4l2-ctl &> /dev/null; then
    v4l2-ctl --device=/dev/video0 --list-formats-ext
else
    echo "⚠ v4l2-ctl not available"
fi

echo ""
echo "2. Testing different capture methods..."

# Method 1: fswebcam with delay and different settings
if command -v fswebcam &> /dev/null; then
    echo "Trying fswebcam with 2 second delay..."
    fswebcam -d /dev/video0 -r 640x480 --no-banner --skip 10 webcam_test1.jpg 2>&1
    if [ -f webcam_test1.jpg ]; then
        size=$(stat -c%s webcam_test1.jpg)
        echo "✓ Captured webcam_test1.jpg ($size bytes)"
    fi
    
    echo ""
    echo "Trying fswebcam with 320x240..."
    fswebcam -d /dev/video0 -r 320x240 --no-banner --skip 10 webcam_test2.jpg 2>&1
    if [ -f webcam_test2.jpg ]; then
        size=$(stat -c%s webcam_test2.jpg)
        echo "✓ Captured webcam_test2.jpg ($size bytes)"
    fi
    
    echo ""
    echo "Trying fswebcam with MJPEG format..."
    fswebcam -d /dev/video0 -r 640x480 --no-banner --skip 10 -F 1 webcam_test3.jpg 2>&1
    if [ -f webcam_test3.jpg ]; then
        size=$(stat -c%s webcam_test3.jpg)
        echo "✓ Captured webcam_test3.jpg ($size bytes)"
    fi
else
    echo "⚠ fswebcam not installed"
    echo "  Install with: sudo apt install fswebcam"
fi

# Method 2: Try ffmpeg if available
echo ""
if command -v ffmpeg &> /dev/null; then
    echo "Trying ffmpeg capture..."
    timeout 3 ffmpeg -f v4l2 -input_format mjpeg -video_size 640x480 -i /dev/video0 -frames:v 1 -y webcam_test4.jpg 2>&1 | tail -5
    if [ -f webcam_test4.jpg ]; then
        size=$(stat -c%s webcam_test4.jpg)
        echo "✓ Captured webcam_test4.jpg ($size bytes)"
    fi
else
    echo "⚠ ffmpeg not available"
fi

echo ""
echo "=========================================="
echo "Check the webcam_test*.jpg files"
echo "=========================================="

