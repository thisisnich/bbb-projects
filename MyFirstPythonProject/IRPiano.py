"""
IR Piano - Plays musical notes based on distance, only when force is applied.

Uses IR Distance sensor (slot 1) to measure distance and determine note,
Buzzer (slot 3) to play the note, and Force Sensor (slot 4) as a trigger.
"""

import time
from irdistance_module import IRDistance
from buzzer_module import Buzzer
from force_module import ForceSensor


# Generate full chromatic scale frequencies
# Formula: frequency = 440 * 2^((n-9)/12) where n is the semitone number
# A4 (440 Hz) is semitone 9

def generate_chromatic_scale(start_octave=3, end_octave=7):
    """
    Generate chromatic scale frequencies from start_octave to end_octave.
    
    Returns:
        List of frequencies in Hz
    """
    frequencies = []
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    for octave in range(start_octave, end_octave + 1):
        for note_idx, note_name in enumerate(note_names):
            # Calculate semitone number (C4 = 0, C#4 = 1, ..., B4 = 11, C5 = 12, etc.)
            semitone = (octave - 4) * 12 + note_idx + (9 - 9)  # A4 is reference
            # Adjust for A4 = 440 Hz (semitone 9 in octave 4)
            semitone_from_a4 = (octave - 4) * 12 + note_idx - 9
            frequency = 440.0 * (2 ** (semitone_from_a4 / 12.0))
            frequencies.append((frequency, f"{note_name}{octave}"))
    
    return frequencies


# Generate full chromatic scale from C3 to C7 (4 octaves, 48 notes)
CHROMATIC_NOTES = generate_chromatic_scale(3, 7)

# Distance range: 5cm to 80cm (75cm range for 48 notes = ~1.56cm per note)
MIN_DISTANCE = 5.0
MAX_DISTANCE = 80.0
DISTANCE_RANGE = MAX_DISTANCE - MIN_DISTANCE
NOTES_COUNT = len(CHROMATIC_NOTES)
DISTANCE_PER_NOTE = DISTANCE_RANGE / NOTES_COUNT


def get_note_from_distance(distance_cm: float) -> float:
    """
    Get musical note frequency based on distance using full chromatic scale.
    
    Args:
        distance_cm: Distance in centimeters
    
    Returns:
        Frequency in Hz, or None if distance is out of range
    """
    if distance_cm is None:
        return None
    
    # Stop if distance is too far or too close
    if distance_cm > MAX_DISTANCE or distance_cm < MIN_DISTANCE:
        return None
    
    # Map distance to note index (closer = higher note)
    # Closer distance = higher index (higher frequency)
    note_index = int((MAX_DISTANCE - distance_cm) / DISTANCE_PER_NOTE)
    
    # Clamp to valid range
    note_index = max(0, min(NOTES_COUNT - 1, note_index))
    
    frequency, note_name = CHROMATIC_NOTES[note_index]
    return frequency


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
        print(f"Musical range: C3 to C7 (4 octaves, {NOTES_COUNT} notes)")
        print(f"Distance range: {MIN_DISTANCE}cm to {MAX_DISTANCE}cm (closer = higher notes)")
        print("Press Ctrl+C to stop.\n")
        
        while True:
            # Check if force is being applied (higher threshold to avoid early triggering)
            force_detected = force_sensor.is_force_detected(threshold=1.0)
            
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
