"""
VibroMotor module for Click Board.

Controls a vibration motor using PWM for frequency control.
"""

import time
from typing import Optional
from slot_config import get_slot_pin


class VibroMotor:
    """Vibration motor module with PWM frequency control."""
    
    def __init__(self, slot: int, *, lazy_hw: bool = False):
        """
        Initialize the vibration motor.
        
        Args:
            slot: Click board slot number (1-4)
            lazy_hw: If True, don't initialize hardware until open() is called
        """
        self._slot = slot
        self._pin = get_slot_pin(slot, "pwm")
        self._lazy_hw = lazy_hw
        self._PWM = None
        self._is_running = False
    
    def open(self):
        """Open the PWM connection and initialize."""
        if self._PWM is not None:
            return
        
        import Adafruit_BBIO.PWM as PWM
        self._PWM = PWM
        PWM.start(self._pin, 50)
        self._is_running = True
    
    def close(self):
        """Close the PWM connection and stop motor."""
        if self._PWM is not None and self._is_running:
            self._PWM.stop(self._pin)
            self._is_running = False
        self._PWM = None
    
    def __enter__(self):
        """Context manager entry."""
        if self._PWM is None:
            self.open()
        return self
    
    def __exit__(self, exc_type, exc, tb):
        """Context manager exit."""
        self.close()
    
    def set_frequency(self, frequency: float):
        """
        Set motor vibration frequency.
        
        Args:
            frequency: Frequency in Hz
        """
        if self._PWM is None:
            self.open()
        self._PWM.set_frequency(self._pin, frequency)
    
    def set_duty_cycle(self, duty_cycle: float):
        """
        Set PWM duty cycle.
        
        Args:
            duty_cycle: Duty cycle percentage (0-100)
        """
        if self._PWM is None:
            self.open()
        self._PWM.set_duty_cycle(self._pin, duty_cycle)
    
    def stop(self):
        """Stop the vibration motor."""
        self.close()
    
    def vibrate(self, frequency: float, duration_s: float):
        """
        Vibrate at a specified frequency for a duration.
        
        Args:
            frequency: Frequency in Hz
            duration_s: Duration in seconds
        """
        if self._PWM is None:
            self.open()
        self.set_frequency(frequency)
        time.sleep(duration_s)
    
    def pulse(self, high_freq: float = 5000, low_freq: float = 1, 
              high_duration: float = 1.0, low_duration: float = 0.1, 
              count: int = 3):
        """
        Create a pulsing vibration pattern.
        
        Args:
            high_freq: High frequency in Hz
            low_freq: Low frequency in Hz
            high_duration: Duration at high frequency in seconds
            low_duration: Duration at low frequency in seconds
            count: Number of pulses
        """
        if self._PWM is None:
            self.open()
        for _ in range(count):
            self.set_frequency(high_freq)
            time.sleep(high_duration)
            self.set_frequency(low_freq)
            time.sleep(low_duration)
        self.set_frequency(high_freq)
        time.sleep(high_duration)


if __name__ == "__main__":
    # Example usage
    motor = VibroMotor(slot=1)
    try:
        motor.pulse(count=3)
    except KeyboardInterrupt:
        print("\nStopped")
    finally:
        motor.close()

