#!/bin/bash
# Script to check what's using the I2C bus and help release it

echo "=== I2C Bus Diagnostic ==="
echo ""

# Check for processes using I2C
echo "1. Checking for processes using /dev/i2c-1..."
if command -v lsof &> /dev/null; then
    echo "   Using lsof:"
    sudo lsof /dev/i2c-1 2>/dev/null || echo "   No processes found with lsof"
else
    echo "   lsof not available"
fi

if command -v fuser &> /dev/null; then
    echo "   Using fuser:"
    sudo fuser /dev/i2c-1 2>/dev/null || echo "   No processes found with fuser"
else
    echo "   fuser not available"
fi

echo ""
echo "2. Checking for Python processes that might be using I2C..."
ps aux | grep -i python | grep -v grep | head -10

echo ""
echo "3. Checking I2C bus status..."
i2cdetect -y 1 2>/dev/null || echo "   i2cdetect failed (bus might be locked)"

echo ""
echo "4. Attempting to release I2C bus..."
# Try to open and immediately close the I2C device to release any stale locks
if [ -e /dev/i2c-1 ]; then
    echo "   Attempting to release /dev/i2c-1..."
    # This might require sudo
    python3 << 'EOF'
import os
import fcntl
try:
    fd = os.open('/dev/i2c-1', os.O_RDWR)
    os.close(fd)
    print("   Successfully opened and closed /dev/i2c-1")
except Exception as e:
    print(f"   Could not release: {e}")
EOF
else
    echo "   /dev/i2c-1 does not exist"
fi

echo ""
echo "=== Diagnostic Complete ==="
echo ""
echo "If the bus is still locked, try:"
echo "  1. Kill any Python processes: pkill -f python"
echo "  2. Wait a few seconds"
echo "  3. Try running your OLED test again"
echo ""
echo "The updated oled_simple.py should automatically use direct I2C file access"
echo "if smbus2 fails, which should bypass the lock issue."


