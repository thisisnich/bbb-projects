"""
Flame sensor module for Click Board.

Detects flame using an analog flame sensor via ADC.
"""

import time
from typing import Optional
from slot_config import get_slot_pin


class FlameSensor:
    """Flame detection sensor module."""
    
    def __init__(self, slot: int, *, lazy_hw: bool = False):
        """
        Initialize the flame sensor.
        
        Args:
            slot: Click board slot number (1-4)
            lazy_hw: If True, don't initialize hardware until open() is called
        """
        self._slot = slot
        self._pin = get_slot_pin(slot, "adc")
        self._lazy_hw = lazy_hw
        self._ADC = None
        
        if not self._lazy_hw:
            self.open()
    
    def open(self):
        """Open the ADC connection and initialize."""
        if self._ADC is not None:
            return
        
        import Adafruit_BBIO.ADC as ADC
        self._ADC = ADC
        ADC.setup()
    
    def close(self):
        """Close the ADC connection."""
        self._ADC = None
    
    def __enter__(self):
        """Context manager entry."""
        if self._ADC is None:
            self.open()
        return self
    
    def __exit__(self, exc_type, exc, tb):
        """Context manager exit."""
        self.close()
    
    def read_digital(self) -> float:
        """
        Read digital value from ADC.
        
        Returns:
            Digital value (0.0 to 1.0)
        """
        if self._ADC is None:
            self.open()
        return self._ADC.read(self._pin)
    
    def read_voltage(self) -> float:
        """
        Read analog voltage from ADC.
        
        Returns:
            Voltage in volts
        """
        digital_value = self.read_digital()
        # Voltage calculation: (DigitalValue * 1.8) * (2200 / 1200)
        analog_voltage = (digital_value * 1.8) * (2200 / 1200)
        return analog_voltage
    
    def read(self) -> dict:
        """
        Read all sensor values.
        
        Returns:
            Dictionary with digital_value and voltage
        """
        digital_value = self.read_digital()
        voltage = self.read_voltage()
        
        return {
            "digital_value": digital_value,
            "voltage": voltage
        }
    
    def is_flame_detected(self, threshold: float = 0.5) -> bool:
        """
        Check if flame is detected based on voltage threshold.
        
        Args:
            threshold: Voltage threshold for flame detection
        
        Returns:
            True if flame detected, False otherwise
        """
        voltage = self.read_voltage()
        return voltage > threshold
    
    def poll(self, interval_s: float = 0.3, count: Optional[int] = None):
        """
        Poll flame sensor and print readings.
        
        Args:
            interval_s: Time between polls in seconds
            count: Number of polls (None = infinite)
        """
        i = 0
        while count is None or i < count:
            reading = self.read()
            print(f"Digital Value: {reading['digital_value']:.3f}, "
                  f"Analog Voltage: {reading['voltage']:.3f}")
            time.sleep(interval_s)
            i += 1


if __name__ == "__main__":
    # Example usage
    sensor = FlameSensor(slot=2)
    try:
        sensor.poll(interval_s=0.3, count=10)
    except KeyboardInterrupt:
        print("\nStopped")
    finally:
        sensor.close()

