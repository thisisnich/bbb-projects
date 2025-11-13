"""
IR Piano - Plays musical notes based on distance, only when force is applied.

Uses IR Distance sensor (slot 1) to measure distance and determine note,
Buzzer (slot 3) to play the note, and Force Sensor (slot 4) as a trigger.
"""

import time
from irdistance_module import IRDistance
from buzzer_module import Buzzer
from force_module import ForceSensor


# Musical note frequencies (Hz) - C major scale
NOTES = {
    (10, 15): 523,   # C5
    (15, 20): 587,   # D5
    (20, 25): 659,   # E5
    (25, 30): 698,   # F5
    (30, 35): 783,   # G5
    (35, 40): 880,   # A5
    (40, 45): 988,   # B5
    (45, 100): 1046, # C6
}


def get_note_from_distance(distance_cm: float) -> float:
    """
    Get musical note frequency based on distance.
    
    Args:
        distance_cm: Distance in centimeters
    
    Returns:
        Frequency in Hz, or None if distance is out of range
    """
    if distance_cm is None or distance_cm > 100:
        return None
    
    for (min_dist, max_dist), frequency in NOTES.items():
        if min_dist < distance_cm <= max_dist:
            return frequency
    
    return None


def main():
    """Main IR Piano loop."""
    # Initialize sensors and buzzer
    ir_sensor = IRDistance(slot=1)
    buzzer = Buzzer(slot=3)
    force_sensor = ForceSensor(slot=4)
    
    try:
        # Start buzzer (but keep it stopped initially)
        buzzer.open()
        buzzer.stop()
        
        print("IR Piano started. Press force sensor to play notes based on distance.")
        print("Press Ctrl+C to stop.\n")
        
        while True:
            # Check if force is being applied
            force_detected = force_sensor.is_force_detected(threshold=0.5)
            
            # Read distance
            distance_cm = ir_sensor.read_distance_cm()
            
            if force_detected and distance_cm is not None:
                # Get note frequency based on distance
                frequency = get_note_from_distance(distance_cm)
                
                if frequency is not None:
                    # Play the note
                    buzzer.open()
                    buzzer.set_frequency(frequency)
                else:
                    # Distance out of range, stop buzzer
                    buzzer.stop()
            else:
                # No force detected, stop buzzer
                buzzer.stop()
            
            time.sleep(0.3)
    
    except KeyboardInterrupt:
        print("\nStopped")
    finally:
        # Clean up
        buzzer.close()
        ir_sensor.close()
        force_sensor.close()


if __name__ == "__main__":
    main()
