## Press Counter Module Specification (Draft)

### Purpose
- Provide a clean, well-documented Python module that combines a tamper switch (push button) with a 7-segment display.
- Display a counter (0-99) that increments each time the button is pressed.
- Offer simple APIs for counter control, reset, and display updates.

### Hardware Assumptions (to confirm)
- Platform: BeagleBone Black.
- Libraries: `Adafruit_BBIO.SPI`, `Adafruit_BBIO.GPIO`.
- Two separate boards:
  - Tamper switch on GPIO pin `P9_15`.
  - 7-segment display on SPI bus 0, device 0, mode 0, with GPIO pins `P8_19` and `P8_14`.
- Current script (`MyFirstPythonProject/pressCounter.py`) shows:
  - Counter increments on button press (0-99, wraps to 0).
  - Display updates immediately after increment.

Open questions for you to confirm:
1) Should counter wrap at 99 or stop at 99?
2) Should we support decrement functionality?
3) Should we support manual counter setting?
4) Is debouncing needed for the button?
5) Should we support preset values (e.g., reset to 0, set to specific number)?

### Success Criteria
- Simple API for incrementing/decrementing counter.
- Automatic display update when counter changes.
- Optional manual counter setting.
- Reset functionality.
- Clean integration of button and display components.
- Clean resource handling (open/close/context manager).

### Out of Scope (initial)
- Multiple counters.
- Complex button sequences (long press, double click).
- Network/CLI/GUI control surfaces.
- Persistent storage of counter value.

### API Design

Class: `PressCounter`
- Construction
  - `PressCounter(button_pin: str = "P9_15", *, seg_bus: int = 0, seg_device: int = 0, seg_mode: int = 0, seg_pin_a: str = "P8_19", seg_pin_b: str = "P8_14", min_value: int = 0, max_value: int = 99, wrap: bool = True, debounce_ms: int = 50, lazy_hw: bool = False)`
    - `button_pin`: GPIO pin for tamper switch.
    - `seg_*`: 7-segment display configuration (SPI and GPIO pins).
    - `min_value`, `max_value`: Counter range (default 0-99).
    - `wrap`: If True, counter wraps at limits; if False, stops at limits.
    - `debounce_ms`: Button debounce delay.
    - `lazy_hw`: Import/init hardware on first use if True.

- Lifecycle
  - `open()` / `close()` and context manager support.

- Counter control
  - `increment() -> int` - Increments counter and updates display, returns new value.
  - `decrement() -> int` - Decrements counter and updates display, returns new value.
  - `set_value(value: int) -> None` - Sets counter to specific value and updates display.
  - `reset() -> None` - Resets counter to min_value and updates display.
  - `get_value() -> int` - Returns current counter value.

- Display control
  - `update_display() -> None` - Manually updates display with current counter value.
  - `show(value: int) -> None` - Displays arbitrary value without changing counter.

- Button monitoring (optional)
  - `poll() -> bool` - Checks button state and increments if pressed, returns True if incremented.
  - `start_auto_poll(interval_s: float = 0.01) -> None` - Starts background polling (optional, simple implementation).
  - `stop_auto_poll() -> None` - Stops background polling.

- Low-level access
  - `button` - Property returning underlying `TamperSwitch` instance (if implemented separately).
  - `display` - Property returning underlying `SevenSegment` instance (if implemented separately).

### Error Handling
- Validate counter range and parameters.
- Raise `ValueError` for invalid values (out of range).
- Hardware errors surface as exceptions.

### Testing/Examples
- Provide an interactive `__main__` menu similar to other modules to exercise:
  - Increment/decrement counter
  - Set specific value
  - Reset counter
  - Manual polling demo
  - Simple automatic polling demo

### Configuration Defaults (proposed)
- Button: GPIO `P9_15`
- Display: SPI bus 0, device 0, mode 0, GPIO `P8_19`, `P8_14`
- Counter range: 0-99
- Wrap: True
- Debounce: 50ms

### Implementation Plan (post-approval)
1) Implement `PressCounter` with init/open/close.
2) Integrate button reading and display control.
3) Implement counter increment/decrement logic.
4) Add manual value setting and reset.
5) Add optional polling functionality.
6) Add interactive test harness in `__main__` and examples.

### Your Review
Please confirm:
- Counter range (0-99 or different)
- Wrap behavior (wrap at limits or stop)
- Decrement support needed
- Manual value setting needed
- Debouncing requirements
- Any additional features needed

