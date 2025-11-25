#!/bin/bash
# Stream video using mjpg-streamer (if available)

echo "=========================================="
echo "MJPG-Streamer Video Stream"
echo "=========================================="

# Check if mjpg-streamer is installed
if ! command -v mjpg_streamer &> /dev/null; then
    echo "mjpg-streamer not found"
    echo ""
    echo "To install:"
    echo "  sudo apt install mjpg-streamer -y"
    echo ""
    echo "Or use the Python streamer instead:"
    echo "  python3 video_stream_simple.py"
    exit 1
fi

# Check if webcam exists
if [ ! -e /dev/video0 ]; then
    echo "✗ /dev/video0 not found"
    echo "Connect your webcam and try again"
    exit 1
fi

echo "Starting mjpg-streamer on port 8080..."
echo "Access at: http://<bbbw-ip>:8080/?action=stream"
echo "Press Ctrl+C to stop"
echo ""

mjpg_streamer -i "input_uvc.so -d /dev/video0 -r 640x480 -f 15" -o "output_http.so -p 8080 -w /usr/share/mjpg-streamer/www"

