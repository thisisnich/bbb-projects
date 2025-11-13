## Seven-Segment Display Module Specification (Draft)

### Purpose
- Provide a clean, well-documented Python module to drive a 2-digit 7-segment display over SPI with GPIO control on BeagleBone Black.
- Offer high-level APIs for showing numbers, strings (subset), and per-segment control, plus low-level raw byte access.

### Hardware Assumptions (to confirm)
- Platform: BeagleBone Black.
- Libraries: `Adafruit_BBIO.SPI` and `Adafruit_BBIO.GPIO`.
- Current script (`MyFirstPythonProject/7seg.py`) uses:
  - SPI bus 0, device 0, mode 0.
  - GPIO pins `P8_19` and `P8_14` set HIGH on init (likely latch/OE/power). These should be configurable.
- Two bytes are written per update: `[ones, tens]` using a lookup table `DigitList`.
- Lookup table (from code): `DigitList = [0x7E, 0x0A, 0xB6, 0x9E, 0xCA, 0xDC, 0xFC, 0x0E, 0xFE, 0xDE]` for digits 0..9.
- Endianness/order: Current code writes ones first, then tens. Confirm wiring expects `[ones, tens]` (not `[tens, ones]`).

Open questions for you to confirm:
1) Exact driver IC(s) or shift-register behind the display? Common anode or common cathode?
2) Segment bit mapping for a single digit (a/b/c/d/e/f/g + optional DP). Is `0x7E` intended for digit 0 and which bit is DP?
3) Are `P8_19` and `P8_14` latch/OE, and what are the required idle levels and sequencing (if any)?
4) Should the module support decimal points (DP) per digit?
5) Do you need minus sign, blanks, or limited alphabet (A,b,C,d,E,F,H,L,P,U, etc.)?
6) Is the ones-then-tens byte order fixed, or should we make it configurable?

### Success Criteria
- Simple API for displaying 0–99 with optional leading zero suppression.
- Support DP per digit and a small set of letters/symbols (documented), plus custom per-segment control.
- Configurable pins and SPI; clean resource handling (open/close/context manager).
- Optional animations (count up/down), and flashing.

### Out of Scope (initial)
- Multiplexing more than 2 digits.
- Fonts for full ASCII; we’ll implement a small, practical subset.

### API Design

Class: `SevenSegment`
- Construction
  - `SevenSegment(bus: int = 0, device: int = 0, *, mode: int = 0, pin_a: str = "P8_19", pin_b: str = "P8_14", order: str = "ones,tens", lazy_hw: bool = False)`
    - `order`: write order of bytes, default `"ones,tens"`; allow `"tens,ones"` if wiring requires.
    - `lazy_hw`: import/init hardware on first use if True.

- Lifecycle
  - `open()` / `close()` and context manager support.

- High-level display
  - `show_number(n: int, *, leading_zero: bool = False) -> None`  # 0..99, clamps outside
  - `show_string(s: str) -> None`  # 1–2 chars from supported font; unsupported chars become blanks
  - `show_digits(tens: int | None, ones: int | None, *, dp_tens: bool = False, dp_ones: bool = False) -> None`
    - Display per-digit value with optional decimal points; `None` renders blank for that digit.
  - `clear() -> None`  # both digits blank/off

- Per-segment/low-level
  - `set_segments(tens: int | None, ones: int | None) -> None`  # raw 8-bit patterns; None leaves unchanged
  - `encode_digit(ch: str, *, dp: bool = False) -> int`  # returns 8-bit pattern per font map
  - `set_raw_bytes(byte0: int, byte1: int) -> None`  # send bytes in configured order

- Animations (optional)
  - `count(start: int = 0, stop: int = 99, step: int = 1, delay_s: float = 0.1) -> None`
  - `blink(text: str, times: int = 3, on_s: float = 0.3, off_s: float = 0.3) -> None`

### Segment Mapping (to verify)
- We will define a segment map for a 7-seg digit with optional DP. Proposed bit layout (LSB on the right):
```
bit7 bit6 bit5 bit4 bit3 bit2 bit1 bit0
 DP    g    f    e    d    c    b    a
```
- Current `DigitList` suggests: `0 -> 0x7E` which sets segments a,b,c,d,e,f (and clears g, DP). We will build the font table to match your hardware (common anode/cathode affects bit polarity; confirm).

Initial font (to confirm polarity):
- Digits 0..9 from `DigitList` mapping.
- Symbols: `-` (only g), blank (0x00), letters {A,b,C,d,E,F,H,L,P,U} as feasible.

### Error Handling
- Validate ranges (digits 0..9), clamp number range to 0..99, and raise `ValueError` for invalid inputs or unsupported characters in strict modes.
- Hardware exceptions bubble up; document common SPI/GPIO issues.

### Testing/Examples
- Provide an interactive `__main__` menu similar to the bar graph module to exercise: number, string, per-segment, raw bytes, count animation, blink.

### Configuration Defaults (proposed)
- SPI: bus=0, device=0, mode=0
- GPIO: `P8_19`, `P8_14` set HIGH on init (until clarified)
- Byte order: `ones,tens`

### Implementation Plan (post-approval)
1) Implement `SevenSegment` with init/open/close and raw `set_raw_bytes` honoring `order`.
2) Port the digit font from `DigitList` into a named map, confirm polarity with you.
3) Implement `show_number`, `show_digits`, `show_string` with DP support.
4) Implement per-segment raw and animations.
5) Add interactive test harness in `__main__` and examples.

### Your Review
Please confirm:
- Common anode/cathode and segment polarity
- Exact DP usage and need per-digit DP
- Byte order `[ones, tens]` vs `[tens, ones]`
- Any additional symbols/behaviors you want (minus sign, blanks, letters)








