## BarGraph Module Specification (Draft)

### Purpose
- Provide a clean, well-documented Python module to fully utilize a 10-LED bar graph on BeagleBone Black via SPI and GPIO.
- Offer high-level APIs for common tasks (set bars, set percentage, clear/fill, animations) and a low-level API for raw bit patterns.

### Hardware Assumptions (to confirm)
- Platform: BeagleBone Black.
- Libraries: `Adafruit_BBIO.SPI` and `Adafruit_BBIO.GPIO`.
- Bar graph appears to be driven by chained shift register(s) (e.g., 74HC595 or LED driver) using 3 output bytes per update.
- `bar.py` writes 3 bytes per state; examples:
  - 0 bars: `[0x00, 0x00, 0x00]`
  - 1 bar:  `[0x00, 0x00, 0x01]`
  - 5 bars: `[0x00, 0x40, 0x1F]`
  - 10 bars: `[0x0F, 0xC0, 0xFF]`
- Two GPIO pins `P9_14` and `P9_12` are configured as outputs and set HIGH in init. Their exact roles are unclear (likely latch/enable or power control). These will be configurable.
- SPI: Bus 1, device 0, SPI mode 0 as per current code.

Open questions for you to confirm:
1) What exact hardware is behind the bar (part numbers, wiring)?
2) What are the functions of `P9_14` and `P9_12` (latch/OE/power/other)? Required idle levels?
3) LED order and direction: should bar 1 be leftmost or rightmost? Do we need a reversible option?
4) Brightness control required (global PWM via OE or per-LED brightness)? Or simple on/off only?
5) Safe import on non-BeagleBone (defer hardware import) needed, or not necessary?

### Success Criteria
- Simple, discoverable API with docstrings and type hints.
- Can set any bar count 0–10 consistently; mapping matches physical LED order.
- Supports percentage-based control (0–100%) with rounding strategy documented.
- Provides low-level raw mask function for advanced patterns.
- Optional animations (sweep, bounce) with clean cancellation.
- Configurable pins and SPI parameters; sensible defaults to current code.
- Clean resource handling: open/close SPI and GPIO; context manager support.

### Out of Scope (initial)
- Complex per-LED brightness control unless hardware clearly supports it.
- Network/CLI/GUI control surfaces.

### API Design

Class: `BarGraph`
- Construction
  - `BarGraph(bus: int = 1, device: int = 0, mode: int = 0, max_bars: int = 10, pin_a: str = "P9_14", pin_b: str = "P9_12", reverse: bool = False, lazy_hw: bool = False)`
    - `pin_a`/`pin_b`: configurable GPIOs (roles clarified in hardware section). Idle levels configurable if needed.
    - `reverse`: logical left/right reversal.
    - `lazy_hw`: if True, delay importing/initializing hardware until first use, to allow import on non-BBB hosts.

- Lifecycle
  - `open()` → initialize SPI and GPIO
  - `close()` → release resources
  - Context manager: `with BarGraph(...) as bg:`

- High-level control
  - `set_bars(count: int) -> None`
    - Sets 0…`max_bars` LEDs lit according to direction and mapping.
  - `set_percentage(pct: float, *, rounding: Literal["floor","nearest","ceil"] = "nearest") -> int`
    - Converts percentage to bar count, applies, returns count used.
  - `clear() -> None` (alias for `set_bars(0)`).
  - `fill() -> None` (alias for `set_bars(max_bars)`).
  - `set_segments(colors: dict[int, Literal["off","green","red","amber"]]) -> None`
    - Arbitrary per-segment color control (order-independent). Keys are segment indices 1..10 (right→left). Unspecified segments remain unchanged unless `clear_others=True` is added (optional parameter).
  - `set_row(colors: list[Literal["off","green","red","amber"]]) -> None`
    - Convenience to set all 10 segments in one call using a list of length 10 (index 0 = seg 1 at the right).

- Low-level control
  - `set_mask(b0: int, b1: int, b2: int) -> None`
    - Sends raw 3-byte pattern; caller responsible for bit layout.
  - `get_mask_for_bars(count: int) -> tuple[int,int,int]`
    - Returns the 3-byte mask for a given bar count using the selected direction; helpful for preview/testing.
  - `set_color_mask(green_mask: int, red_mask: int) -> None`
    - Color-aware helper: apply 10-bit masks for green and red segments; module maps to the 3 SPI bytes.
  - `encode_colors(colors: list[Literal["off","green","red","amber"]]) -> tuple[int,int,int]` 
    - Pure function: convert a 10-length color list into the three SPI bytes without sending (useful for previews/tests).

- Animations (optional, cancellable)
  - `animate_sweep(delay_s: float = 0.1, cycles: int | None = None) -> None`
  - `animate_bounce(delay_s: float = 0.1, cycles: int | None = None) -> None`
  - Implementation will be synchronous by default; optional stop flag if run in a thread by caller.

### Bit Mapping, Colors, and Direction (to verify)

Bi-color model:
- 10 segments, each with Green and Red LED; both on simultaneously yield Amber.
- Ordering from right to left: Green seg 1→10, then Red seg 1→10 (right→left).
- Total control bits: 20 (10 green + 10 red), mapped into 24 bits (3 SPI bytes). Four bits are unused.

Proposed byte/bit layout (LSB at right):
```
[B0][B1][B2]  // MSB ................ LSB

B2 (8 bits, LSB side):   gggggggg   -> Green segments 1..8 (right→left)
B1 (8 bits):             RRRRRRGG   -> Red segments 1..6 (bits 2..7), Green segments 9..10 (bits 0..1)
B0 (8 bits, MSB side):   xxxxRRRR   -> Unused (bits 4..7), Red segments 7..10 (bits 0..3)
```

Current `bar.py` suggests an accumulation pattern for a monochrome ramp (greens only):

```
g = green, r= red, a=amber(the red and green leds both on), x= off
0  -> [0x00, 0x00, 0x00] all off
1  -> [0x00, 0x00, 0x01] gxxxxxxxxx
2  -> [0x00, 0x00, 0x03] ggxxxxxxxx
3  -> [0x00, 0x00, 0x07] gggxxxxxxx
4  -> [0x00, 0x00, 0x0F] ggggxxxxxx
5  -> [0x00, 0x40, 0x1F] ggggaxxxxx
6  -> [0x00, 0xC0, 0x3F] ggggaaxxxx
7  -> [0x01, 0xC0, 0x7F] ggggaaaxxx
8  -> [0x03, 0xC0, 0xFF] ggggaaaaxx
9  -> [0x07, 0xC0, 0xFF] ggggaaaarx
10 -> [0x0F, 0xC0, 0xFF] ggggaaaarr
```

Interpreting with the proposed layout and your observed behavior:
- `B2` increments for Green segs 1..8.
- `B1` bits 6..7 (`0x40`, `0x80`) are Red segs 5..6 (explains count=5→`0x40`, count=6→`0xC0`).
- `B0` low nibble represents Red segs 7..10 (explains counts 7..10 increasing `B0`).
- `B1` bits 0..1 can be used for Green segs 9..10 when explicitly setting green beyond 8.

We will implement:
- Mapping helpers for green-only ramp and color-aware masks.
- Optional `reverse=True` to invert logical left/right if physical orientation differs.

Questions to confirm mapping:
- Please confirm the byte/bit layout above aligns with your wiring.
- Are any bits truly reserved/unused beyond the four MSBs of `B0`? Any special meanings for `B1`'s `0xC0` when greens 9–10 are on?

### Error Handling
- Validate inputs (e.g., `0 <= count <= max_bars`, `0 <= pct <= 100` with clamping or error per spec).
- Raise clear `ValueError` for invalid parameters.
- Hardware errors surface as exceptions; document common causes (SPI not available, permissions).

### Testing/Examples
- Provide an `examples/bar_demo.py`:
  - Ramp 0→10 bars with delays.
  - Percentage demo at 0%, 25%, 50%, 75%, 100%.
  - Sweep and bounce animations (short).
- Optional mock backend when `lazy_hw=True` on non-BBB for import-time testability.

### Configuration Defaults (proposed)
- SPI: bus=1, device=0, mode=0
- GPIO pins: `P9_14` and `P9_12` as in current code; both default HIGH on init (until clarified).
- Max bars: 10
- Default delay for animations: 0.1s

### Implementation Plan (post-approval)
1) Implement `BarGraph` with init/open/close and raw `set_mask`.
2) Add mapping table for `count -> (b0,b1,b2)` including reverse support.
3) Implement `set_bars`, `set_percentage`, `clear`, `fill`.
4) Add animations and example script.
5) Inline docstrings and type hints; short README in examples.

### Your Review
Please confirm:
- Hardware details, pin roles, and idle levels
- Direction/orientation of the bar
- Whether brightness/PWM is required
- Mapping table correctness for 0–10 bars
- Any additional features you need (e.g., blinking patterns)


