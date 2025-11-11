"""
VibraSense vibration sensor module for Click Board.

Detects vibration using GPIO input, with power control via GPIO output.
"""

import time
from typing import Optional
from slot_config import get_slot_pin


class VibraSense:
    """Vibration detection sensor module."""
    
    def __init__(self, slot: int, *, lazy_hw: bool = False):
        """
        Initialize the VibraSense sensor.
        
        Args:
            slot: Click board slot number (1-4)
            lazy_hw: If True, don't initialize hardware until open() is called
        """
        self._slot = slot
        self._input_pin = get_slot_pin(slot, "input")
        self._output_pin = get_slot_pin(slot, "output")
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
        GPIO.setup(self._output_pin, GPIO.OUT)
        GPIO.setup(self._input_pin, GPIO.IN)
        GPIO.output(self._output_pin, GPIO.HIGH)
    
    def close(self):
        """Close the GPIO connection."""
        if self._GPIO is not None:
            self._GPIO.output(self._output_pin, self._GPIO.LOW)
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
        Read vibration detection state.
        
        Returns:
            True if vibration detected, False otherwise
        """
        if self._GPIO is None:
            self.open()
        return bool(self._GPIO.input(self._input_pin))
    
    def is_vibration_detected(self) -> bool:
        """
        Check if vibration is detected.
        
        Returns:
            True if vibration detected, False otherwise
        """
        return self.read()
    
    def enable(self):
        """Enable the sensor (power on)."""
        if self._GPIO is None:
            self.open()
        self._GPIO.output(self._output_pin, self._GPIO.HIGH)
    
    def disable(self):
        """Disable the sensor (power off)."""
        if self._GPIO is None:
            self.open()
        self._GPIO.output(self._output_pin, self._GPIO.LOW)
    
    def poll(self, interval_s: float = 0.3, count: Optional[int] = None):
        """
        Poll vibration sensor and print status.
        
        Args:
            interval_s: Time between polls in seconds
            count: Number of polls (None = infinite)
        """
        i = 0
        while count is None or i < count:
            if self.read():
                print("Vibration is Detected")
            else:
                print("No Vibration is Detected")
            time.sleep(interval_s)
            i += 1


if __name__ == "__main__":
    # Example usage
    sensor = VibraSense(slot=2)
    try:
        sensor.poll(interval_s=0.3, count=10)
    except KeyboardInterrupt:
        print("\nStopped")
    finally:
        sensor.close()

