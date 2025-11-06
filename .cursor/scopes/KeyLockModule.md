## Key Lock Module Specification (Draft)

### Purpose
- Provide a clean, well-documented Python module to read a 3-position key lock switch on BeagleBone Black via GPIO.
- Detect lock position by reading 3 GPIO inputs that encode the position (one-hot encoding).
- Offer simple APIs for position detection and optional position change events.

### Hardware Assumptions (to confirm)
- Platform: BeagleBone Black.
- Libraries: `Adafruit_BBIO.GPIO`.
- Current script (`MyFirstPythonProject/keylock2.py`) uses:
  - GPIO pins `P8_16`, `P8_13`, `P8_17` configured as inputs.
  - Position encoding (one-hot):
    - Position 1: `[0, 0, 1]` (P8_16=0, P8_13=0, P8_17=1)
    - Position 2: `[0, 1, 0]` (P8_16=0, P8_13=1, P8_17=0)
    - Position 3: `[1, 0, 0]` (P8_16=1, P8_13=0, P8_17=0)

Open questions for you to confirm:
1) What are the position names (e.g., "OFF", "ON1", "ON2" or "LOCK", "UNLOCK", "ALARM")?
2) Are pull-up/pull-down resistors needed (internal or external)?
3) Is debouncing needed for position changes?
4) Should we support custom position mappings?
5) What happens if multiple pins are HIGH (invalid state)?

### Success Criteria
- Simple API for detecting current lock position.
- Optional position name mapping (numeric 1-3 or custom labels).
- Detection of invalid states (multiple pins HIGH simultaneously).
- Optional position change events/callbacks.
- Clean resource handling (open/close/context manager).

### Out of Scope (initial)
- Multiple key locks in a single module (separate instances per lock).
- Complex lock sequences or patterns.
- Network/CLI/GUI control surfaces.

### API Design

Class: `KeyLock`
- Construction
  - `KeyLock(pin_a: str = "P8_16", pin_b: str = "P8_13", pin_c: str = "P8_17", *, position_names: Dict[int, str] = None, pull: str = "UP", lazy_hw: bool = False)`
    - `pin_a`, `pin_b`, `pin_c`: GPIO pin identifiers.
    - `position_names`: Custom position names dict, e.g., `{1: "OFF", 2: "ON", 3: "ALARM"}`. Default: {1: "Position1", 2: "Position2", 3: "Position3"}.
    - `pull`: Pull resistor configuration ("UP", "DOWN", or None) for all pins.
    - `lazy_hw`: Import/init hardware on first use if True.

- Lifecycle
  - `open()` / `close()` and context manager support.

- High-level reading
  - `read_position() -> int` - Returns position number (1, 2, or 3).
  - `read_position_name() -> str` - Returns position name string.
  - `is_position(position: int | str) -> bool` - Returns True if lock is in specified position.
  - `wait_for_position(position: int | str, timeout_s: float = None) -> bool` - Blocks until lock reaches specified position, returns True if reached, False if timeout.

- Low-level
  - `read_raw() -> Tuple[int, int, int]` - Returns raw GPIO values `(pin_a, pin_b, pin_c)`.
  - `read_binary() -> Tuple[int, int, int]` - Alias for `read_raw()`.

- State validation
  - `is_valid_state() -> bool` - Returns True if exactly one pin is HIGH (valid one-hot encoding).
  - `get_invalid_reason() -> str | None` - Returns error message if state is invalid, None if valid.

- Event callbacks (optional)
  - `on_position_change(callback: Callable[[int, str]]) -> None` - Register callback for position change events (receives position number and name).

### Error Handling
- Validate GPIO pin identifiers.
- Detect invalid states (multiple pins HIGH or all LOW).
- Raise `ValueError` for invalid parameters.
- Hardware errors surface as exceptions.

### Testing/Examples
- Provide an interactive `__main__` menu similar to other modules to exercise:
  - Read current position
  - Test all positions
  - Display raw values
  - Test invalid state detection
  - Simple polling loop demo

### Configuration Defaults (proposed)
- GPIO pins: `P8_16`, `P8_13`, `P8_17`
- Position encoding:
  - Position 1: [0, 0, 1]
  - Position 2: [0, 1, 0]
  - Position 3: [1, 0, 0]
- Position names: {1: "Position1", 2: "Position2", 3: "Position3"} (to be customized)
- Pull: UP (to be confirmed)

### Implementation Plan (post-approval)
1) Implement `KeyLock` with init/open/close and basic `read_position()`.
2) Add position name mapping.
3) Implement invalid state detection.
4) Add optional callback support.
5) Add interactive test harness in `__main__` and examples.

### Your Review
Please confirm:
- Position names/labels (e.g., "OFF", "ON1", "ON2" or "LOCK", "UNLOCK", "ALARM")
- Pull resistor configuration
- Debouncing requirements
- How to handle invalid states
- Any additional features needed

