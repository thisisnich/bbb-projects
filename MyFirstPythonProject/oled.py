import time
from typing import Optional, List, Tuple
import math


class OledDisplay:
    """Driver for a 64x32 OLED display (SSD1306) controlled via I2C.

    Uses Adafruit SSD1306 library for display control and PIL for drawing.
    """
    
    def __init__(
        self,
        width: int = 64,
        height: int = 32,
        *,
        dc_pin: str = "P9_16",
        reset_pin: str = "P9_23",
        i2c_addr: int = 0x3C,
        lazy_hw: bool = False,
    ) -> None:
        """Initialize the OLED display.

        Args:
            width: Display width in pixels (default: 64)
            height: Display height in pixels (default: 32)
            dc_pin: Data/Command pin (default: P9_16)
            reset_pin: Reset pin (default: P9_23)
            i2c_addr: I2C address (default: 0x3C)
            lazy_hw: If True, don't initialize hardware until open() is called
        """
        self._width = width
        self._height = height
        self._dc_pin = dc_pin
        self._reset_pin = reset_pin
        self._i2c_addr = i2c_addr
        self._lazy_hw = lazy_hw
        
        self._display = None  # type: ignore[var-annotated]
        self._image = None  # type: ignore[var-annotated]
        self._draw = None  # type: ignore[var-annotated]
        self._font = None  # type: ignore[var-annotated]
        
        if not self._lazy_hw:
            self.open()
    
    def open(self) -> None:
        """Open the display connection and initialize."""
        if self._display is not None:
            return
        
        import board
        import busio
        import digitalio
        import adafruit_ssd1306
        from board import SCL, SDA
        from PIL import Image, ImageDraw, ImageFont
        
        # Setup pins
        Pin_DC = digitalio.DigitalInOut(getattr(board, self._dc_pin))
        Pin_DC.direction = digitalio.Direction.OUTPUT
        Pin_DC.value = False
        
        Pin_RESET = digitalio.DigitalInOut(getattr(board, self._reset_pin))
        Pin_RESET.direction = digitalio.Direction.OUTPUT
        Pin_RESET.value = True
        
        # Initialize I2C
        i2c = busio.I2C(SCL, SDA)
        
        # Initialize display
        self._display = adafruit_ssd1306.SSD1306_I2C(
            self._width, self._height, i2c, addr=self._i2c_addr
        )
        
        # Create image and drawing context
        self._image = Image.new("1", (self._width, self._height))
        self._draw = ImageDraw.Draw(self._image)
        self._font = ImageFont.load_default()
    
    def close(self) -> None:
        """Close the display connection."""
        self._display = None
        self._image = None
        self._draw = None
        self._font = None
    
    def __enter__(self) -> "OledDisplay":
        """Context manager entry."""
        if self._display is None:
            self.open()
        return self
    
    def __exit__(self, exc_type, exc, tb) -> None:
        """Context manager exit."""
        self.close()
    
    def clear(self) -> None:
        """Clear the display (all pixels off)."""
        if self._draw is None:
            self.open()
        self._draw.rectangle((0, 0, self._width - 1, self._height - 1), outline=0, fill=0)
        self.show()
    
    def fill(self) -> None:
        """Fill the display (all pixels on)."""
        if self._draw is None:
            self.open()
        self._draw.rectangle((0, 0, self._width - 1, self._height - 1), outline=1, fill=1)
        self.show()
    
    def show(self) -> None:
        """Update the display with current image."""
        if self._display is None:
            self.open()
        self._display.image(self._image)  # type: ignore[attr-defined]
        self._display.show()  # type: ignore[attr-defined]
    
    # ----------------------------- High-level Drawing APIs ----------------------------
    
    def draw_border(self, thickness: int = 1) -> None:
        """Draw a border around the display.

        Args:
            thickness: Border thickness in pixels
        """
        if self._draw is None:
            self.open()
        for i in range(thickness):
            self._draw.rectangle(
                (i, i, self._width - 1 - i, self._height - 1 - i),
                outline=1,
                fill=0
            )
        self.show()
    
    def draw_text(
        self,
        text: str,
        x: int = 0,
        y: int = 0,
        *,
        font=None,
        fill: int = 1,
    ) -> None:
        """Draw text on the display.

        Args:
            text: Text to display
            x: X position (left)
            y: Y position (top)
            font: Font to use (None = default)
            fill: Fill value (1 = white, 0 = black)
        """
        if self._draw is None:
            self.open()
        if font is None:
            font = self._font
        self._draw.text((x, y), text, font=font, fill=fill)
        self.show()
    
    def draw_centered_text(
        self,
        text: str,
        y: int = None,
        *,
        font=None,
        fill: int = 1,
    ) -> None:
        """Draw centered text on the display.

        Args:
            text: Text to display
            y: Y position (None = center vertically)
            font: Font to use (None = default)
            fill: Fill value (1 = white, 0 = black)
        """
        if self._draw is None:
            self.open()
        if font is None:
            font = self._font
        
        # Get text size
        bbox = self._draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Calculate positions
        x = (self._width - text_width) // 2
        if y is None:
            y = (self._height - text_height) // 2
        else:
            y = max(0, min(y, self._height - text_height))
        
        self._draw.text((x, y), text, font=font, fill=fill)
        self.show()
    
    def draw_rectangle(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        *,
        outline: int = 1,
        fill: int = 0,
    ) -> None:
        """Draw a rectangle.

        Args:
            x: Left position
            y: Top position
            width: Rectangle width
            height: Rectangle height
            outline: Outline color (1 = white, 0 = black)
            fill: Fill color (1 = white, 0 = black)
        """
        if self._draw is None:
            self.open()
        self._draw.rectangle(
            (x, y, x + width - 1, y + height - 1),
            outline=outline,
            fill=fill
        )
        self.show()
    
    def draw_circle(
        self,
        x: int,
        y: int,
        radius: int,
        *,
        outline: int = 1,
        fill: int = 0,
    ) -> None:
        """Draw a circle.

        Args:
            x: Center X position
            y: Center Y position
            radius: Circle radius
            outline: Outline color (1 = white, 0 = black)
            fill: Fill color (1 = white, 0 = black)
        """
        if self._draw is None:
            self.open()
        self._draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            outline=outline,
            fill=fill
        )
        self.show()
    
    def draw_line(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        *,
        fill: int = 1,
        width: int = 1,
    ) -> None:
        """Draw a line.

        Args:
            x1: Start X position
            y1: Start Y position
            x2: End X position
            y2: End Y position
            fill: Line color (1 = white, 0 = black)
            width: Line width
        """
        if self._draw is None:
            self.open()
        self._draw.line((x1, y1, x2, y2), fill=fill, width=width)
        self.show()
    
    # ----------------------------- Preset Functions ----------------------------
    
    def preset_welcome(self) -> None:
        """Display a welcome message with border."""
        self.clear()
        self.draw_border(1)
        self.draw_centered_text("Welcome", 8)
        self.draw_centered_text("to", 18)
        self.draw_centered_text("OLED!", 24)
    
    def preset_nyp(self) -> None:
        """Display 'I Love NYP' message (original code)."""
        self.clear()
        self.draw_border(1)
        self.draw_text("I Love NYP", 2, 10)
    
    def preset_hello_world(self) -> None:
        """Display 'Hello World'."""
        self.clear()
        self.draw_centered_text("Hello")
        self.draw_centered_text("World", 20)
    
    def preset_clock_face(self) -> None:
        """Draw a simple clock face."""
        self.clear()
        center_x = self._width // 2
        center_y = self._height // 2
        radius = min(self._width, self._height) // 2 - 2
        
        # Draw circle
        self.draw_circle(center_x, center_y, radius, outline=1, fill=0)
        
        # Draw hour markers
        for hour in range(12):
            angle = math.radians(hour * 30 - 90)
            x1 = center_x + int((radius - 2) * math.cos(angle))
            y1 = center_y + int((radius - 2) * math.sin(angle))
            x2 = center_x + int(radius * math.cos(angle))
            y2 = center_y + int(radius * math.sin(angle))
            self.draw_line(x1, y1, x2, y2, fill=1, width=1)
        
        # Draw hands (example: 3:00)
        self.draw_line(center_x, center_y, center_x + radius // 2, center_y, fill=1, width=2)
        self.draw_line(center_x, center_y, center_x, center_y - radius // 3, fill=1, width=1)
        self.show()
    
    def preset_progress_bar(self, percentage: float = 50.0) -> None:
        """Draw a progress bar.

        Args:
            percentage: Progress percentage (0-100)
        """
        self.clear()
        bar_width = self._width - 4
        bar_height = 6
        bar_x = 2
        bar_y = (self._height - bar_height) // 2
        
        # Draw border
        self.draw_rectangle(bar_x, bar_y, bar_width, bar_height, outline=1, fill=0)
        
        # Draw fill
        fill_width = int(bar_width * percentage / 100.0)
        if fill_width > 0:
            self.draw_rectangle(bar_x + 1, bar_y + 1, fill_width - 2, bar_height - 2, outline=1, fill=1)
        
        # Draw percentage text
        text = f"{int(percentage)}%"
        self.draw_centered_text(text, self._height - 10)
        self.show()
    
    def preset_battery(self, percentage: float = 75.0) -> None:
        """Draw a battery indicator.

        Args:
            percentage: Battery percentage (0-100)
        """
        self.clear()
        bat_width = 20
        bat_height = 10
        bat_x = (self._width - bat_width) // 2
        bat_y = (self._height - bat_height) // 2
        
        # Draw battery outline
        self.draw_rectangle(bat_x, bat_y, bat_width, bat_height, outline=1, fill=0)
        # Draw battery terminal
        self.draw_rectangle(bat_x + bat_width, bat_y + 2, 2, 6, outline=1, fill=1)
        
        # Draw battery level
        fill_width = int((bat_width - 2) * percentage / 100.0)
        if fill_width > 0:
            self.draw_rectangle(bat_x + 1, bat_y + 1, fill_width, bat_height - 2, outline=1, fill=1)
        
        # Draw percentage
        text = f"{int(percentage)}%"
        self.draw_centered_text(text, bat_y + bat_height + 2)
        self.show()
    
    # ----------------------------- Animations --------------------------------
    
    def animate_scroll_text(
        self,
        text: str,
        delay_s: float = 0.1,
        direction: str = "left",
        cycles: Optional[int] = None,
    ) -> None:
        """Scroll text horizontally.

        Args:
            text: Text to scroll
            delay_s: Delay between frames in seconds
            direction: "left" or "right"
            cycles: Number of cycles (None = infinite)
        """
        if self._draw is None:
            self.open()
        
        # Get text width
        bbox = self._draw.textbbox((0, 0), text, font=self._font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        y_pos = (self._height - text_height) // 2
        
        loops = 0
        while cycles is None or loops < cycles:
            if direction == "left":
                for x in range(self._width + text_width, -text_width, -2):
                    self.clear()
                    self._draw.text((x, y_pos), text, font=self._font, fill=1)
                    self.show()
                    time.sleep(delay_s)
            else:  # right
                for x in range(-text_width, self._width + text_width, 2):
                    self.clear()
                    self._draw.text((x, y_pos), text, font=self._font, fill=1)
                    self.show()
                    time.sleep(delay_s)
            loops += 1
    
    def animate_bouncing_ball(
        self,
        delay_s: float = 0.05,
        cycles: Optional[int] = None,
    ) -> None:
        """Animate a bouncing ball.

        Args:
            delay_s: Delay between frames in seconds
            cycles: Number of cycles (None = infinite)
        """
        radius = 3
        x = self._width // 2
        y = self._height // 2
        vx = 2
        vy = 1
        
        loops = 0
        while cycles is None or loops < cycles:
            # Update position
            x += vx
            y += vy
            
            # Bounce off walls
            if x <= radius or x >= self._width - radius:
                vx = -vx
                x = max(radius, min(self._width - radius, x))
            if y <= radius or y >= self._height - radius:
                vy = -vy
                y = max(radius, min(self._height - radius, y))
            
            # Draw
            self.clear()
            self.draw_circle(x, y, radius, outline=1, fill=1)
            time.sleep(delay_s)
            loops += 1
    
    def animate_progress(
        self,
        delay_s: float = 0.1,
        cycles: Optional[int] = None,
    ) -> None:
        """Animate a progress bar filling up.

        Args:
            delay_s: Delay between updates in seconds
            cycles: Number of cycles (None = infinite)
        """
        loops = 0
        while cycles is None or loops < cycles:
            for pct in range(0, 101, 5):
                self.preset_progress_bar(float(pct))
                time.sleep(delay_s)
            loops += 1
    
    def animate_pulse(
        self,
        delay_s: float = 0.1,
        cycles: Optional[int] = None,
    ) -> None:
        """Animate a pulsing circle.

        Args:
            delay_s: Delay between frames in seconds
            cycles: Number of cycles (None = infinite)
        """
        center_x = self._width // 2
        center_y = self._height // 2
        max_radius = min(self._width, self._height) // 2 - 1
        
        loops = 0
        while cycles is None or loops < cycles:
            # Grow
            for r in range(1, max_radius + 1):
                self.clear()
                self.draw_circle(center_x, center_y, r, outline=1, fill=0)
                time.sleep(delay_s)
            # Shrink
            for r in range(max_radius, 0, -1):
                self.clear()
                self.draw_circle(center_x, center_y, r, outline=1, fill=0)
                time.sleep(delay_s)
            loops += 1
    
    def animate_wave(
        self,
        delay_s: float = 0.05,
        cycles: Optional[int] = None,
    ) -> None:
        """Animate a sine wave.

        Args:
            delay_s: Delay between frames in seconds
            cycles: Number of cycles (None = infinite)
        """
        amplitude = self._height // 2 - 2
        frequency = 2
        phase = 0
        
        loop_count = 0
        while cycles is None or loop_count < cycles:
            self.clear()
            prev_y = None
            for x in range(self._width):
                y = int(self._height // 2 + amplitude * math.sin(2 * math.pi * frequency * x / self._width + phase))
                if prev_y is not None:
                    self.draw_line(x - 1, prev_y, x, y, fill=1, width=1)
                prev_y = y
            self.show()
            time.sleep(delay_s)
            phase += 0.1
            loop_count += 1
    
    def animate_marquee(
        self,
        texts: List[str],
        delay_s: float = 1.0,
        cycles: Optional[int] = None,
    ) -> None:
        """Cycle through multiple texts.

        Args:
            texts: List of text strings to display
            delay_s: Delay between texts in seconds
            cycles: Number of cycles (None = infinite)
        """
        loops = 0
        while cycles is None or loops < cycles:
            for text in texts:
                self.clear()
                self.draw_centered_text(text)
                time.sleep(delay_s)
            loops += 1


def _print_menu() -> None:
    """Print the test menu."""
    print("\nOLED Display test menu:")
    print("  1) clear")
    print("  2) fill")
    print("  3) draw_border [thickness]")
    print("  4) draw_text <text> [x] [y]")
    print("  5) draw_centered_text <text> [y]")
    print("  6) draw_rectangle <x> <y> <width> <height> [outline] [fill]")
    print("  7) draw_circle <x> <y> <radius> [outline] [fill]")
    print("  8) draw_line <x1> <y1> <x2> <y2> [width]")
    print("  9) preset_welcome")
    print(" 10) preset_nyp")
    print(" 11) preset_hello_world")
    print(" 12) preset_clock_face")
    print(" 13) preset_progress_bar [percentage]")
    print(" 14) preset_battery [percentage]")
    print(" 15) animate_scroll_text <text> [delay_s] [left|right] [cycles]")
    print(" 16) animate_bouncing_ball [delay_s] [cycles]")
    print(" 17) animate_progress [delay_s] [cycles]")
    print(" 18) animate_pulse [delay_s] [cycles]")
    print(" 19) animate_wave [delay_s] [cycles]")
    print(" 20) animate_marquee <text1,text2,...> [delay_s] [cycles]")
    print("  q) quit")


def _parse_int(s: str) -> int:
    """Parse an integer (decimal or hex)."""
    s = s.strip()
    return int(s, 16) if s.lower().startswith("0x") else int(s)


if __name__ == "__main__":
    oled = OledDisplay()
    try:
        while True:
            _print_menu()
            line = input("\n> ").strip()
            if not line:
                continue
            if line.lower() in {"q", "quit", "exit"}:
                break
            
            parts = [p.strip() for p in line.split()]
            cmd = parts[0]
            
            try:
                if cmd == "1":
                    oled.clear()
                    print("Display cleared")
                    
                elif cmd == "2":
                    oled.fill()
                    print("Display filled")
                    
                elif cmd == "3":
                    thickness = int(parts[1]) if len(parts) > 1 else 1
                    oled.draw_border(thickness)
                    print(f"Border drawn (thickness={thickness})")
                    
                elif cmd == "4":
                    if len(parts) < 2:
                        print("usage: 4 <text> [x] [y]")
                        continue
                    text = parts[1]
                    x = int(parts[2]) if len(parts) > 2 else 0
                    y = int(parts[3]) if len(parts) > 3 else 0
                    oled.draw_text(text, x, y)
                    print(f"Text drawn: '{text}' at ({x}, {y})")
                    
                elif cmd == "5":
                    if len(parts) < 2:
                        print("usage: 5 <text> [y]")
                        continue
                    text = parts[1]
                    y = int(parts[2]) if len(parts) > 2 else None
                    oled.draw_centered_text(text, y)
                    print(f"Centered text drawn: '{text}'")
                    
                elif cmd == "6":
                    if len(parts) < 5:
                        print("usage: 6 <x> <y> <width> <height> [outline] [fill]")
                        continue
                    x = int(parts[1])
                    y = int(parts[2])
                    w = int(parts[3])
                    h = int(parts[4])
                    outline = int(parts[5]) if len(parts) > 5 else 1
                    fill = int(parts[6]) if len(parts) > 6 else 0
                    oled.draw_rectangle(x, y, w, h, outline=outline, fill=fill)
                    print(f"Rectangle drawn at ({x}, {y}), size {w}x{h}")
                    
                elif cmd == "7":
                    if len(parts) < 4:
                        print("usage: 7 <x> <y> <radius> [outline] [fill]")
                        continue
                    x = int(parts[1])
                    y = int(parts[2])
                    r = int(parts[3])
                    outline = int(parts[4]) if len(parts) > 4 else 1
                    fill = int(parts[5]) if len(parts) > 5 else 0
                    oled.draw_circle(x, y, r, outline=outline, fill=fill)
                    print(f"Circle drawn at ({x}, {y}), radius={r}")
                    
                elif cmd == "8":
                    if len(parts) < 5:
                        print("usage: 8 <x1> <y1> <x2> <y2> [width]")
                        continue
                    x1 = int(parts[1])
                    y1 = int(parts[2])
                    x2 = int(parts[3])
                    y2 = int(parts[4])
                    width = int(parts[5]) if len(parts) > 5 else 1
                    oled.draw_line(x1, y1, x2, y2, width=width)
                    print(f"Line drawn from ({x1}, {y1}) to ({x2}, {y2})")
                    
                elif cmd == "9":
                    oled.preset_welcome()
                    print("Welcome preset displayed")
                    
                elif cmd == "10":
                    oled.preset_nyp()
                    print("NYP preset displayed")
                    
                elif cmd == "11":
                    oled.preset_hello_world()
                    print("Hello World preset displayed")
                    
                elif cmd == "12":
                    oled.preset_clock_face()
                    print("Clock face preset displayed")
                    
                elif cmd == "13":
                    percentage = float(parts[1]) if len(parts) > 1 else 50.0
                    oled.preset_progress_bar(percentage)
                    print(f"Progress bar displayed ({percentage}%)")
                    
                elif cmd == "14":
                    percentage = float(parts[1]) if len(parts) > 1 else 75.0
                    oled.preset_battery(percentage)
                    print(f"Battery indicator displayed ({percentage}%)")
                    
                elif cmd == "15":
                    if len(parts) < 2:
                        print("usage: 15 <text> [delay_s] [left|right] [cycles]")
                        continue
                    text = parts[1]
                    delay = float(parts[2]) if len(parts) > 2 else 0.1
                    direction = parts[3] if len(parts) > 3 and parts[3] in ("left", "right") else "left"
                    if len(parts) > 3 and parts[3] in ("left", "right"):
                        cycles = int(parts[4]) if len(parts) > 4 else None
                    else:
                        cycles = int(parts[3]) if len(parts) > 3 else None
                    print(f"Scrolling text '{text}' {direction}...")
                    oled.animate_scroll_text(text, delay, direction, cycles)
                    
                elif cmd == "16":
                    delay = float(parts[1]) if len(parts) > 1 else 0.05
                    cycles = int(parts[2]) if len(parts) > 2 else None
                    print(f"Bouncing ball animation (delay={delay}s, cycles={cycles or 'infinite'})...")
                    oled.animate_bouncing_ball(delay, cycles)
                    
                elif cmd == "17":
                    delay = float(parts[1]) if len(parts) > 1 else 0.1
                    cycles = int(parts[2]) if len(parts) > 2 else None
                    print(f"Progress animation (delay={delay}s, cycles={cycles or 'infinite'})...")
                    oled.animate_progress(delay, cycles)
                    
                elif cmd == "18":
                    delay = float(parts[1]) if len(parts) > 1 else 0.1
                    cycles = int(parts[2]) if len(parts) > 2 else None
                    print(f"Pulse animation (delay={delay}s, cycles={cycles or 'infinite'})...")
                    oled.animate_pulse(delay, cycles)
                    
                elif cmd == "19":
                    delay = float(parts[1]) if len(parts) > 1 else 0.05
                    cycles = int(parts[2]) if len(parts) > 2 else None
                    print(f"Wave animation (delay={delay}s, cycles={cycles or 'infinite'})...")
                    oled.animate_wave(delay, cycles)
                    
                elif cmd == "20":
                    if len(parts) < 2:
                        print("usage: 20 <text1,text2,...> [delay_s] [cycles]")
                        continue
                    texts = [t.strip() for t in parts[1].split(',')]
                    delay = float(parts[2]) if len(parts) > 2 else 1.0
                    cycles = int(parts[3]) if len(parts) > 3 else None
                    print(f"Marquee animation with {len(texts)} texts...")
                    oled.animate_marquee(texts, delay, cycles)
                    
                else:
                    print("unknown command")
                    
            except Exception as e:
                print(f"error: {e}")
                
    finally:
        oled.close()
        print("\nDisplay closed")


# ============================================================================
# ORIGINAL CODE (commented for reference)
# ============================================================================
# import board
# import busio
# import digitalio
# import adafruit_ssd1306
# from board import SCL, SDA
# from PIL import Image, ImageDraw, ImageFont
#
# def OLEDClickInit():
#     Pin_DC = digitalio.DigitalInOut(board.P9_16)
#     Pin_DC.direction = digitalio.Direction.OUTPUT
#     Pin_DC.value = False
#     Pin_RESET = digitalio.DigitalInOut(board.P9_23)
#     Pin_RESET.direction = digitalio.Direction.OUTPUT
#     Pin_RESET.value = True
#     L_I2c = busio.I2C(SCL, SDA)
#     return L_I2c
#     
# G_I2c = OLEDClickInit()
# Display = adafruit_ssd1306.SSD1306_I2C(64, 32, G_I2c, addr=0x3C)
# ImageObj = Image.new("1", (Display.width, Display.height))
#
# Draw = ImageDraw.Draw(ImageObj)
# Draw.rectangle((0, 0, Display.width - 1, Display.height - 1), outline=1, fill=0)
#
# Font = ImageFont.load_default()
# Text = "I Love NYP"
# Draw.text((2, 10), Text, font=Font, fill=1)
#
# Display.image(ImageObj)
# Display.show()
