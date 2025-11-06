## Tamper Switch Module Specification (Draft)

### Purpose
- Provide a clean, well-documented Python module to read a tamper switch/push button on BeagleBone Black via GPIO.
- Offer simple APIs for reading button state (pressed/not pressed) with optional debouncing and event callbacks.

### Hardware Assumptions (to confirm)
- Platform: BeagleBone Black.
- Libraries: `Adafruit_BBIO.GPIO`.
- Current script (`MyFirstPythonProject/Tamper.py`) uses:
  - GPIO pin `P9_15` configured as input.
  - Button provides HIGH when pressed, LOW when not pressed (or vice versa - to confirm).
  - Simple polling loop reads state every 0.3 seconds.

Open questions for you to confirm:
1) What is the button's default state (HIGH or LOW when not pressed)?
2) What is the button's active state (HIGH or LOW when pressed)?
3) Is debouncing needed (hardware or software)?
4) Pull-up/pull-down resistor configuration (internal or external)?
5) What is the physical button type (momentary, toggle, tamper switch)?

### Success Criteria
- Simple API for reading button state (pressed/not pressed).
- Optional debouncing to prevent false triggers.
- Optional event callbacks (on_press, on_release).
- Configurable GPIO pin.
- Clean resource handling (open/close/context manager).
- Polling and interrupt-based reading options.

### Out of Scope (initial)
- Multiple buttons in a single module (separate instances per button).
- Complex button sequences or patterns.
- Network/CLI/GUI control surfaces.

### API Design

Class: `TamperSwitch`
- Construction
  - `TamperSwitch(pin: str = "P9_15", *, pull: str = "UP", active_high: bool = True, debounce_ms: int = 50, lazy_hw: bool = False)`
    - `pin`: GPIO pin identifier (default: "P9_15").
    - `pull`: Pull resistor configuration ("UP", "DOWN", or None).
    - `active_high`: True if button press reads HIGH, False if LOW.
    - `debounce_ms`: Debounce delay in milliseconds (0 = no debouncing).
    - `lazy_hw`: Import/init hardware on first use if True.

- Lifecycle
  - `open()` / `close()` and context manager support.

- High-level reading
  - `read() -> bool` - Returns True if pressed, False if not pressed.
  - `is_pressed() -> bool` - Alias for `read()`.
  - `wait_for_press(timeout_s: float = None) -> bool` - Blocks until button is pressed, returns True if pressed, False if timeout.
  - `wait_for_release(timeout_s: float = None) -> bool` - Blocks until button is released, returns True if released, False if timeout.

- Event callbacks (optional)
  - `on_press(callback: Callable) -> None` - Register callback for button press events.
  - `on_release(callback: Callable) -> None` - Register callback for button release events.
  - `clear_callbacks() -> None` - Remove all registered callbacks.

- Low-level
  - `read_raw() -> int` - Returns raw GPIO value (0 or 1).

### Error Handling
- Validate GPIO pin identifier.
- Raise `ValueError` for invalid parameters.
- Hardware errors surface as exceptions; document common causes (GPIO not available, permissions).

### Testing/Examples
- Provide an interactive `__main__` menu similar to other modules to exercise:
  - Read current state
  - Wait for press/release
  - Test with debouncing
  - Simple polling loop demo

### Configuration Defaults (proposed)
- GPIO: `P9_15`
- Pull: UP (to be confirmed)
- Active high: True (to be confirmed)
- Debounce: 50ms (to be confirmed)

### Implementation Plan (post-approval)
1) Implement `TamperSwitch` with init/open/close and basic `read()`.
2) Add debouncing logic.
3) Implement wait functions.
4) Add optional callback support.
5) Add interactive test harness in `__main__` and examples.

### Your Review
Please confirm:
- Button active state (HIGH or LOW when pressed)
- Default state (HIGH or LOW when not pressed)
- Pull resistor configuration
- Debouncing requirements
- Any additional features needed

