"""
IR Distance sensor module for Click Board.

Measures distance using an IR distance sensor via ADC.
"""

import time
from typing import Optional
from slot_config import get_slot_pin


class IRDistance:
    """IR distance measurement sensor module."""
    
    def __init__(self, slot: int, *, lazy_hw: bool = False):
        """
        Initialize the IR distance sensor.
        
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
        if digital_value == 0:
            return 0.0
        # Voltage calculation: (DigitalValue * 1.8) * (2200 / 1200)
        analog_voltage = (digital_value * 1.8) * (2200 / 1200)
        return analog_voltage
    
    def read_distance_cm(self) -> Optional[float]:
        """
        Read distance in centimeters.
        
        Returns:
            Distance in cm, or None if reading is invalid
        """
        digital_value = self.read_digital()
        if digital_value == 0:
            return None
        analog_voltage = self.read_voltage()
        # Distance formula: 29.988 * pow(AnalogVoltage, -1.173)
        distance_cm = 29.988 * pow(analog_voltage, -1.173)
        return distance_cm
    
    def read(self) -> dict:
        """
        Read all sensor values.
        
        Returns:
            Dictionary with digital_value, voltage, and distance_cm
        """
        digital_value = self.read_digital()
        if digital_value == 0:
            return {
                "digital_value": 0.0,
                "voltage": 0.0,
                "distance_cm": None
            }
        
        voltage = self.read_voltage()
        distance_cm = self.read_distance_cm()
        
        return {
            "digital_value": digital_value,
            "voltage": voltage,
            "distance_cm": distance_cm
        }
    
    def poll(self, interval_s: float = 0.3, count: Optional[int] = None):
        """
        Poll IR distance sensor and print readings.
        
        Args:
            interval_s: Time between polls in seconds
            count: Number of polls (None = infinite)
        """
        i = 0
        while count is None or i < count:
            reading = self.read()
            if reading["distance_cm"] is not None:
                print(f"Distance(cm): {reading['distance_cm']:.2f}")
            else:
                print("No valid reading")
            time.sleep(interval_s)
            i += 1


if __name__ == "__main__":
    # Example usage
    sensor = IRDistance(slot=1)
    try:
        sensor.poll(interval_s=0.3, count=10)
    except KeyboardInterrupt:
        print("\nStopped")
    finally:
        sensor.close()

