## Volume Control Indicator Module Specification (Draft)

### Purpose
- Provide a clean, well-documented Python module that combines a potentiometer with a bar graph display.
- Control bar graph level based on potentiometer reading (0-10 bars mapped from 0-100%).
- Offer simple APIs for reading pot value and updating bar graph display.

### Hardware Assumptions (to confirm)
- Platform: BeagleBone Black.
- Libraries: `Adafruit_BBIO.SPI`, `Adafruit_BBIO.GPIO`, `Adafruit_BBIO.ADC`.
- Two separate boards:
  - Potentiometer on ADC pin `P9_37` (AIN2).
  - Bar graph on SPI bus 1, device 0, mode 0, with GPIO pins `P9_14` and `P9_12`.
- Current script (`MyFirstPythonProject/volumeControlIndicator.py`) shows:
  - Reads potentiometer value (0.0 - 1.0).
  - Maps to bar count: `G_NumberOfBar = int(DigitalValue * 17)` (maps 0-1.0 to 0-17, clamped to 0-10).
  - Updates bar graph display continuously in loop.

Open questions for you to confirm:
1) What is the mapping formula? Current code uses `int(DigitalValue * 17)` which seems unusual.
2) Should mapping be linear (0.0 → 0 bars, 1.0 → 10 bars) or different?
3) Is calibration needed (min/max pot voltage adjustment)?
4) Should we support smoothing/filtering for noisy pot readings?
5) Update rate (continuous polling or event-based)?

### Success Criteria
- Simple API for reading pot value and updating bar graph.
- Configurable mapping between pot voltage and bar count (0-10).
- Optional calibration support.
- Optional smoothing for noisy readings.
- Clean integration of pot and bar graph components.
- Clean resource handling (open/close/context manager).

### Out of Scope (initial)
- Multiple volume controls.
- Complex mapping curves (non-linear).
- Network/CLI/GUI control surfaces.
- Audio volume control (focus on visual indicator only).

### API Design

Class: `VolumeControlIndicator`
- Construction
  - `VolumeControlIndicator(pot_pin: str = "P9_37", *, bar_bus: int = 1, bar_device: int = 0, bar_mode: int = 0, bar_pin_a: str = "P9_14", bar_pin_b: str = "P9_12", min_bars: int = 0, max_bars: int = 10, smoothing_samples: int = 1, mapping: str = "linear", lazy_hw: bool = False)`
    - `pot_pin`: ADC pin for potentiometer.
    - `bar_*`: Bar graph configuration (SPI and GPIO pins).
    - `min_bars`, `max_bars`: Bar count range (default 0-10).
    - `smoothing_samples`: Number of samples for averaging pot reading (1 = no smoothing).
    - `mapping`: Mapping strategy ("linear", "logarithmic", or custom function).
    - `lazy_hw`: Import/init hardware on first use if True.

- Lifecycle
  - `open()` / `close()` and context manager support.

- Main control
  - `update() -> int` - Reads pot value, updates bar graph, returns bar count (0-10).
  - `read_pot_percentage() -> float` - Returns pot reading as percentage (0.0 - 100.0).
  - `read_pot_voltage() -> float` - Returns pot reading as voltage.
  - `get_bar_count() -> int` - Returns current bar graph count.

- Display control
  - `set_bars(count: int) -> None` - Manually sets bar count without reading pot.
  - `set_percentage(pct: float) -> None` - Sets bar count based on percentage.

- Calibration
  - `calibrate_min() -> None` - Sets current pot reading as minimum.
  - `calibrate_max() -> None` - Sets current pot reading as maximum.
  - `reset_calibration() -> None` - Resets calibration to defaults.

- Continuous monitoring (optional)
  - `start_auto_update(interval_s: float = 0.1) -> None` - Starts continuous polling and display updates.
  - `stop_auto_update() -> None` - Stops continuous updates.

- Low-level access
  - `potentiometer` - Property returning underlying `Potentiometer` instance (if implemented separately).
  - `bar_graph` - Property returning underlying `BarGraph` instance (if implemented separately).

### Error Handling
- Validate parameters and ranges.
- Raise `ValueError` for invalid values.
- Hardware errors surface as exceptions.

### Testing/Examples
- Provide an interactive `__main__` menu similar to other modules to exercise:
  - Manual update (read pot and update display)
  - Set bars manually
  - Calibration demo
  - Continuous monitoring demo
  - Smoothing test

### Configuration Defaults (proposed)
- Pot: ADC `P9_37` (AIN2)
- Bar graph: SPI bus 1, device 0, mode 0, GPIO `P9_14`, `P9_12`
- Bar range: 0-10
- Mapping: Linear (0.0 → 0 bars, 1.0 → 10 bars)
- Smoothing: 1 sample (no smoothing by default)
- Update interval: 0.1s (for continuous mode)

### Implementation Plan (post-approval)
1) Implement `VolumeControlIndicator` with init/open/close.
2) Integrate pot reading and bar graph control.
3) Implement mapping logic (linear by default).
4) Add calibration support.
5) Add optional smoothing.
6) Add continuous monitoring functionality.
7) Add interactive test harness in `__main__` and examples.

### Your Review
Please confirm:
- Mapping formula (current code uses `int(DigitalValue * 17)` - is this correct?)
- Desired mapping (linear or different)
- Calibration requirements
- Smoothing needs
- Update rate for continuous mode
- Any additional features needed

