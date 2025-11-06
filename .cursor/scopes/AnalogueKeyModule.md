## Analogue Keypad Module Specification (Draft)

### Purpose
- Provide a clean, well-documented Python module to read a 6-key analog keypad on BeagleBone Black via ADC.
- Detect which key is pressed by reading voltage thresholds on an analog input.
- Offer simple APIs for key detection and optional key press/release events.

### Hardware Assumptions (to confirm)
- Platform: BeagleBone Black.
- Libraries: `Adafruit_BBIO.ADC`.
- Current script (`MyFirstPythonProject/analogueKey.py`) uses:
  - ADC pin `P9_40` (AIN1).
  - 6 keys (T1-T6) with voltage divider network.
  - Voltage thresholds from code:
    - No key: 0.00 - 0.10
    - T6: 0.16 - 0.18
    - T5: 0.33 - 0.35
    - T4: 0.50 - 0.52
    - T3: 0.67 - 0.69
    - T2: 0.84 - 0.86
    - T1: 0.90 - 1.10

Open questions for you to confirm:
1) Are the voltage thresholds accurate and stable?
2) Is debouncing needed for key presses?
3) Should we support custom voltage thresholds?
4) What are the physical key labels (T1-T6 or custom)?
5) Is simultaneous key press detection needed (unlikely with analog)?

### Success Criteria
- Simple API for detecting which key is currently pressed.
- Optional key name mapping (T1-T6 or custom labels).
- Configurable voltage thresholds with reasonable defaults.
- Optional debouncing to prevent false triggers.
- Clean resource handling (open/close/context manager).

### Out of Scope (initial)
- Multiple keypads in a single module (separate instances per keypad).
- Complex key sequences or combinations.
- Network/CLI/GUI control surfaces.

### API Design

Class: `AnalogueKeypad`
- Construction
  - `AnalogueKeypad(pin: str = "P9_40", *, thresholds: Dict[str, Tuple[float, float]] = None, debounce_ms: int = 50, lazy_hw: bool = False)`
    - `pin`: ADC pin identifier (default: "P9_40").
    - `thresholds`: Custom voltage thresholds dict, e.g., `{"T1": (0.90, 1.10), ...}`. If None, uses defaults.
    - `debounce_ms`: Debounce delay in milliseconds (0 = no debouncing).
    - `lazy_hw`: Import/init hardware on first use if True.

- Lifecycle
  - `open()` / `close()` and context manager support.

- High-level reading
  - `read_key() -> str | None` - Returns key name if pressed, None if no key pressed.
  - `is_key_pressed(key: str) -> bool` - Returns True if specified key is pressed.
  - `get_all_keys() -> List[str]` - Returns list of all available key names.
  - `wait_for_key(timeout_s: float = None) -> str | None` - Blocks until any key is pressed, returns key name or None if timeout.

- Low-level
  - `read_voltage() -> float` - Returns raw ADC voltage reading (0.0 - 1.8V).
  - `read_raw() -> float` - Returns raw ADC digital value (0.0 - 1.0).

- Utility
  - `calibrate_key(key: str, samples: int = 10) -> Tuple[float, float]` - Reads multiple samples to determine voltage range for a key (helper for calibration).

### Error Handling
- Validate ADC pin identifier.
- Raise `ValueError` for invalid key names or parameters.
- Hardware errors surface as exceptions; document common causes (ADC not available, permissions).

### Testing/Examples
- Provide an interactive `__main__` menu similar to other modules to exercise:
  - Read current key
  - Test all keys
  - Display raw voltage
  - Calibration helper
  - Simple polling loop demo

### Configuration Defaults (proposed)
- ADC: `P9_40` (AIN1)
- Default thresholds (from current code):
  - No key: (0.00, 0.10)
  - T6: (0.16, 0.18)
  - T5: (0.33, 0.35)
  - T4: (0.50, 0.52)
  - T3: (0.67, 0.69)
  - T2: (0.84, 0.86)
  - T1: (0.90, 1.10)
- Debounce: 50ms (to be confirmed)

### Implementation Plan (post-approval)
1) Implement `AnalogueKeypad` with init/open/close and basic `read_key()`.
2) Add voltage threshold matching logic.
3) Implement debouncing.
4) Add calibration helper.
5) Add interactive test harness in `__main__` and examples.

### Your Review
Please confirm:
- Voltage thresholds accuracy
- Key naming convention (T1-T6 or custom)
- Debouncing requirements
- Any additional features needed

