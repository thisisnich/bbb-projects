import time
from typing import Optional, Dict, Tuple, Callable


class KeyLock:
    """Driver for a 3-position key lock switch controlled via GPIO.

    Detects lock position by reading 3 GPIO inputs that encode the position (one-hot encoding).
    """

    # Position encoding (from original code observations)
    POSITION_ENCODING = {
        1: (0, 0, 1),  # P8_16=0, P8_13=0, P8_17=1
        2: (0, 1, 0),  # P8_16=0, P8_13=1, P8_17=0
        3: (1, 0, 0),  # P8_16=1, P8_13=0, P8_17=0
    }

    def __init__(
        self,
        pin_a: str = "P8_16",
        pin_b: str = "P8_13",
        pin_c: str = "P8_17",
        *,
        position_names: Optional[Dict[int, str]] = None,
        pull: str = "UP",
        lazy_hw: bool = False,
    ) -> None:
        """Initialize the key lock.

        Args:
            pin_a: GPIO pin for position 1 indicator (default: P8_16)
            pin_b: GPIO pin for position 2 indicator (default: P8_13)
            pin_c: GPIO pin for position 3 indicator (default: P8_17)
            position_names: Custom position names dict, e.g., {1: "OFF", 2: "ON", 3: "ALARM"}
                           Default: {1: "Position1", 2: "Position2", 3: "Position3"}
            pull: Pull resistor configuration ("UP", "DOWN", or None) for all pins
            lazy_hw: If True, don't initialize hardware until open() is called
        """
        self._pin_a = pin_a
        self._pin_b = pin_b
        self._pin_c = pin_c
        self._pull = pull
        self._lazy_hw = lazy_hw

        if position_names is None:
            self._position_names = {
                1: "Position1",
                2: "Position2",
                3: "Position3",
            }
        else:
            self._position_names = dict(position_names)

        self._GPIO = None  # type: ignore[var-annotated]
        self._on_position_change_callbacks = []

        if not self._lazy_hw:
            self.open()

    def open(self) -> None:
        """Open the GPIO connection and initialize."""
        if self._GPIO is not None:
            return

        import Adafruit_BBIO.GPIO as GPIO  # type: ignore

        self._GPIO = GPIO

        # Map pull string to GPIO constant
        pull_map = {
            "UP": GPIO.PUD_UP,
            "DOWN": GPIO.PUD_DOWN,
        }
        pull_value = pull_map.get(self._pull.upper(), GPIO.PUD_OFF)

        GPIO.setup(self._pin_a, GPIO.IN, pull_up_down=pull_value)
        GPIO.setup(self._pin_b, GPIO.IN, pull_up_down=pull_value)
        GPIO.setup(self._pin_c, GPIO.IN, pull_up_down=pull_value)

    def close(self) -> None:
        """Close the GPIO connection."""
        self._GPIO = None
        self._on_position_change_callbacks.clear()

    def __enter__(self) -> "KeyLock":
        """Context manager entry."""
        if self._GPIO is None:
            self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Context manager exit."""
        self.close()

    def read_raw(self) -> Tuple[int, int, int]:
        """Read raw GPIO values.

        Returns:
            Tuple of (pin_a, pin_b, pin_c) values (0 or 1)
        """
        if self._GPIO is None:
            self.open()
        return (
            self._GPIO.input(self._pin_a),  # type: ignore[attr-defined]
            self._GPIO.input(self._pin_b),  # type: ignore[attr-defined]
            self._GPIO.input(self._pin_c),  # type: ignore[attr-defined]
        )

    def is_valid_state(self) -> bool:
        """Check if the current state is valid (exactly one pin is HIGH).

        Returns:
            True if state is valid (one-hot encoding), False otherwise
        """
        raw = self.read_raw()
        high_count = sum(raw)
        return high_count == 1

    def get_invalid_reason(self) -> Optional[str]:
        """Get error message if state is invalid.

        Returns:
            Error message if invalid, None if valid
        """
        raw = self.read_raw()
        high_count = sum(raw)

        if high_count == 0:
            return "All pins are LOW (no position detected)"
        elif high_count > 1:
            return f"Multiple pins are HIGH ({high_count} pins), expected exactly one"
        return None

    def read_position(self) -> int:
        """Read current lock position.

        Returns:
            Position number (1, 2, or 3)
        """
        raw = self.read_raw()

        # Check against known encodings
        for pos, encoding in self.POSITION_ENCODING.items():
            if raw == encoding:
                return pos

        # If no match, try to determine from one-hot
        if raw[2] == 1:  # pin_c
            return 1
        elif raw[1] == 1:  # pin_b
            return 2
        elif raw[0] == 1:  # pin_a
            return 3

        # Default to position 1 if unclear
        return 1

    def read_position_name(self) -> str:
        """Read current lock position name.

        Returns:
            Position name string
        """
        pos = self.read_position()
        return self._position_names.get(pos, f"Position{pos}")

    def is_position(self, position: int | str) -> bool:
        """Check if lock is in specified position.

        Args:
            position: Position number (1, 2, 3) or position name string

        Returns:
            True if lock is in specified position, False otherwise
        """
        current_pos = self.read_position()

        if isinstance(position, int):
            return current_pos == position
        else:
            # Find position number for this name
            for pos_num, pos_name in self._position_names.items():
                if pos_name == position:
                    return current_pos == pos_num
            return False

    def wait_for_position(self, position: int | str, timeout_s: Optional[float] = None) -> bool:
        """Wait until lock reaches specified position.

        Args:
            position: Position number (1, 2, 3) or position name string
            timeout_s: Maximum time to wait in seconds (None = infinite)

        Returns:
            True if position reached, False if timeout
        """
        start_time = time.time()
        while True:
            if self.is_position(position):
                return True
            if timeout_s is not None and (time.time() - start_time) >= timeout_s:
                return False
            time.sleep(0.01)  # Small delay to avoid busy-waiting

    def on_position_change(self, callback: Callable[[int, str], None]) -> None:
        """Register callback for position change events.

        Args:
            callback: Function to call when position changes (receives position number and name)
        """
        self._on_position_change_callbacks.append(callback)

    def clear_callbacks(self) -> None:
        """Remove all registered callbacks."""
        self._on_position_change_callbacks.clear()


def _print_menu() -> None:
    """Print the test menu."""
    print("\nKey Lock test menu:")
    print("  1) read_position")
    print("  2) read_position_name")
    print("  3) is_position <position>")
    print("  4) read_raw")
    print("  5) is_valid_state")
    print("  6) get_invalid_reason")
    print("  7) wait_for_position <position> [timeout_s]")
    print("  8) poll_loop [interval_s] [count]")
    print("  q) quit")


if __name__ == "__main__":
    lock = KeyLock()
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
                    pos = lock.read_position()
                    print(f"Position: {pos}")
                elif cmd == "2":
                    name = lock.read_position_name()
                    print(f"Position name: {name}")
                elif cmd == "3":
                    if len(parts) < 2:
                        print("usage: 3 <position> (e.g., 1, 2, 3, or position name)")
                        continue
                    position = parts[1]
                    # Try to convert to int, otherwise use as string
                    try:
                        position = int(position)
                    except ValueError:
                        pass
                    is_pos = lock.is_position(position)
                    print(f"Lock is {'in' if is_pos else 'not in'} position '{position}'")
                elif cmd == "4":
                    raw = lock.read_raw()
                    print(f"Raw values (pin_a, pin_b, pin_c): {raw}")
                elif cmd == "5":
                    valid = lock.is_valid_state()
                    print(f"State is {'VALID' if valid else 'INVALID'}")
                elif cmd == "6":
                    reason = lock.get_invalid_reason()
                    print(f"Invalid reason: {reason if reason else 'State is valid'}")
                elif cmd == "7":
                    if len(parts) < 2:
                        print("usage: 7 <position> [timeout_s]")
                        continue
                    position = parts[1]
                    try:
                        position = int(position)
                    except ValueError:
                        pass
                    timeout = float(parts[2]) if len(parts) > 2 else None
                    print(f"Waiting for position '{position}' (timeout={timeout or 'infinite'}s)...")
                    result = lock.wait_for_position(position, timeout)
                    print(f"Position {'REACHED' if result else 'TIMEOUT'}")
                elif cmd == "8":
                    interval = float(parts[1]) if len(parts) > 1 else 0.3
                    count = int(parts[2]) if len(parts) > 2 else 10
                    print(f"Polling loop (interval={interval}s, count={count})...")
                    for i in range(count):
                        pos = lock.read_position()
                        name = lock.read_position_name()
                        raw = lock.read_raw()
                        valid = lock.is_valid_state()
                        print(f"[{i+1}] Position: {pos} ({name}), Raw: {raw}, Valid: {valid}")
                        time.sleep(interval)
                else:
                    print("unknown command")
            except Exception as e:
                print(f"error: {e}")
    finally:
        lock.close()
        print("\nKey lock closed")


# ============================================================================
# ORIGINAL CODE (commented for reference)
# ============================================================================
# #keylock2 code
# import time
# import Adafruit_BBIO.GPIO as GPIO
#
# GPIO.setup("P8_16", GPIO.IN)
# GPIO.setup("P8_13", GPIO.IN)
# GPIO.setup("P8_17", GPIO.IN)
#
# while True:
#     print(GPIO.input("P8_16"), GPIO.input("P8_13"), GPIO.input("P8_17"))
#     time.sleep(0.3)

