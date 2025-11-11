"""
Motion sensor module for Click Board.

Detects motion using a GPIO input pin.
"""

import time
from typing import Optional
from slot_config import get_slot_pin


class MotionSensor:
    """Motion detection sensor module."""
    
    def __init__(self, slot: int, *, lazy_hw: bool = False):
        """
        Initialize the motion sensor.
        
        Args:
            slot: Click board slot number (1-4)
            lazy_hw: If True, don't initialize hardware until open() is called
        """
        self._slot = slot
        self._pin = get_slot_pin(slot, "input")
        self._lazy_hw = lazy_hw
        self._GPIO = None
        
        if not self._lazy_hw:
            self.open()
    
    def open(self):
        """Open the GPIO connection and initialize."""
        if self._GPIO is not None:
            return
        
        import Adafruit_BBIO.GPIO as GPIO
        self._GPIO = GPIO
        GPIO.setup(self._pin, GPIO.IN)
    
    def close(self):
        """Close the GPIO connection."""
        self._GPIO = None
    
    def __enter__(self):
        """Context manager entry."""
        if self._GPIO is None:
            self.open()
        return self
    
    def __exit__(self, exc_type, exc, tb):
        """Context manager exit."""
        self.close()
    
    def read(self) -> bool:
        """
        Read motion detection state.
        
        Returns:
            True if motion detected, False otherwise
        """
        if self._GPIO is None:
            self.open()
        return bool(self._GPIO.input(self._pin))
    
    def is_motion_detected(self) -> bool:
        """
        Check if motion is detected.
        
        Returns:
            True if motion detected, False otherwise
        """
        return self.read()
    
    def poll(self, interval_s: float = 0.3, count: Optional[int] = None):
        """
        Poll motion sensor and print status.
        
        Args:
            interval_s: Time between polls in seconds
            count: Number of polls (None = infinite)
        """
        i = 0
        while count is None or i < count:
            if self.read():
                print("Motion is Detected")
            else:
                print("No Motion is Detected")
            time.sleep(interval_s)
            i += 1


if __name__ == "__main__":
    # Example usage
    sensor = MotionSensor(slot=1)
    try:
        sensor.poll(interval_s=0.3, count=10)
    except KeyboardInterrupt:
        print("\nStopped")
    finally:
        sensor.close()

