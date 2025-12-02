#!/usr/bin/env python3
"""
Force release I2C bus by closing any open file descriptors.
This helps when CircuitPython's busio.I2C leaves the bus locked.
"""
import os
import sys

def force_release_i2c(bus_num=1):
    """Try to force release I2C bus."""
    i2c_dev = f"/dev/i2c-{bus_num}"
    
    if not os.path.exists(i2c_dev):
        print(f"ERROR: {i2c_dev} does not exist")
        return False
    
    print(f"Attempting to force release {i2c_dev}...")
    
    # Method 1: Try to open and immediately close (might release lock)
    try:
        fd = os.open(i2c_dev, os.O_RDWR)
        os.close(fd)
        print(f"  Method 1: Opened and closed {i2c_dev}")
        return True
    except OSError as e:
        print(f"  Method 1 failed: {e}")
    
    # Method 2: Check for processes using it
    try:
        import subprocess
        result = subprocess.run(['lsof', i2c_dev], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            print(f"  Processes using {i2c_dev}:")
            print(result.stdout)
        else:
            print(f"  No processes found using {i2c_dev} (but bus is still locked)")
    except:
        pass
    
    # Method 3: Try with a delay
    import time
    print("  Waiting 1 second and retrying...")
    time.sleep(1)
    try:
        fd = os.open(i2c_dev, os.O_RDWR)
        os.close(fd)
        print(f"  Method 3: Successfully opened after delay")
        return True
    except OSError as e:
        print(f"  Method 3 failed: {e}")
    
    print(f"  WARNING: Could not force release {i2c_dev}")
    print(f"  You may need to reboot the BBBW to clear the lock")
    return False

if __name__ == "__main__":
    bus_num = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    success = force_release_i2c(bus_num)
    sys.exit(0 if success else 1)


