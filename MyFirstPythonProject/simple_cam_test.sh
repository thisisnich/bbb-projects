#!/bin/bash
# Simple webcam test script - no Python dependencies needed

echo "=========================================="
echo "Simple Webcam Test"
echo "=========================================="

echo ""
echo "1. Checking USB devices..."
lsusb | grep -i logitech || echo "Logitech webcam not found in lsusb"

echo ""
echo "2. Checking video devices..."
if [ -e /dev/video0 ]; then
    echo "✓ /dev/video0 exists"
    ls -l /dev/video0
else
    echo "✗ /dev/video0 not found"
fi

echo ""
echo "3. Testing with fswebcam (if available)..."
if command -v fswebcam &> /dev/null; then
    echo "Capturing test image..."
    fswebcam -r 640x480 --no-banner webcam_test.jpg 2>&1
    if [ -f webcam_test.jpg ]; then
        echo "✓ SUCCESS! Test image captured at webcam_test.jpg"
        ls -lh webcam_test.jpg
    else
        echo "✗ Failed to capture image"
    fi
else
    echo "⚠ fswebcam not installed"
    echo "  Install with: sudo apt install fswebcam"
fi

echo ""
echo "=========================================="

