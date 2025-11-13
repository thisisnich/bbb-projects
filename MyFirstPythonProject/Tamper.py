import time
from typing import Optional, Callable


class TamperSwitch:
    """Driver for a tamper switch/push button controlled via GPIO.

    Reads button state (pressed/not pressed) with optional debouncing.
    """

    def __init__(
        self,
        pin: str = "P9_15",
        *,
        pull: str = "UP",
        active_high: bool = True,
        debounce_ms: int = 50,
        lazy_hw: bool = False,
    ) -> None:
        """Initialize the tamper switch.

        Args:
            pin: GPIO pin identifier (default: P9_15)
            pull: Pull resistor configuration ("UP", "DOWN", or None)
            active_high: True if button press reads HIGH, False if LOW
            debounce_ms: Debounce delay in milliseconds (0 = no debouncing)
            lazy_hw: If True, don't initialize hardware until open() is called
        """
        self._pin = pin
        self._pull = pull
        self._active_high = active_high
        self._debounce_ms = debounce_ms
        self._lazy_hw = lazy_hw

        self._GPIO = None  # type: ignore[var-annotated]
        self._last_state = None
        self._last_change_time = 0.0
        self._on_press_callbacks = []
        self._on_release_callbacks = []

        if not self._lazy_hw:
            self.open()

    def open(self) -> None:
        """Open the GPIO connection and initialize the button."""
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

        GPIO.setup(self._pin, GPIO.IN, pull_up_down=pull_value)
        self._last_state = self._read_raw()

    def close(self) -> None:
        """Close the GPIO connection."""
        self._GPIO = None
        self._on_press_callbacks.clear()
        self._on_release_callbacks.clear()

    def __enter__(self) -> "TamperSwitch":
        """Context manager entry."""
        if self._GPIO is None:
            self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Context manager exit."""
        self.close()

    def _read_raw(self) -> int:
        """Read raw GPIO value."""
        if self._GPIO is None:
            self.open()
        return self._GPIO.input(self._pin)  # type: ignore[attr-defined]

    def read(self) -> bool:
        """Read button state (True if pressed, False if not pressed).

        Returns:
            True if button is pressed, False otherwise
        """
        raw = self._read_raw()

        # Apply active_high logic
        if self._active_high:
            pressed = (raw == 1)
        else:
            pressed = (raw == 0)

        # Debouncing
        if self._debounce_ms > 0:
            current_time = time.time() * 1000  # Convert to milliseconds
            if pressed != self._last_state:
                if current_time - self._last_change_time < self._debounce_ms:
                    # Still in debounce period, return previous state
                    return self._last_state if self._last_state is not None else pressed
                # State changed, update timestamps
                self._last_change_time = current_time
                old_state = self._last_state
                self._last_state = pressed

                # Trigger callbacks
                if pressed and old_state is False:
                    for callback in self._on_press_callbacks:
                        try:
                            callback()
                        except Exception:
                            pass
                elif not pressed and old_state is True:
                    for callback in self._on_release_callbacks:
                        try:
                            callback()
                        except Exception:
                            pass
            else:
                self._last_state = pressed
        else:
            # No debouncing
            if pressed != self._last_state:
                old_state = self._last_state
                self._last_state = pressed

                # Trigger callbacks
                if pressed and old_state is False:
                    for callback in self._on_press_callbacks:
                        try:
                            callback()
                        except Exception:
                            pass
                elif not pressed and old_state is True:
                    for callback in self._on_release_callbacks:
                        try:
                            callback()
                        except Exception:
                            pass

        return pressed

    def is_pressed(self) -> bool:
        """Alias for read(). Returns True if pressed, False if not pressed."""
        return self.read()

    def read_raw(self) -> int:
        """Read raw GPIO value (0 or 1)."""
        return self._read_raw()

    def wait_for_press(self, timeout_s: Optional[float] = None) -> bool:
        """Wait until button is pressed.

        Args:
            timeout_s: Maximum time to wait in seconds (None = infinite)

        Returns:
            True if button was pressed, False if timeout
        """
        start_time = time.time()
        while True:
            if self.read():
                return True
            if timeout_s is not None and (time.time() - start_time) >= timeout_s:
                return False
            time.sleep(0.01)  # Small delay to avoid busy-waiting

    def wait_for_release(self, timeout_s: Optional[float] = None) -> bool:
        """Wait until button is released.

        Args:
            timeout_s: Maximum time to wait in seconds (None = infinite)

        Returns:
            True if button was released, False if timeout
        """
        start_time = time.time()
        while True:
            if not self.read():
                return True
            if timeout_s is not None and (time.time() - start_time) >= timeout_s:
                return False
            time.sleep(0.01)  # Small delay to avoid busy-waiting

    def on_press(self, callback: Callable[[], None]) -> None:
        """Register callback for button press events.

        Args:
            callback: Function to call when button is pressed
        """
        self._on_press_callbacks.append(callback)

    def on_release(self, callback: Callable[[], None]) -> None:
        """Register callback for button release events.

        Args:
            callback: Function to call when button is released
        """
        self._on_release_callbacks.append(callback)

    def clear_callbacks(self) -> None:
        """Remove all registered callbacks."""
        self._on_press_callbacks.clear()
        self._on_release_callbacks.clear()


def _print_menu() -> None:
    """Print the test menu."""
    print("\nTamper Switch test menu:")
    print("  1) read")
    print("  2) is_pressed")
    print("  3) read_raw")
    print("  4) wait_for_press [timeout_s]")
    print("  5) wait_for_release [timeout_s]")
    print("  6) poll_loop [interval_s] [count]")
    print("  q) quit")


if __name__ == "__main__":
    button = TamperSwitch()
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
                    state = button.read()
                    print(f"Button is {'PRESSED' if state else 'NOT PRESSED'}")
                elif cmd == "2":
                    state = button.is_pressed()
                    print(f"Button is {'PRESSED' if state else 'NOT PRESSED'}")
                elif cmd == "3":
                    raw = button.read_raw()
                    print(f"Raw GPIO value: {raw}")
                elif cmd == "4":
                    timeout = float(parts[1]) if len(parts) > 1 else None
                    print(f"Waiting for press (timeout={timeout or 'infinite'}s)...")
                    result = button.wait_for_press(timeout)
                    print(f"Button {'PRESSED' if result else 'TIMEOUT'}")
                elif cmd == "5":
                    timeout = float(parts[1]) if len(parts) > 1 else None
                    print(f"Waiting for release (timeout={timeout or 'infinite'}s)...")
                    result = button.wait_for_release(timeout)
                    print(f"Button {'RELEASED' if result else 'TIMEOUT'}")
                elif cmd == "6":
                    interval = float(parts[1]) if len(parts) > 1 else 0.3
                    count = int(parts[2]) if len(parts) > 2 else 10
                    print(f"Polling loop (interval={interval}s, count={count})...")
                    for i in range(count):
                        state = button.read()
                        print(f"[{i+1}] Button is {'PRESSED' if state else 'NOT PRESSED'}")
                        time.sleep(interval)
                else:
                    print("unknown command")
            except Exception as e:
                print(f"error: {e}")
    finally:
        button.close()
        print("\nButton closed")


# ============================================================================
# ORIGINAL CODE (commented for reference)
# ============================================================================
# #tamper code
#
# import time
# import Adafruit_BBIO.GPIO as GPIO
#
# GPIO.setup("P9_15", GPIO.IN)
#
# while True:
#     if GPIO.input("P9_15"):
#         print("Push Button is Pressed")
#     else:
#         print("Push Button is Not Pressed")
#     time.sleep(0.3)
