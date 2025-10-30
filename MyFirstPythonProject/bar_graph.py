import time
from typing import Optional, Tuple, Dict, List
try:
    from typing import Literal  # type: ignore[attr-defined]
except Exception:  # Python < 3.8 fallback
    from typing_extensions import Literal  # type: ignore


Color = Literal["off", "green", "red", "amber"]


class BarGraph:
    """Driver for a 10-segment bi-color bar graph controlled via SPI.

    Mapping (LSB on the right):
    - B2 bits 0..7  -> Green segments 1..8 (right to left)
    - B1 bits 6..7  -> Green segments 9..10
    - B1 bits 0..5  -> Red segments 1..6
    - B0 bits 0..3  -> Red segments 7..10

    Segment indexing is 1..10 from right to left. If both green and red of a
    segment are on, the color appears amber.
    """

    def __init__(
        self,
        bus: int = 1,
        device: int = 0,
        *,
        mode: int = 0,
        pin_a: str = "P9_14",
        pin_b: str = "P9_12",
        reverse: bool = False,
        lazy_hw: bool = False,
    ) -> None:
        self._bus = bus
        self._device = device
        self._mode = mode
        self._pin_a = pin_a
        self._pin_b = pin_b
        self._reverse = reverse
        self._lazy_hw = lazy_hw

        self._spi = None  # type: ignore[var-annotated]
        self._GPIO = None  # type: ignore[var-annotated]

        # Track current masks for idempotent updates and partial set operations
        self._green_mask_10 = 0
        self._red_mask_10 = 0

        if not self._lazy_hw:
            self.open()

    def open(self) -> None:
        if self._spi is not None:
            return
        from Adafruit_BBIO.SPI import SPI  # type: ignore
        import Adafruit_BBIO.GPIO as GPIO  # type: ignore

        self._GPIO = GPIO
        GPIO.setup(self._pin_a, GPIO.OUT)
        GPIO.setup(self._pin_b, GPIO.OUT)
        GPIO.output(self._pin_a, GPIO.HIGH)
        GPIO.output(self._pin_b, GPIO.HIGH)

        spi = SPI(self._bus, self._device)
        spi.mode = self._mode
        self._spi = spi

    def close(self) -> None:
        if self._spi is not None:
            try:
                self._spi.close()
            finally:
                self._spi = None

    def __enter__(self) -> "BarGraph":
        if self._spi is None:
            self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    # ----------------------------- High-level APIs ----------------------------
    def clear(self) -> None:
        self.set_color_mask(0, 0)

    def fill(self) -> None:
        self.set_color_mask((1 << 10) - 1, (1 << 10) - 1)

    def set_bars(self, count: int) -> None:
        """Set 0..10 bars using the G/A/R policy: 1-4 G, 5-8 Amber, 9-10 Red.
        """
        if count < 0 or count > 10:
            raise ValueError("count must be between 0 and 10 inclusive")

        green_mask = 0
        red_mask = 0
        # Positions are 1..10 from right to left
        for seg in range(1, count + 1):
            if seg <= 4:
                green_mask |= 1 << (seg - 1)
            elif seg <= 8:
                green_mask |= 1 << (seg - 1)
                red_mask |= 1 << (seg - 1)
            else:
                red_mask |= 1 << (seg - 1)

        self.set_color_mask(green_mask, red_mask)

    def set_percentage(
        self,
        pct: float,
        *,
        rounding: Literal["floor", "nearest", "ceil"] = "nearest",
    ) -> int:
        if pct < 0:
            pct = 0
        if pct > 100:
            pct = 100
        raw = pct * 10.0 / 100.0
        if rounding == "floor":
            count = int(raw // 1)
        elif rounding == "ceil":
            count = int(-(-raw // 1))
        else:
            count = int(round(raw))
        if count > 10:
            count = 10
        self.set_bars(count)
        return count

    def set_segments(
        self,
        colors: Dict[int, Color],
        *,
        clear_others: bool = False,
    ) -> None:
        """Set arbitrary per-segment colors. Keys are 1..10 (right to left).

        If clear_others is True, unspecified segments are turned off.
        """
        if clear_others:
            green_mask = 0
            red_mask = 0
        else:
            green_mask = self._green_mask_10
            red_mask = self._red_mask_10

        for seg, color in colors.items():
            if seg < 1 or seg > 10:
                raise ValueError("segment index must be in 1..10")
            bit = 1 << (seg - 1)
            if color == "off":
                green_mask &= ~bit
                red_mask &= ~bit
            elif color == "green":
                green_mask |= bit
                red_mask &= ~bit
            elif color == "red":
                green_mask &= ~bit
                red_mask |= bit
            elif color == "amber":
                green_mask |= bit
                red_mask |= bit
            else:
                raise ValueError("unknown color")

        self.set_color_mask(green_mask, red_mask)

    def set_row(self, colors: List[Color]) -> None:
        if len(colors) != 10:
            raise ValueError("colors must have length 10")
        b0, b1, b2, gmask, rmask = self.encode_colors(colors)
        self._green_mask_10 = gmask
        self._red_mask_10 = rmask
        self._write3(b0, b1, b2)

    # ----------------------------- Low-level APIs ----------------------------
    def set_mask(self, b0: int, b1: int, b2: int) -> None:
        self._write3(b0, b1, b2)

    def get_mask_for_bars(self, count: int) -> Tuple[int, int, int]:
        # Backward-compat mapping identical to bar.py ramp (greens first)
        if count < 0 or count > 10:
            raise ValueError("count must be between 0 and 10 inclusive")
        mapping = {
            0: (0x00, 0x00, 0x00),
            1: (0x00, 0x00, 0x01),
            2: (0x00, 0x00, 0x03),
            3: (0x00, 0x00, 0x07),
            4: (0x00, 0x00, 0x0F),
            5: (0x00, 0x40, 0x1F),
            6: (0x00, 0xC0, 0x3F),
            7: (0x01, 0xC0, 0x7F),
            8: (0x03, 0xC0, 0xFF),
            9: (0x07, 0xC0, 0xFF),
            10: (0x0F, 0xC0, 0xFF),
        }
        return mapping[count]

    def set_color_mask(self, green_mask: int, red_mask: int) -> None:
        """Apply two 10-bit masks (segments 1..10, right→left) to colors.
        """
        if green_mask < 0 or red_mask < 0:
            raise ValueError("masks must be non-negative")
        green_mask &= (1 << 10) - 1
        red_mask &= (1 << 10) - 1

        if self._reverse:
            green_mask = self._reverse_mask_10(green_mask)
            red_mask = self._reverse_mask_10(red_mask)

        b0, b1, b2 = self._encode_masks(green_mask, red_mask)
        self._green_mask_10 = green_mask
        self._red_mask_10 = red_mask
        self._write3(b0, b1, b2)

    def encode_colors(
        self, colors: List[Color]
    ) -> Tuple[int, int, int, int, int]:
        """Pure encoder from a 10-length color list to (b0,b1,b2, gmask, rmask)."""
        if len(colors) != 10:
            raise ValueError("colors must have length 10")
        gmask = 0
        rmask = 0
        for i, c in enumerate(colors, start=1):
            bit = 1 << (i - 1)
            if c == "green":
                gmask |= bit
            elif c == "red":
                rmask |= bit
            elif c == "amber":
                gmask |= bit
                rmask |= bit
        if self._reverse:
            gmask = self._reverse_mask_10(gmask)
            rmask = self._reverse_mask_10(rmask)
        b0, b1, b2 = self._encode_masks(gmask, rmask)
        return b0, b1, b2, gmask, rmask

    # ------------------------------ Animations -------------------------------
    def animate_sweep(self, delay_s: float = 0.1, cycles: Optional[int] = None) -> None:
        loops = 0
        while cycles is None or loops < cycles:
            for i in range(0, 11):
                self.set_bars(i)
                time.sleep(delay_s)
            loops += 1

    def animate_bounce(self, delay_s: float = 0.1, cycles: Optional[int] = None) -> None:
        loops = 0
        while cycles is None or loops < cycles:
            for i in range(0, 10):
                self.set_bars(i)
                time.sleep(delay_s)
            for i in range(10, -1, -1):
                self.set_bars(i)
                time.sleep(delay_s)
            loops += 1

    # ------------------------------- Internals -------------------------------
    def _reverse_mask_10(self, mask: int) -> int:
        rev = 0
        for i in range(10):
            if mask & (1 << i):
                rev |= 1 << (9 - i)
        return rev

    def _encode_masks(self, gmask: int, rmask: int) -> Tuple[int, int, int]:
        # B2: g[1..8] => bits 0..7
        b2 = gmask & 0xFF
        # B1: r[1..6] => bits 2..7; g[9..10] => bits 0..1
        b1_red = (rmask & 0x3F) << 2
        b1_green = (gmask >> 8) & 0x03
        b1 = (b1_red | b1_green) & 0xFF
        # B0: r[7..10] => bits 0..3; upper nibble unused
        b0 = (rmask >> 6) & 0x0F
        return b0, b1, b2

    def _write3(self, b0: int, b1: int, b2: int) -> None:
        if self._spi is None:
            self.open()
        # Clamp to bytes
        b0 &= 0xFF
        b1 &= 0xFF
        b2 &= 0xFF
        self._spi.writebytes([b0, b1, b2])  # type: ignore[attr-defined]



def _print_menu() -> None:
    print("BarGraph test menu:")
    print("  1) clear")
    print("  2) fill")
    print("  3) set_bars <0-10>")
    print("  4) set_percentage <0-100> [floor|nearest|ceil]")
    print("  5) set_segments (example: 1=green,5=amber,10=red) [clear]")
    print("  6) set_color_mask <green_mask_10> <red_mask_10>  (decimal or 0x..)")
    print("  7) set_mask <b0> <b1> <b2>  (decimal or 0x..)")
    print("  8) get_mask_for_bars <0-10>")
    print("  9) encode_colors <10 chars of g/r/a/x> (right→left)")
    print(" 10) animate_sweep [delay_s] [cycles]")
    print(" 11) animate_bounce [delay_s] [cycles]")
    print("  q) quit")


def _parse_int(s: str) -> int:
    s = s.strip()
    return int(s, 16) if s.lower().startswith("0x") else int(s)


if __name__ == "__main__":
    bg = BarGraph()
    try:
        while True:
            _print_menu()
            line = input("> ").strip()
            if not line:
                continue
            if line.lower() in {"q", "quit", "exit"}:
                break
            parts = [p.strip() for p in line.split()]
            cmd = parts[0]
            try:
                if cmd == "1":
                    bg.clear()
                elif cmd == "2":
                    bg.fill()
                elif cmd == "3":
                    if len(parts) < 2:
                        print("usage: 3 <0-10>")
                        continue
                    bg.set_bars(int(parts[1]))
                elif cmd == "4":
                    if len(parts) < 2:
                        print("usage: 4 <0-100> [floor|nearest|ceil]")
                        continue
                    rounding = parts[2] if len(parts) > 2 else "nearest"
                    used = bg.set_percentage(float(parts[1]), rounding=rounding)  # type: ignore[arg-type]
                    print(f"bars used: {used}")
                elif cmd == "5":
                    # Example: 1=green,5=amber,10=red [clear]
                    if len(parts) < 2:
                        print("usage: 5 seg=color[,seg=color...] [clear]")
                        continue
                    clear_others = any(p.lower() == "clear" for p in parts[2:])
                    seg_map: Dict[int, Color] = {}
                    for item in parts[1].split(','):
                        if not item:
                            continue
                        seg_s, color = item.split('=')
                        seg = int(seg_s)
                        color_l = color.lower()
                        if color_l not in ("off", "green", "red", "amber"):
                            print("color must be off|green|red|amber")
                            seg_map = {}
                            break
                        seg_map[seg] = color_l  # type: ignore[assignment]
                    if seg_map:
                        bg.set_segments(seg_map, clear_others=clear_others)
                elif cmd == "6":
                    if len(parts) < 3:
                        print("usage: 6 <green_mask_10> <red_mask_10>")
                        continue
                    gm = _parse_int(parts[1])
                    rm = _parse_int(parts[2])
                    bg.set_color_mask(gm, rm)
                elif cmd == "7":
                    if len(parts) < 4:
                        print("usage: 7 <b0> <b1> <b2>")
                        continue
                    b0 = _parse_int(parts[1])
                    b1 = _parse_int(parts[2])
                    b2 = _parse_int(parts[3])
                    bg.set_mask(b0, b1, b2)
                elif cmd == "8":
                    if len(parts) < 2:
                        print("usage: 8 <0-10>")
                        continue
                    b0, b1, b2 = bg.get_mask_for_bars(int(parts[1]))
                    print(f"b0=0x{b0:02X} b1=0x{b1:02X} b2=0x{b2:02X}")
                elif cmd == "9":
                    if len(parts) < 2:
                        print("usage: 9 <10 chars of g/r/a/x>")
                        continue
                    s = parts[1].strip()
                    if len(s) != 10 or any(c.lower() not in "grax" for c in s):
                        print("must be 10 chars using g,r,a,x")
                        continue
                    colors: List[Color] = []
                    for c in s:
                        if c.lower() == 'g':
                            colors.append("green")
                        elif c.lower() == 'r':
                            colors.append("red")
                        elif c.lower() == 'a':
                            colors.append("amber")
                        else:
                            colors.append("off")
                    b0, b1, b2, gm, rm = bg.encode_colors(colors)
                    print(f"b0=0x{b0:02X} b1=0x{b1:02X} b2=0x{b2:02X}  gm=0x{gm:03X} rm=0x{rm:03X}")
                    bg.set_mask(b0, b1, b2)
                elif cmd == "10":
                    delay = float(parts[1]) if len(parts) > 1 else 0.1
                    cycles = int(parts[2]) if len(parts) > 2 else None
                    bg.animate_sweep(delay, cycles)
                elif cmd == "11":
                    delay = float(parts[1]) if len(parts) > 1 else 0.1
                    cycles = int(parts[2]) if len(parts) > 2 else None
                    bg.animate_bounce(delay, cycles)
                else:
                    print("unknown command")
            except Exception as e:
                print(f"error: {e}")
    finally:
        bg.close()
