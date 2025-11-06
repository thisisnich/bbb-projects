import time
from typing import Optional, List, Tuple


class LedMatrix8x8:
    """Driver for an 8x8 LED matrix controlled via SPI.
    
    The matrix uses MAX7219-style commands where each row (1-8) is addressed
    with a register number (0x01-0x08) and an 8-bit pattern.
    """
    
    # Preset patterns - 8 rows of 8 bits each
    PRESETS = {
        "smiley": [0b00111100,
                   0b01000010,
                   0b10101001,
                   0b10000101,
                   0b10000101,
                   0b10101001,
                   0b01000010,
                   0b00111100],
        
        "sad": [0b00111100,
                0b01000010,
                0b10101001,
                0b10000101,
                0b10000101,
                0b10011001,
                0b01000010,
                0b00111100],
        
        "heart": [0b00000000,
                  0b01100110,
                  0b11111111,
                  0b11111111,
                  0b01111110,
                  0b00111100,
                  0b00011000,
                  0b00000000],
        
        "arrow_up": [0b00011000,
                     0b00111100,
                     0b01111110,
                     0b11111111,
                     0b00011000,
                     0b00011000,
                     0b00011000,
                     0b00011000],
        
        "arrow_down": [0b00011000,
                       0b00011000,
                       0b00011000,
                       0b00011000,
                       0b11111111,
                       0b01111110,
                       0b00111100,
                       0b00011000],
        
        "arrow_left": [0b00011000,
                       0b00110000,
                       0b01100000,
                       0b11111111,
                       0b11111111,
                       0b01100000,
                       0b00110000,
                       0b00011000],
        
        "arrow_right": [0b00011000,
                        0b00001100,
                        0b00000110,
                        0b11111111,
                        0b11111111,
                        0b00000110,
                        0b00001100,
                        0b00011000],
        
        "check": [0b00000000,
                  0b00000001,
                  0b00000011,
                  0b00000110,
                  0b11001100,
                  0b01111000,
                  0b00110000,
                  0b00000000],
        
        "x": [0b11000011,
              0b01100110,
              0b00111100,
              0b00011000,
              0b00011000,
              0b00111100,
              0b01100110,
              0b11000011],
        
        "filled": [0b11111111,
                   0b11111111,
                   0b11111111,
                   0b11111111,
                   0b11111111,
                   0b11111111,
                   0b11111111,
                   0b11111111],
        
        "empty": [0b00000000,
                  0b00000000,
                  0b00000000,
                  0b00000000,
                  0b00000000,
                  0b00000000,
                  0b00000000,
                  0b00000000],
        
        "cross": [0b10000001,
                  0b01000010,
                  0b00100100,
                  0b00011000,
                  0b00011000,
                  0b00100100,
                  0b01000010,
                  0b10000001],
        
        "square": [0b11111111,
                   0b10000001,
                   0b10000001,
                   0b10000001,
                   0b10000001,
                   0b10000001,
                   0b10000001,
                   0b11111111],
        
        "circle": [0b00111100,
                   0b01000010,
                   0b10000001,
                   0b10000001,
                   0b10000001,
                   0b10000001,
                   0b01000010,
                   0b00111100],
        
        "diamond": [0b00011000,
                    0b00111100,
                    0b01111110,
                    0b11111111,
                    0b11111111,
                    0b01111110,
                    0b00111100,
                    0b00011000],
    }
    
    def __init__(
        self,
        bus: int = 1,
        device: int = 0,
        *,
        mode: int = 0,
        lazy_hw: bool = False,
    ) -> None:
        """Initialize the LED matrix.
        
        Args:
            bus: SPI bus number (default: 1)
            device: SPI device number (default: 0)
            mode: SPI mode (default: 0)
            lazy_hw: If True, don't initialize hardware until open() is called
        """
        self._bus = bus
        self._device = device
        self._mode = mode
        self._lazy_hw = lazy_hw
        
        self._spi = None  # type: ignore[var-annotated]
        self._current_pattern = [0] * 8
        
        if not self._lazy_hw:
            self.open()
    
    def open(self) -> None:
        """Open the SPI connection and initialize the matrix."""
        if self._spi is not None:
            return
        
        from Adafruit_BBIO.SPI import SPI  # type: ignore
        
        self._spi = SPI(self._bus, self._device)
        self._spi.mode = self._mode
        
        # Initialize MAX7219 registers
        # 0x09: Decode mode (0x00 = no decode)
        self._spi.writebytes([0x09, 0x00])
        # 0x0A: Intensity (0x01 = low brightness)
        self._spi.writebytes([0x0A, 0x01])
        # 0x0B: Scan limit (0x07 = all 8 rows)
        self._spi.writebytes([0x0B, 0x07])
        # 0x0C: Shutdown register (0x01 = normal operation)
        self._spi.writebytes([0x0C, 0x01])
    
    def close(self) -> None:
        """Close the SPI connection."""
        if self._spi is not None:
            try:
                self._spi.close()
            finally:
                self._spi = None
    
    def __enter__(self) -> "LedMatrix8x8":
        """Context manager entry."""
        if self._spi is None:
            self.open()
        return self
    
    def __exit__(self, exc_type, exc, tb) -> None:
        """Context manager exit."""
        self.close()
    
    # ----------------------------- High-level APIs ----------------------------
    
    def clear(self) -> None:
        """Clear the display (all LEDs off)."""
        self.set_pattern([0] * 8)
    
    def fill(self) -> None:
        """Fill the display (all LEDs on)."""
        self.set_pattern([0xFF] * 8)
    
    def set_pattern(self, pattern: List[int]) -> None:
        """Set the display to a custom pattern.
        
        Args:
            pattern: List of 8 bytes (one per row), where each byte represents
                    8 columns (LSB = rightmost column)
        """
        if len(pattern) != 8:
            raise ValueError("pattern must have exactly 8 rows")
        
        if self._spi is None:
            self.open()
        
        self._current_pattern = list(pattern)
        for row in range(8):
            # Register addresses are 0x01-0x08 for rows 0-7
            self._spi.writebytes([0x01 + row, pattern[row]])  # type: ignore[attr-defined]
    
    def set_preset(self, name: str) -> None:
        """Display a preset pattern.
        
        Args:
            name: Name of the preset (e.g., "smiley", "heart", "arrow_up")
        """
        if name not in self.PRESETS:
            available = ", ".join(sorted(self.PRESETS.keys()))
            raise ValueError(f"Unknown preset '{name}'. Available: {available}")
        self.set_pattern(self.PRESETS[name])
    
    def set_pixel(self, row: int, col: int, on: bool = True) -> None:
        """Set a single pixel on or off.
        
        Args:
            row: Row number (0-7, top to bottom)
            col: Column number (0-7, left to right)
            on: True to turn on, False to turn off
        """
        if not (0 <= row < 8 and 0 <= col < 8):
            raise ValueError("row and col must be between 0 and 7")
        
        pattern = list(self._current_pattern)
        if on:
            pattern[row] |= (1 << (7 - col))  # Bit 7 is leftmost
        else:
            pattern[row] &= ~(1 << (7 - col))
        
        self.set_pattern(pattern)
    
    def get_pattern(self) -> List[int]:
        """Get the current display pattern."""
        return list(self._current_pattern)
    
    # ----------------------------- Animations --------------------------------
    
    def animate_spin(self, delay_s: float = 0.1, cycles: Optional[int] = None) -> None:
        """Animate a spinning pattern.
        
        Args:
            delay_s: Delay between frames in seconds
            cycles: Number of cycles (None = infinite)
        """
        pattern = [0b00000001,
                   0b00000010,
                   0b00000100,
                   0b00001000,
                   0b00010000,
                   0b00100000,
                   0b01000000,
                   0b10000000]
        
        loops = 0
        while cycles is None or loops < cycles:
            for _ in range(8):
                self.set_pattern(pattern)
                time.sleep(delay_s)
                # Rotate pattern
                pattern = [(b >> 1) | ((b & 1) << 7) for b in pattern]
            loops += 1
    
    def animate_sweep_horizontal(self, delay_s: float = 0.1, cycles: Optional[int] = None) -> None:
        """Animate a horizontal sweep (left to right).
        
        Args:
            delay_s: Delay between frames in seconds
            cycles: Number of cycles (None = infinite)
        """
        loops = 0
        while cycles is None or loops < cycles:
            for col in range(8):
                pattern = [0] * 8
                for row in range(8):
                    pattern[row] = 1 << (7 - col)
                self.set_pattern(pattern)
                time.sleep(delay_s)
            loops += 1
    
    def animate_sweep_vertical(self, delay_s: float = 0.1, cycles: Optional[int] = None) -> None:
        """Animate a vertical sweep (top to bottom).
        
        Args:
            delay_s: Delay between frames in seconds
            cycles: Number of cycles (None = infinite)
        """
        loops = 0
        while cycles is None or loops < cycles:
            for row in range(8):
                pattern = [0] * 8
                pattern[row] = 0xFF
                self.set_pattern(pattern)
                time.sleep(delay_s)
            loops += 1
    
    def animate_grow(self, delay_s: float = 0.1, cycles: Optional[int] = None) -> None:
        """Animate a growing/shrinking square.
        
        Args:
            delay_s: Delay between frames in seconds
            cycles: Number of cycles (None = infinite)
        """
        def make_square(size: int) -> List[int]:
            """Create a square pattern of given size (1-8)."""
            if size == 0:
                return [0] * 8
            pattern = [0] * 8
            start = (8 - size) // 2
            for i in range(start, start + size):
                pattern[i] = (0xFF >> (8 - size)) << ((8 - size) // 2)
            return pattern
        
        loops = 0
        while cycles is None or loops < cycles:
            # Grow
            for size in range(0, 9):
                self.set_pattern(make_square(size))
                time.sleep(delay_s)
            # Shrink
            for size in range(7, -1, -1):
                self.set_pattern(make_square(size))
                time.sleep(delay_s)
            loops += 1
    
    def animate_blink(self, pattern_name: str, delay_s: float = 0.3, cycles: Optional[int] = None) -> None:
        """Blink a preset pattern on and off.
        
        Args:
            pattern_name: Name of preset to blink
            delay_s: Delay between on/off states in seconds
            cycles: Number of cycles (None = infinite)
        """
        if pattern_name not in self.PRESETS:
            available = ", ".join(sorted(self.PRESETS.keys()))
            raise ValueError(f"Unknown preset '{pattern_name}'. Available: {available}")
        
        pattern = self.PRESETS[pattern_name]
        loops = 0
        while cycles is None or loops < cycles:
            self.set_pattern(pattern)
            time.sleep(delay_s)
            self.clear()
            time.sleep(delay_s)
            loops += 1
    
    def animate_scroll(self, pattern: List[int], direction: str = "left", delay_s: float = 0.1, cycles: Optional[int] = None) -> None:
        """Scroll a pattern horizontally.
        
        Args:
            pattern: Pattern to scroll (8 rows)
            direction: "left" or "right"
            delay_s: Delay between frames in seconds
            cycles: Number of cycles (None = infinite)
        """
        if len(pattern) != 8:
            raise ValueError("pattern must have exactly 8 rows")
        
        loops = 0
        while cycles is None or loops < cycles:
            for shift in range(8):
                if direction == "left":
                    shifted = [(b << shift) | (b >> (8 - shift)) for b in pattern]
                else:  # right
                    shifted = [(b >> shift) | (b << (8 - shift)) for b in pattern]
                self.set_pattern(shifted)
                time.sleep(delay_s)
            loops += 1
    
    def animate_cycle_presets(self, delay_s: float = 0.5, cycles: Optional[int] = None) -> None:
        """Cycle through all preset patterns.
        
        Args:
            delay_s: Delay between patterns in seconds
            cycles: Number of cycles (None = infinite)
        """
        preset_names = sorted(self.PRESETS.keys())
        loops = 0
        while cycles is None or loops < cycles:
            for name in preset_names:
                self.set_preset(name)
                time.sleep(delay_s)
            loops += 1
    
    def animate_random_walk(self, delay_s: float = 0.2, steps: int = 50) -> None:
        """Animate a random walk pattern.
        
        Args:
            delay_s: Delay between steps in seconds
            steps: Number of steps to take
        """
        import random
        
        # Start at center
        row, col = 4, 4
        pattern = [0] * 8
        
        for _ in range(steps):
            # Set current position
            pattern[row] |= (1 << (7 - col))
            self.set_pattern(pattern)
            time.sleep(delay_s)
            
            # Move randomly (with boundary checks)
            direction = random.randint(0, 3)
            if direction == 0 and row > 0:  # up
                row -= 1
            elif direction == 1 and row < 7:  # down
                row += 1
            elif direction == 2 and col > 0:  # left
                col -= 1
            elif direction == 3 and col < 7:  # right
                col += 1


def _print_menu() -> None:
    """Print the test menu."""
    print("\nLED Matrix 8x8 test menu:")
    print("  1) clear")
    print("  2) fill")
    print("  3) set_preset <name>")
    print("  4) set_pixel <row> <col> [on|off]")
    print("  5) set_pattern <8 bytes in hex: e.g., 3C 42 A9 85 85 A9 42 3C>")
    print("  6) list_presets")
    print("  7) animate_spin [delay_s] [cycles]")
    print("  8) animate_sweep_horizontal [delay_s] [cycles]")
    print("  9) animate_sweep_vertical [delay_s] [cycles]")
    print(" 10) animate_grow [delay_s] [cycles]")
    print(" 11) animate_blink <preset_name> [delay_s] [cycles]")
    print(" 12) animate_scroll <preset_name> [left|right] [delay_s] [cycles]")
    print(" 13) animate_cycle_presets [delay_s] [cycles]")
    print(" 14) animate_random_walk [delay_s] [steps]")
    print("  q) quit")


def _parse_int(s: str) -> int:
    """Parse an integer (decimal or hex)."""
    s = s.strip()
    return int(s, 16) if s.lower().startswith("0x") else int(s)


if __name__ == "__main__":
    matrix = LedMatrix8x8()
    try:
        while True:
            _print_menu()
            line = input("\n> ").strip()
            if not line:
                continue
            if line.lower() in {"q", "quit", "exit"}:
                break
            
            parts = [p.strip() for p in line.split()]
            cmd = parts[0]
            
            try:
                if cmd == "1":
                    matrix.clear()
                    print("Display cleared")
                    
                elif cmd == "2":
                    matrix.fill()
                    print("Display filled")
                    
                elif cmd == "3":
                    if len(parts) < 2:
                        print("usage: 3 <preset_name>")
                        print(f"Available presets: {', '.join(sorted(LedMatrix8x8.PRESETS.keys()))}")
                        continue
                    matrix.set_preset(parts[1])
                    print(f"Displaying preset: {parts[1]}")
                    
                elif cmd == "4":
                    if len(parts) < 3:
                        print("usage: 4 <row> <col> [on|off]")
                        continue
                    row = int(parts[1])
                    col = int(parts[2])
                    on = parts[3].lower() != "off" if len(parts) > 3 else True
                    matrix.set_pixel(row, col, on)
                    print(f"Pixel ({row}, {col}) set to {'on' if on else 'off'}")
                    
                elif cmd == "5":
                    if len(parts) < 9:
                        print("usage: 5 <byte1> <byte2> ... <byte8>")
                        print("Example: 5 3C 42 A9 85 85 A9 42 3C")
                        continue
                    pattern = [_parse_int(p) for p in parts[1:9]]
                    matrix.set_pattern(pattern)
                    print("Pattern set")
                    
                elif cmd == "6":
                    print("Available presets:")
                    for name in sorted(LedMatrix8x8.PRESETS.keys()):
                        print(f"  - {name}")
                    
                elif cmd == "7":
                    delay = float(parts[1]) if len(parts) > 1 else 0.1
                    cycles = int(parts[2]) if len(parts) > 2 else None
                    print(f"Spinning (delay={delay}s, cycles={cycles or 'infinite'})...")
                    matrix.animate_spin(delay, cycles)
                    
                elif cmd == "8":
                    delay = float(parts[1]) if len(parts) > 1 else 0.1
                    cycles = int(parts[2]) if len(parts) > 2 else None
                    print(f"Horizontal sweep (delay={delay}s, cycles={cycles or 'infinite'})...")
                    matrix.animate_sweep_horizontal(delay, cycles)
                    
                elif cmd == "9":
                    delay = float(parts[1]) if len(parts) > 1 else 0.1
                    cycles = int(parts[2]) if len(parts) > 2 else None
                    print(f"Vertical sweep (delay={delay}s, cycles={cycles or 'infinite'})...")
                    matrix.animate_sweep_vertical(delay, cycles)
                    
                elif cmd == "10":
                    delay = float(parts[1]) if len(parts) > 1 else 0.1
                    cycles = int(parts[2]) if len(parts) > 2 else None
                    print(f"Growing square (delay={delay}s, cycles={cycles or 'infinite'})...")
                    matrix.animate_grow(delay, cycles)
                    
                elif cmd == "11":
                    if len(parts) < 2:
                        print("usage: 11 <preset_name> [delay_s] [cycles]")
                        continue
                    delay = float(parts[2]) if len(parts) > 2 else 0.3
                    cycles = int(parts[3]) if len(parts) > 3 else None
                    print(f"Blinking {parts[1]} (delay={delay}s, cycles={cycles or 'infinite'})...")
                    matrix.animate_blink(parts[1], delay, cycles)
                    
                elif cmd == "12":
                    if len(parts) < 2:
                        print("usage: 12 <preset_name> [left|right] [delay_s] [cycles]")
                        continue
                    preset_name = parts[1]
                    if preset_name not in LedMatrix8x8.PRESETS:
                        print(f"Unknown preset: {preset_name}")
                        continue
                    
                    # Parse optional arguments
                    direction = "left"
                    delay = 0.1
                    cycles = None
                    
                    if len(parts) > 2:
                        if parts[2] in ("left", "right"):
                            direction = parts[2]
                            if len(parts) > 3:
                                delay = float(parts[3])
                                if len(parts) > 4:
                                    cycles = int(parts[4])
                        else:
                            delay = float(parts[2])
                            if len(parts) > 3:
                                cycles = int(parts[3])
                    
                    print(f"Scrolling {preset_name} {direction} (delay={delay}s, cycles={cycles or 'infinite'})...")
                    matrix.animate_scroll(LedMatrix8x8.PRESETS[preset_name], direction, delay, cycles)
                    
                elif cmd == "13":
                    delay = float(parts[1]) if len(parts) > 1 else 0.5
                    cycles = int(parts[2]) if len(parts) > 2 else None
                    print(f"Cycling presets (delay={delay}s, cycles={cycles or 'infinite'})...")
                    matrix.animate_cycle_presets(delay, cycles)
                    
                elif cmd == "14":
                    delay = float(parts[1]) if len(parts) > 1 else 0.2
                    steps = int(parts[2]) if len(parts) > 2 else 50
                    print(f"Random walk (delay={delay}s, steps={steps})...")
                    matrix.animate_random_walk(delay, steps)
                    
                else:
                    print("unknown command")
                    
            except Exception as e:
                print(f"error: {e}")
                
    finally:
        matrix.close()
        print("\nDisplay closed")


# ============================================================================
# ORIGINAL CODE (commented for reference)
# ============================================================================
# from Adafruit_BBIO.SPI import SPI
#
# G_SmileyHappyFace = [0b00111100,
#                      0b01000010,
#                      0b10101001,
#                      0b10000101,
#                      0b10000101,
#                      0b10101001,
#                      0b01000010,
#                      0b00111100]
#
# def LedMatrix8x8ClickInit():
#     L_Spi1 = SPI(1,0)
#     L_Spi1.mode = 0
#     L_Spi1.writebytes([0x09, 0x00])
#     L_Spi1.writebytes([0x0A, 0x01])
#     L_Spi1.writebytes([0x0B, 0x07])
#     L_Spi1.writebytes([0x0C, 0x01])
#     return L_Spi1
#
# def PrintDisplay(L_Spi1, DisplayList):
#     L_Spi1.writebytes([0x01, DisplayList[0]])
#     L_Spi1.writebytes([0x02, DisplayList[1]])
#     L_Spi1.writebytes([0x03, DisplayList[2]])
#     L_Spi1.writebytes([0x04, DisplayList[3]])
#     L_Spi1.writebytes([0x05, DisplayList[4]])
#     L_Spi1.writebytes([0x06, DisplayList[5]])
#     L_Spi1.writebytes([0x07, DisplayList[6]])
#     L_Spi1.writebytes([0x08, DisplayList[7]])
#     
#
# G_Spi1 = LedMatrix8x8ClickInit()
# PrintDisplay(G_Spi1, G_SmileyHappyFace)
