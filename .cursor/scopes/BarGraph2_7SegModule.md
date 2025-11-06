## Bar Graph + 7-Segment Display Module Specification (Draft)

### Purpose
- Provide a clean, well-documented Python module that combines a bar graph with a 7-segment display.
- Display the same value on both displays simultaneously (bar count 0-10 and number 0-99).
- Offer simple APIs for synchronized display updates and animations.

### Hardware Assumptions (to confirm)
- Platform: BeagleBone Black.
- Libraries: `Adafruit_BBIO.SPI`, `Adafruit_BBIO.GPIO`.
- Two separate boards:
  - Bar graph on SPI bus 1, device 0, mode 0, with GPIO pins `P9_14` and `P9_12`.
  - 7-segment display on SPI bus 0, device 0, mode 0, with GPIO pins `P8_19` and `P8_14`.
- Current script (`MyFirstPythonProject/BarGraph2_7Seg.py`) shows:
  - Displays number on 7-seg (0-99, increments).
  - Displays bar count on bar graph (1-10, increments every 10 number cycles).
  - Both update in sync.

Open questions for you to confirm:
1) Should both displays show the same value (0-10) or different ranges (bar: 0-10, 7-seg: 0-99)?
2) What is the relationship between bar count and 7-seg number?
3) Should we support independent control of each display?
4) Should we support synchronized animations?
5) What update rate/speed is desired?

### Success Criteria
- Simple API for displaying values on both displays simultaneously.
- Synchronized updates (both displays update together).
- Support for different value ranges per display.
- Optional independent control of each display.
- Clean integration of both components.
- Clean resource handling (open/close/context manager).

### Out of Scope (initial)
- Multiple display pairs.
- Complex synchronization requirements.
- Network/CLI/GUI control surfaces.

### API Design

Class: `BarGraph7Seg`
- Construction
  - `BarGraph7Seg(bar_bus: int = 1, bar_device: int = 0, bar_mode: int = 0, bar_pin_a: str = "P9_14", bar_pin_b: str = "P9_12", seg_bus: int = 0, seg_device: int = 0, seg_mode: int = 0, seg_pin_a: str = "P8_19", seg_pin_b: str = "P8_14", bar_range: Tuple[int, int] = (0, 10), seg_range: Tuple[int, int] = (0, 99), sync_mode: str = "auto", lazy_hw: bool = False)`
    - `bar_*`: Bar graph configuration (SPI and GPIO pins).
    - `seg_*`: 7-segment display configuration (SPI and GPIO pins).
    - `bar_range`: Bar graph value range (default 0-10).
    - `seg_range`: 7-segment display value range (default 0-99).
    - `sync_mode`: Synchronization mode ("auto" = same value, "independent" = different values, "ratio" = bar = seg/10).
    - `lazy_hw`: Import/init hardware on first use if True.

- Lifecycle
  - `open()` / `close()` and context manager support.

- Synchronized display
  - `show(value: int) -> None` - Displays value on both displays (bar shows 0-10, 7-seg shows 0-99, auto-mapped).
  - `show_sync(bar_value: int, seg_value: int) -> None` - Displays different values on each display.
  - `show_bar(value: int) -> None` - Updates only bar graph.
  - `show_seg(value: int) -> None` - Updates only 7-segment display.
  - `clear() -> None` - Clears both displays.

- Value mapping
  - `map_value_to_bar(value: int) -> int` - Maps value (0-99) to bar count (0-10).
  - `map_value_to_seg(value: int) -> int` - Maps value to 7-seg range (0-99).

- Animations (optional)
  - `animate_count(start: int = 0, stop: int = 99, step: int = 1, delay_s: float = 0.1) -> None` - Counts up/down on both displays.
  - `animate_sweep(delay_s: float = 0.1, cycles: int = None) -> None` - Sweeps both displays from min to max.
  - `animate_sync(delay_s: float = 0.1, cycles: int = None) -> None` - Synchronized animation on both displays.

- Low-level access
  - `bar_graph` - Property returning underlying `BarGraph` instance (if implemented separately).
  - `seven_segment` - Property returning underlying `SevenSegment` instance (if implemented separately).

### Error Handling
- Validate value ranges for each display.
- Raise `ValueError` for invalid values or ranges.
- Hardware errors surface as exceptions.

### Testing/Examples
- Provide an interactive `__main__` menu similar to other modules to exercise:
  - Display same value on both
  - Display different values
  - Independent control
  - Count animation
  - Sweep animation

### Configuration Defaults (proposed)
- Bar graph: SPI bus 1, device 0, mode 0, GPIO `P9_14`, `P9_12`
- 7-segment: SPI bus 0, device 0, mode 0, GPIO `P8_19`, `P8_14`
- Bar range: 0-10
- 7-seg range: 0-99
- Sync mode: "auto" (bar = value/10, 7-seg = value)
- Default delay: 0.1s

### Implementation Plan (post-approval)
1) Implement `BarGraph7Seg` with init/open/close.
2) Integrate both display components.
3) Implement value mapping logic.
4) Add synchronized display updates.
5) Add independent control options.
6) Add animation functions.
7) Add interactive test harness in `__main__` and examples.

### Your Review
Please confirm:
- Value relationship (bar: 0-10, 7-seg: 0-99, or different)
- Sync mode preference (auto, independent, ratio)
- Animation requirements
- Update rate/speed
- Any additional features needed

