import time
from typing import Optional, Dict, Tuple, List


class AnalogueKeypad:
    """Driver for a 6-key analog keypad controlled via ADC.

    Detects which key is pressed by reading voltage thresholds on an analog input.
    """

    # Default voltage thresholds (from original code)
    DEFAULT_THRESHOLDS = {
        "T1": (0.90, 1.10),
        "T2": (0.84, 0.86),
        "T3": (0.67, 0.69),
        "T4": (0.50, 0.52),
        "T5": (0.33, 0.35),
        "T6": (0.16, 0.18),
        "NONE": (0.00, 0.10),
    }

    def __init__(
        self,
        pin: str = "P9_40",
        *,
        thresholds: Optional[Dict[str, Tuple[float, float]]] = None,
        debounce_ms: int = 50,
        lazy_hw: bool = False,
    ) -> None:
        """Initialize the analog keypad.

        Args:
            pin: ADC pin identifier (default: P9_40)
            thresholds: Custom voltage thresholds dict, e.g., {"T1": (0.90, 1.10), ...}
                        If None, uses defaults from original code
            debounce_ms: Debounce delay in milliseconds (0 = no debouncing)
            lazy_hw: If True, don't initialize hardware until open() is called
        """
        self._pin = pin
        self._debounce_ms = debounce_ms
        self._lazy_hw = lazy_hw

        if thresholds is None:
            self._thresholds = dict(self.DEFAULT_THRESHOLDS)
        else:
            self._thresholds = dict(thresholds)
            # Ensure NONE key is present
            if "NONE" not in self._thresholds:
                self._thresholds["NONE"] = (0.00, 0.10)

        self._ADC = None  # type: ignore[var-annotated]
        self._last_key = None
        self._last_change_time = 0.0

        if not self._lazy_hw:
            self.open()

    def open(self) -> None:
        """Open the ADC connection and initialize."""
        if self._ADC is not None:
            return

        import Adafruit_BBIO.ADC as ADC  # type: ignore

        self._ADC = ADC
        ADC.setup()

    def close(self) -> None:
        """Close the ADC connection."""
        self._ADC = None

    def __enter__(self) -> "AnalogueKeypad":
        """Context manager entry."""
        if self._ADC is None:
            self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Context manager exit."""
        self.close()

    def read_voltage(self) -> float:
        """Read raw ADC voltage reading.

        Returns:
            Voltage in volts (0.0 - 1.8V typically)
        """
        if self._ADC is None:
            self.open()
        digital_value = self._ADC.read(self._pin)  # type: ignore[attr-defined]
        return digital_value * 1.8  # Convert to voltage

    def read_raw(self) -> float:
        """Read raw ADC digital value.

        Returns:
            Raw ADC value (0.0 - 1.0)
        """
        if self._ADC is None:
            self.open()
        return self._ADC.read(self._pin)  # type: ignore[attr-defined]

    def read_key(self) -> Optional[str]:
        """Read which key is currently pressed.

        Returns:
            Key name if pressed (e.g., "T1", "T2", ..., "T6"), None if no key pressed
        """
        voltage = self.read_voltage()

        # Check thresholds (excluding NONE)
        for key_name, (min_v, max_v) in self._thresholds.items():
            if key_name == "NONE":
                continue
            if min_v <= voltage <= max_v:
                # Found a match
                current_key = key_name

                # Debouncing
                if self._debounce_ms > 0:
                    current_time = time.time() * 1000
                    if current_key != self._last_key:
                        if current_time - self._last_change_time < self._debounce_ms:
                            # Still in debounce period, return previous key
                            return self._last_key
                        # Key changed, update timestamps
                        self._last_change_time = current_time
                        self._last_key = current_key
                    else:
                        self._last_key = current_key
                else:
                    self._last_key = current_key

                return current_key

        # No key match (within NONE range or outside all ranges)
        current_key = None

        # Debouncing
        if self._debounce_ms > 0:
            current_time = time.time() * 1000
            if current_key != self._last_key:
                if current_time - self._last_change_time < self._debounce_ms:
                    return self._last_key
                self._last_change_time = current_time
                self._last_key = current_key
            else:
                self._last_key = current_key
        else:
            self._last_key = current_key

        return None

    def is_key_pressed(self, key: str) -> bool:
        """Check if a specific key is pressed.

        Args:
            key: Key name to check (e.g., "T1", "T2", etc.)

        Returns:
            True if specified key is pressed, False otherwise
        """
        return self.read_key() == key

    def get_all_keys(self) -> List[str]:
        """Get list of all available key names.

        Returns:
            List of key names (excluding "NONE")
        """
        return [k for k in self._thresholds.keys() if k != "NONE"]

    def wait_for_key(self, timeout_s: Optional[float] = None) -> Optional[str]:
        """Wait until any key is pressed.

        Args:
            timeout_s: Maximum time to wait in seconds (None = infinite)

        Returns:
            Key name if pressed, None if timeout
        """
        start_time = time.time()
        while True:
            key = self.read_key()
            if key is not None:
                return key
            if timeout_s is not None and (time.time() - start_time) >= timeout_s:
                return None
            time.sleep(0.01)  # Small delay to avoid busy-waiting

    def calibrate_key(self, key: str, samples: int = 10) -> Tuple[float, float]:
        """Read multiple samples to determine voltage range for a key.

        Args:
            key: Key name to calibrate
            samples: Number of samples to take

        Returns:
            Tuple of (min_voltage, max_voltage) for the key
        """
        print(f"Press and hold key '{key}'...")
        voltages = []
        for _ in range(samples):
            voltages.append(self.read_voltage())
            time.sleep(0.1)

        min_v = min(voltages)
        max_v = max(voltages)
        # Add small margin
        margin = (max_v - min_v) * 0.1
        return (min_v - margin, max_v + margin)


def _print_menu() -> None:
    """Print the test menu."""
    print("\nAnalogue Keypad test menu:")
    print("  1) read_key")
    print("  2) is_key_pressed <key>")
    print("  3) read_voltage")
    print("  4) read_raw")
    print("  5) get_all_keys")
    print("  6) wait_for_key [timeout_s]")
    print("  7) calibrate_key <key> [samples]")
    print("  8) poll_loop [interval_s] [count]")
    print("  q) quit")


if __name__ == "__main__":
    keypad = AnalogueKeypad()
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
                    key = keypad.read_key()
                    print(f"Key pressed: {key if key else 'NONE'}")
                elif cmd == "2":
                    if len(parts) < 2:
                        print("usage: 2 <key>")
                        print(f"Available keys: {', '.join(keypad.get_all_keys())}")
                        continue
                    key = parts[1]
                    pressed = keypad.is_key_pressed(key)
                    print(f"Key '{key}' is {'PRESSED' if pressed else 'NOT PRESSED'}")
                elif cmd == "3":
                    voltage = keypad.read_voltage()
                    print(f"Voltage: {voltage:.3f}V")
                elif cmd == "4":
                    raw = keypad.read_raw()
                    print(f"Raw ADC value: {raw:.3f}")
                elif cmd == "5":
                    keys = keypad.get_all_keys()
                    print(f"Available keys: {', '.join(keys)}")
                elif cmd == "6":
                    timeout = float(parts[1]) if len(parts) > 1 else None
                    print(f"Waiting for key press (timeout={timeout or 'infinite'}s)...")
                    key = keypad.wait_for_key(timeout)
                    print(f"Key pressed: {key if key else 'TIMEOUT'}")
                elif cmd == "7":
                    if len(parts) < 2:
                        print("usage: 7 <key> [samples]")
                        continue
                    key = parts[1]
                    samples = int(parts[2]) if len(parts) > 2 else 10
                    min_v, max_v = keypad.calibrate_key(key, samples)
                    print(f"Calibrated range for '{key}': ({min_v:.3f}, {max_v:.3f})")
                elif cmd == "8":
                    interval = float(parts[1]) if len(parts) > 1 else 0.3
                    count = int(parts[2]) if len(parts) > 2 else 10
                    print(f"Polling loop (interval={interval}s, count={count})...")
                    for i in range(count):
                        key = keypad.read_key()
                        voltage = keypad.read_voltage()
                        print(f"[{i+1}] Key: {key if key else 'NONE'}, Voltage: {voltage:.3f}V")
                        time.sleep(interval)
                else:
                    print("unknown command")
            except Exception as e:
                print(f"error: {e}")
    finally:
        keypad.close()
        print("\nKeypad closed")


# ============================================================================
# ORIGINAL CODE (commented for reference)
# ============================================================================
# #analogue key code
# import time
# import Adafruit_BBIO.ADC as ADC
#
# ADC.setup()
#
# while True:
#     DigitalValue = ADC.read("P9_40")
#     if DigitalValue >= 0.00 and DigitalValue < 0.10:
#         print("No Key is Pressed")
#     elif DigitalValue > 0.16 and DigitalValue < 0.18:
#         print("T6 Key is Pressed")
#     elif DigitalValue > 0.33 and DigitalValue < 0.35:
#         print("T5 Key is Pressed")
#     elif DigitalValue > 0.50 and DigitalValue < 0.52:
#         print("T4 Key is Pressed")
#     elif DigitalValue > 0.67 and DigitalValue < 0.69:
#         print("T3 Key is Pressed")
#     elif DigitalValue > 0.84 and DigitalValue < 0.86:
#         print("T2 Key is Pressed")
#     elif DigitalValue > 0.90 and DigitalValue < 1.10:
#         print("T1 Key is Pressed")
#     time.sleep(0.3)

