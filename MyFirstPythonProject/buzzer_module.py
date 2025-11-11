"""
Buzzer module for Click Board.

Controls a buzzer using PWM for frequency control.
"""

import time
from typing import Optional
from slot_config import get_slot_pin


class Buzzer:
    """Buzzer module with PWM frequency control."""
    
    def __init__(self, slot: int, *, lazy_hw: bool = False):
        """
        Initialize the buzzer.
        
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
        """Close the PWM connection and stop buzzer."""
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
        Set buzzer frequency.
        
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
        """Stop the buzzer."""
        self.close()
    
    def play_tone(self, frequency: float, duration_s: float):
        """
        Play a tone for a specified duration.
        
        Args:
            frequency: Frequency in Hz
            duration_s: Duration in seconds
        """
        if self._PWM is None:
            self.open()
        self.set_frequency(frequency)
        time.sleep(duration_s)
    
    def play_sequence(self, tones: list, duration_s: float = 0.5):
        """
        Play a sequence of tones.
        
        Args:
            tones: List of frequencies in Hz
            duration_s: Duration for each tone in seconds
        """
        if self._PWM is None:
            self.open()
        for frequency in tones:
            self.play_tone(frequency, duration_s)
        self.stop()


if __name__ == "__main__":
    # Example usage - play a simple melody
    buzzer = Buzzer(slot=3)
    try:
        # Play C, D, E notes
        buzzer.play_sequence([523, 587, 659], duration_s=0.5)
    except KeyboardInterrupt:
        print("\nStopped")
    finally:
        buzzer.close()

