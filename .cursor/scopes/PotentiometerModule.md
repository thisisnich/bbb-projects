## Potentiometer Module Specification (Draft)

### Purpose
- Provide a clean, well-documented Python module to read a potentiometer on BeagleBone Black via ADC.
- Offer simple APIs for reading voltage, percentage, and raw ADC values with optional calibration.

### Hardware Assumptions (to confirm)
- Platform: BeagleBone Black.
- Libraries: `Adafruit_BBIO.ADC`.
- Current script (`MyFirstPythonProject/pot.py`) uses:
  - ADC pin `P9_37` (AIN2).
  - Reads digital value (0.0 - 1.0) and converts to analog voltage (0.0 - 1.8V).
  - Formula: `AnalogVoltage = DigitalValue * 1.8`

Open questions for you to confirm:
1) What is the potentiometer's voltage range (0-1.8V or different)?
2) What is the physical rotation range (e.g., 270°, 300°)?
3) Is calibration needed (min/max voltage adjustment)?
4) Should we support percentage-based readings (0-100%)?
5) Is filtering/smoothing needed for noisy readings?

### Success Criteria
- Simple API for reading voltage, percentage, and raw ADC values.
- Optional calibration support (min/max voltage adjustment).
- Optional filtering/smoothing for noisy readings.
- Configurable ADC pin.
- Clean resource handling (open/close/context manager).

### Out of Scope (initial)
- Multiple potentiometers in a single module (separate instances per pot).
- Complex calibration curves or non-linear mapping.
- Network/CLI/GUI control surfaces.

### API Design

Class: `Potentiometer`
- Construction
  - `Potentiometer(pin: str = "P9_37", *, voltage_range: Tuple[float, float] = (0.0, 1.8), calibrated_min: float = None, calibrated_max: float = None, smoothing_samples: int = 1, lazy_hw: bool = False)`
    - `pin`: ADC pin identifier (default: "P9_37").
    - `voltage_range`: Expected voltage range `(min_voltage, max_voltage)`, default (0.0, 1.8).
    - `calibrated_min`: Calibrated minimum voltage (None = use voltage_range min).
    - `calibrated_max`: Calibrated maximum voltage (None = use voltage_range max).
    - `smoothing_samples`: Number of samples for averaging (1 = no smoothing).
    - `lazy_hw`: Import/init hardware on first use if True.

- Lifecycle
  - `open()` / `close()` and context manager support.

- High-level reading
  - `read_voltage() -> float` - Returns voltage in volts (0.0 - 1.8V or calibrated range).
  - `read_percentage() -> float` - Returns percentage (0.0 - 100.0) based on voltage range.
  - `read_raw() -> float` - Returns raw ADC digital value (0.0 - 1.0).
  - `read_raw_voltage() -> float` - Returns raw ADC voltage without calibration (0.0 - 1.8V).

- Calibration
  - `calibrate_min() -> None` - Sets current reading as minimum voltage.
  - `calibrate_max() -> None` - Sets current reading as maximum voltage.
  - `reset_calibration() -> None` - Resets to voltage_range defaults.
  - `get_calibration() -> Tuple[float, float]` - Returns current calibration range.

### Error Handling
- Validate ADC pin identifier.
- Raise `ValueError` for invalid parameters (e.g., min >= max).
- Hardware errors surface as exceptions.

### Testing/Examples
- Provide an interactive `__main__` menu similar to other modules to exercise:
  - Read voltage
  - Read percentage
  - Display raw values
  - Calibration demo
  - Simple polling loop demo

### Configuration Defaults (proposed)
- ADC: `P9_37` (AIN2)
- Voltage range: (0.0, 1.8) volts
- Smoothing: 1 sample (no smoothing by default)
- Formula: `AnalogVoltage = DigitalValue * 1.8`

### Implementation Plan (post-approval)
1) Implement `Potentiometer` with init/open/close and basic `read_voltage()`.
2) Add percentage calculation.
3) Implement calibration support.
4) Add optional smoothing/filtering.
5) Add interactive test harness in `__main__` and examples.

### Your Review
Please confirm:
- Voltage range (0-1.8V or different)
- Physical rotation range
- Calibration requirements
- Smoothing/filtering needs
- Any additional features needed

