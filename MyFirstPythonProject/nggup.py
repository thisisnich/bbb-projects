"""
Never Gonna Give You Up - Rick Astley
Plays the iconic melody using the buzzer module.
"""

import time
from buzzer_module import Buzzer


# Musical note frequencies (Hz)
# Using A4 = 440 Hz as reference
NOTES = {
    'C4': 261.63,
    'C#4': 277.18,
    'D4': 293.66,
    'D#4': 311.13,
    'E4': 329.63,
    'F4': 349.23,
    'F#4': 369.99,
    'G4': 392.00,
    'G#4': 415.30,
    'A4': 440.00,
    'A#4': 466.16,
    'B4': 493.88,
    'C5': 523.25,
    'C#5': 554.37,
    'D5': 587.33,
    'D#5': 622.25,
    'E5': 659.25,
    'F5': 698.46,
    'F#5': 739.99,
    'G5': 783.99,
    'G#5': 830.61,
    'A5': 880.00,
    'A#5': 932.33,
    'B5': 987.77,
    'C6': 1046.50,
    'REST': 0,  # Rest/silence
}

# Tempo: beats per minute (BPM)
BPM = 120
# Quarter note duration in seconds
QUARTER_NOTE = 60.0 / BPM
# Other note durations
EIGHTH_NOTE = QUARTER_NOTE / 2
HALF_NOTE = QUARTER_NOTE * 2
WHOLE_NOTE = QUARTER_NOTE * 4
DOTTED_QUARTER = QUARTER_NOTE * 1.5
DOTTED_HALF = HALF_NOTE * 1.5

# "Never Gonna Give You Up" main melody
# Format: (note_name, duration_multiplier)
MELODY = [
    # Opening phrase: "We're no strangers to love"
    ('G4', 1), ('G4', 0.5), ('G4', 0.5), ('G4', 1),
    ('G#4', 1), ('G#4', 0.5), ('G#4', 0.5), ('G#4', 1),
    ('A4', 1), ('A4', 0.5), ('A4', 0.5), ('A4', 1),
    ('A#4', 1), ('A#4', 0.5), ('A#4', 0.5), ('A#4', 1),
    
    # "You know the rules and so do I"
    ('C5', 1), ('C5', 0.5), ('C5', 0.5), ('C5', 1),
    ('A#4', 1), ('A#4', 0.5), ('A#4', 0.5), ('A#4', 1),
    ('A4', 1), ('A4', 0.5), ('A4', 0.5), ('A4', 1),
    ('G#4', 1), ('G#4', 0.5), ('G#4', 0.5), ('G#4', 1),
    
    # "A full commitment's what I'm thinking of"
    ('G4', 1), ('G4', 0.5), ('G4', 0.5), ('G4', 1),
    ('G#4', 1), ('G#4', 0.5), ('G#4', 0.5), ('G#4', 1),
    ('A4', 1), ('A4', 0.5), ('A4', 0.5), ('A4', 1),
    ('A#4', 1), ('A#4', 0.5), ('A#4', 0.5), ('A#4', 1),
    
    # "You wouldn't get this from any other guy"
    ('C5', 1), ('C5', 0.5), ('C5', 0.5), ('C5', 1),
    ('A#4', 1), ('A#4', 0.5), ('A#4', 0.5), ('A#4', 1),
    ('A4', 1), ('A4', 0.5), ('A4', 0.5), ('A4', 1),
    ('G#4', 1), ('G#4', 0.5), ('G#4', 0.5), ('G#4', 1),
    
    # Chorus: "Never gonna give you up"
    ('G4', 0.5), ('G4', 0.5), ('G4', 0.5), ('G4', 0.5),
    ('G4', 0.5), ('G4', 0.5), ('G4', 1),
    ('G#4', 0.5), ('G#4', 0.5), ('G#4', 0.5), ('G#4', 0.5),
    ('G#4', 0.5), ('G#4', 0.5), ('G#4', 1),
    
    # "Never gonna let you down"
    ('A4', 0.5), ('A4', 0.5), ('A4', 0.5), ('A4', 0.5),
    ('A4', 0.5), ('A4', 0.5), ('A4', 1),
    ('A#4', 0.5), ('A#4', 0.5), ('A#4', 0.5), ('A#4', 0.5),
    ('A#4', 0.5), ('A#4', 0.5), ('A#4', 1),
    
    # "Never gonna run around and desert you"
    ('C5', 0.5), ('C5', 0.5), ('C5', 0.5), ('C5', 0.5),
    ('C5', 0.5), ('C5', 0.5), ('C5', 0.5), ('C5', 0.5),
    ('A#4', 0.5), ('A#4', 0.5), ('A#4', 0.5), ('A#4', 0.5),
    ('A4', 0.5), ('A4', 0.5), ('A4', 1),
    
    # "Never gonna make you cry"
    ('G#4', 0.5), ('G#4', 0.5), ('G#4', 0.5), ('G#4', 0.5),
    ('G#4', 0.5), ('G#4', 0.5), ('G#4', 1),
    ('G4', 0.5), ('G4', 0.5), ('G4', 0.5), ('G4', 0.5),
    ('G4', 0.5), ('G4', 0.5), ('G4', 1),
    
    # "Never gonna say goodbye"
    ('G4', 0.5), ('G4', 0.5), ('G4', 0.5), ('G4', 0.5),
    ('G4', 0.5), ('G4', 0.5), ('G4', 1),
    ('G#4', 0.5), ('G#4', 0.5), ('G#4', 0.5), ('G#4', 0.5),
    ('G#4', 0.5), ('G#4', 0.5), ('G#4', 1),
    
    # "Never gonna tell a lie and hurt you"
    ('A4', 0.5), ('A4', 0.5), ('A4', 0.5), ('A4', 0.5),
    ('A4', 0.5), ('A4', 0.5), ('A4', 0.5), ('A4', 0.5),
    ('A#4', 0.5), ('A#4', 0.5), ('A#4', 0.5), ('A#4', 0.5),
    ('C5', 0.5), ('C5', 0.5), ('C5', 1),
    
    # Final notes
    ('A#4', 1), ('A4', 1), ('G#4', 1), ('G4', 2),
]


def play_melody(buzzer: Buzzer, melody: list):
    """
    Play a melody using the buzzer.
    
    Args:
        buzzer: Buzzer instance
        melody: List of (note_name, duration_multiplier) tuples
    """
    buzzer.open()
    
    try:
        for note_name, duration_mult in melody:
            frequency = NOTES.get(note_name, 0)
            duration = QUARTER_NOTE * duration_mult
            
            if frequency > 0:
                buzzer.set_frequency(frequency)
                time.sleep(duration)
            else:
                # Rest - silence
                buzzer.stop()
                time.sleep(duration)
                buzzer.open()
    
    except KeyboardInterrupt:
        print("\nStopped")
    finally:
        buzzer.stop()


def main():
    """Main function to play Never Gonna Give You Up."""
    print("Never Gonna Give You Up - Rick Astley")
    print("Playing melody...")
    print("Press Ctrl+C to stop.\n")
    
    buzzer = Buzzer(slot=3)
    
    try:
        play_melody(buzzer, MELODY)
        print("\nFinished!")
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        buzzer.close()


if __name__ == "__main__":
    main()

