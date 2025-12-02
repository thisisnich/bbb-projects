"""
Simple OLED Display Driver (SSD1306) - No QR Code Version

Uses direct I2C communication via smbus instead of CircuitPython libraries.
This avoids any potential QR code watermarks from CircuitPython/Adafruit libraries.
"""
import time
from typing import Optional
import math

try:
    import smbus2
    SMBUS_AVAILABLE = True
except ImportError:
    SMBUS_AVAILABLE = False
    smbus2 = None

# Alternative: Direct I2C file access (fallback if smbus2 has issues)
try:
    import struct
    import fcntl
    I2C_SLAVE = 0x0703
    DIRECT_I2C_AVAILABLE = True
except:
    DIRECT_I2C_AVAILABLE = False
    I2C_SLAVE = None

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None
    ImageDraw = None
    ImageFont = None

# SSD1306 I2C Address
SSD1306_I2C_ADDRESS = 0x3C

# SSD1306 Command Set
SSD1306_SETCONTRAST = 0x81
SSD1306_DISPLAYALLON_RESUME = 0xA4
SSD1306_DISPLAYALLON = 0xA5
SSD1306_NORMALDISPLAY = 0xA6
SSD1306_INVERTDISPLAY = 0xA7
SSD1306_DISPLAYOFF = 0xAE
SSD1306_DISPLAYON = 0xAF
SSD1306_SETDISPLAYOFFSET = 0xD3
SSD1306_SETCOMPINS = 0xDA
SSD1306_SETVCOMDETECT = 0xDB
SSD1306_SETDISPLAYCLOCKDIV = 0xD5
SSD1306_SETPRECHARGE = 0xD9
SSD1306_SETMULTIPLEX = 0xA8
SSD1306_SETLOWCOLUMN = 0x00
SSD1306_SETHIGHCOLUMN = 0x10
SSD1306_SETSTARTLINE = 0x40
SSD1306_MEMORYMODE = 0x20
SSD1306_COLUMNADDR = 0x21
SSD1306_PAGEADDR = 0x22
SSD1306_COMSCANINC = 0xC0
SSD1306_COMSCANDEC = 0xC8
SSD1306_SEGREMAP = 0xA0
SSD1306_CHARGEPUMP = 0x8D
SSD1306_EXTERNALVCC = 0x1
SSD1306_SWITCHCAPVCC = 0x2

# Scrolling constants
SSD1306_ACTIVATE_SCROLL = 0x2F
SSD1306_DEACTIVATE_SCROLL = 0x2E
SSD1306_SET_VERTICAL_SCROLL_AREA = 0xA3
SSD1306_RIGHT_HORIZONTAL_SCROLL = 0x26
SSD1306_LEFT_HORIZONTAL_SCROLL = 0x27
SSD1306_VERTICAL_AND_RIGHT_HORIZONTAL_SCROLL = 0x29
SSD1306_VERTICAL_AND_LEFT_HORIZONTAL_SCROLL = 0x2A


class OledDisplay:
    """Driver for a 64x32 OLED display (SSD1306) controlled via I2C.
    
    Uses direct I2C communication (smbus) instead of CircuitPython libraries.
    This version does not include any QR code watermarks.
    """
    
    def __init__(
        self,
        width: int = 64,
        height: int = 32,
        *,
        dc_pin: str = "P9_16",
        reset_pin: str = "P9_23",
        i2c_addr: int = 0x3C,
        i2c_bus: int = 1,  # I2C bus number (usually 1 for BBBW)
        lazy_hw: bool = False,
    ) -> None:
        """Initialize the OLED display.

        Args:
            width: Display width in pixels (default: 64)
            height: Display height in pixels (default: 32)
            dc_pin: Data/Command pin (not used in I2C mode, kept for compatibility)
            reset_pin: Reset pin (not used in I2C mode, kept for compatibility)
            i2c_addr: I2C address (default: 0x3C)
            i2c_bus: I2C bus number (default: 1 for BBBW)
            lazy_hw: If True, don't initialize hardware until open() is called
        """
        self._width = width
        self._height = height
        self._dc_pin = dc_pin
        self._reset_pin = reset_pin
        self._i2c_addr = i2c_addr
        self._i2c_bus = i2c_bus
        self._lazy_hw = lazy_hw
        
        self._bus = None
        self._i2c_file = None  # Direct file handle for I2C (fallback)
        self._use_direct_i2c = False  # Flag to use direct I2C instead of smbus2
        self._image = None
        self._draw = None
        self._font = None
        
        if not self._lazy_hw:
            self.open()
    
    def open(self) -> None:
        """Open the display connection and initialize."""
        if self._bus is not None:
            return
        
        if not SMBUS_AVAILABLE:
            raise ImportError("smbus2 library not available. Install with: pip install smbus2")
        
        if not PIL_AVAILABLE:
            raise ImportError("PIL/Pillow library not available. Install with: pip install Pillow")
        
        # Try to release any existing I2C locks first
        # This helps if CircuitPython or another process left the bus locked
        try:
            import subprocess
            import os
            # Check if I2C device exists
            i2c_dev = f"/dev/i2c-{self._i2c_bus}"
            if os.path.exists(i2c_dev):
                # Try multiple methods to release the lock
                # Method 1: Try to open and immediately close the device file directly
                try:
                    fd = os.open(i2c_dev, os.O_RDWR)
                    os.close(fd)
                    time.sleep(0.2)  # Small delay
                except:
                    pass  # Ignore errors during cleanup attempt
                
                # Method 2: Try smbus2 open/close
                try:
                    test_bus = smbus2.SMBus(self._i2c_bus)
                    test_bus.close()
                    time.sleep(0.2)  # Small delay
                except:
                    pass  # Ignore errors during cleanup attempt
        except:
            pass  # Ignore if cleanup attempt fails
        
        # Initialize I2C bus with retry logic
        max_retries = 5
        retry_delay = 0.5
        
        for attempt in range(max_retries):
            try:
                self._bus = smbus2.SMBus(self._i2c_bus)
                # Test if we can actually write (quick test)
                try:
                    # Try a simple read to verify bus is accessible
                    # This will fail if bus is truly locked, but succeed if just opened
                    self._bus.read_byte(self._i2c_addr)
                except:
                    # Read might fail, but that's okay - we just want to test if bus is accessible
                    pass
                break  # Success, exit retry loop
            except OSError as e:
                if e.errno == 16:  # Device or resource busy
                    if attempt < max_retries - 1:
                        print(f"[OLED] I2C bus busy, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                        # Try to force release on later attempts
                        if attempt >= 2:
                            try:
                                import subprocess
                                # Try to reset I2C bus (may require sudo)
                                subprocess.run(['i2cdetect', '-y', str(self._i2c_bus)], 
                                             capture_output=True, timeout=1)
                            except:
                                pass
                        time.sleep(retry_delay)
                        continue
                    else:
                        # Last attempt failed - try direct I2C file access as fallback
                        print(f"[OLED] smbus2 failed, trying direct I2C file access...")
                        try:
                            if DIRECT_I2C_AVAILABLE:
                                # Try to force release the bus first
                                import os
                                i2c_dev = f"/dev/i2c-{self._i2c_bus}"
                                for retry in range(3):
                                    try:
                                        # Try to open/close to release lock
                                        try:
                                            fd = os.open(i2c_dev, os.O_RDWR)
                                            os.close(fd)
                                            time.sleep(0.3)
                                        except:
                                            pass
                                        
                                        # Now try to open for I2C
                                        self._use_direct_i2c = True
                                        self._i2c_file = open(i2c_dev, 'r+b', buffering=0)
                                        fcntl.ioctl(self._i2c_file, I2C_SLAVE, self._i2c_addr)
                                        print(f"[OLED] Using direct I2C file access (fallback mode)")
                                        break  # Success with direct I2C
                                    except OSError as direct_e:
                                        if direct_e.errno == 16 and retry < 2:
                                            print(f"[OLED] Direct I2C also busy, retrying... ({retry + 1}/3)")
                                            time.sleep(0.5)
                                            continue
                                        raise
                            else:
                                raise RuntimeError("Direct I2C not available") from e
                        except Exception as direct_e:
                            raise RuntimeError(
                                f"I2C bus {self._i2c_bus} is busy after {max_retries} attempts. "
                                f"This usually means CircuitPython's busio.I2C left a kernel-level lock.\n"
                                f"  SOLUTIONS (try in order):\n"
                                f"    1. Run: python3 /var/lib/cloud9/MyFirstPythonProject/force_release_i2c.py\n"
                                f"    2. Kill Python: pkill -f python (wait 5 seconds)\n"
                                f"    3. Check I2C: sudo lsof /dev/i2c-{self._i2c_bus}\n"
                                f"    4. Reboot the BBBW (most reliable)"
                            ) from direct_e
                else:
                    raise RuntimeError(f"Failed to open I2C bus {self._i2c_bus}: {e}") from e
            except Exception as e:
                raise RuntimeError(f"Failed to open I2C bus {self._i2c_bus}: {e}") from e
        
        # Initialize display with retry logic
        try:
            self._init_display()
        except RuntimeError as e:
            # Close bus/file if init failed
            try:
                if self._use_direct_i2c and self._i2c_file:
                    self._i2c_file.close()
                elif self._bus:
                    self._bus.close()
            except:
                pass
            self._bus = None
            self._i2c_file = None
            self._use_direct_i2c = False
            raise
        
        # Create image and drawing context
        self._image = Image.new("1", (self._width, self._height))
        self._draw = ImageDraw.Draw(self._image)
        self._font = ImageFont.load_default()
    
    def _write_command(self, cmd: int) -> None:
        """Write a single command byte to the display."""
        try:
            if self._use_direct_i2c:
                # Direct I2C file access
                self._i2c_file.write(bytes([0x00, cmd]))  # Control byte 0x00 = command
            else:
                # smbus2 access
                self._bus.write_byte_data(self._i2c_addr, 0x00, cmd)
        except OSError as e:
            if e.errno == 16:  # Device or resource busy
                # Try to fallback to direct I2C if smbus2 fails
                if not self._use_direct_i2c and DIRECT_I2C_AVAILABLE:
                    print(f"[OLED] smbus2 write failed, switching to direct I2C...")
                    try:
                        # Close smbus2
                        try:
                            self._bus.close()
                        except:
                            pass
                        self._bus = None
                        
                        # Open direct I2C
                        self._use_direct_i2c = True
                        i2c_dev = f"/dev/i2c-{self._i2c_bus}"
                        self._i2c_file = open(i2c_dev, 'r+b', buffering=0)
                        fcntl.ioctl(self._i2c_file, I2C_SLAVE, self._i2c_addr)
                        print(f"[OLED] Switched to direct I2C file access")
                        
                        # Retry the write with direct I2C
                        self._i2c_file.write(bytes([0x00, cmd]))
                        return  # Success!
                    except Exception as direct_e:
                        raise RuntimeError(
                            f"I2C bus is busy while writing command 0x{cmd:02X}. "
                            f"Tried smbus2 and direct I2C, both failed. "
                            f"Another process (likely CircuitPython/oled.py) is using the OLED. "
                            f"SOLUTION: Kill Python processes: pkill -f python (wait 2-3 seconds), then try again."
                        ) from direct_e
                else:
                    raise RuntimeError(
                        f"I2C bus is busy while writing command 0x{cmd:02X}. "
                        f"Another process may be using the OLED display. "
                        f"Close other OLED instances first, or reset I2C: "
                        f"sudo modprobe -r i2c_dev && sudo modprobe i2c_dev"
                    ) from e
            else:
                raise RuntimeError(f"Failed to write command 0x{cmd:02X}: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to write command 0x{cmd:02X}: {e}") from e
    
    def _write_data(self, data: bytes) -> None:
        """Write data bytes to the display."""
        try:
            if self._use_direct_i2c:
                # Direct I2C file access - write in chunks
                chunk_size = 32
                for i in range(0, len(data), chunk_size):
                    chunk = data[i:i + chunk_size]
                    # Control byte 0x40 = data mode
                    self._i2c_file.write(bytes([0x40]) + chunk)
            else:
                # smbus2 access
                chunk_size = 32
                for i in range(0, len(data), chunk_size):
                    chunk = data[i:i + chunk_size]
                    self._bus.write_i2c_block_data(self._i2c_addr, 0x40, list(chunk))
        except OSError as e:
            if e.errno == 16:  # Device or resource busy
                # Try to fallback to direct I2C if smbus2 fails
                if not self._use_direct_i2c and DIRECT_I2C_AVAILABLE:
                    print(f"[OLED] smbus2 data write failed, switching to direct I2C...")
                    try:
                        # Close smbus2
                        try:
                            self._bus.close()
                        except:
                            pass
                        self._bus = None
                        
                        # Open direct I2C
                        self._use_direct_i2c = True
                        i2c_dev = f"/dev/i2c-{self._i2c_bus}"
                        self._i2c_file = open(i2c_dev, 'r+b', buffering=0)
                        fcntl.ioctl(self._i2c_file, I2C_SLAVE, self._i2c_addr)
                        print(f"[OLED] Switched to direct I2C file access")
                        
                        # Retry the write with direct I2C
                        chunk_size = 32
                        for i in range(0, len(data), chunk_size):
                            chunk = data[i:i + chunk_size]
                            self._i2c_file.write(bytes([0x40]) + chunk)
                        return  # Success!
                    except Exception as direct_e:
                        raise RuntimeError(
                            f"I2C bus is busy while writing data. "
                            f"Tried smbus2 and direct I2C, both failed. "
                            f"Another process (likely CircuitPython/oled.py) is using the OLED. "
                            f"SOLUTION: Kill Python processes: pkill -f python (wait 2-3 seconds), then try again."
                        ) from direct_e
                else:
                    raise RuntimeError(
                        f"I2C bus is busy while writing data. "
                        f"Another process may be using the OLED display. "
                        f"Close other OLED instances first, or reset I2C: "
                        f"sudo modprobe -r i2c_dev && sudo modprobe i2c_dev"
                    ) from e
            else:
                raise RuntimeError(f"Failed to write data: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to write data: {e}") from e
    
    def _init_display(self) -> None:
        """Initialize the SSD1306 display."""
        # Turn off display
        self._write_command(SSD1306_DISPLAYOFF)
        
        # Set display clock divide ratio and oscillator frequency
        self._write_command(SSD1306_SETDISPLAYCLOCKDIV)
        self._write_command(0x80)
        
        # Set multiplex ratio
        self._write_command(SSD1306_SETMULTIPLEX)
        self._write_command(self._height - 1)
        
        # Set display offset
        self._write_command(SSD1306_SETDISPLAYOFFSET)
        self._write_command(0x0)
        
        # Set start line
        self._write_command(SSD1306_SETSTARTLINE | 0x0)
        
        # Enable charge pump
        self._write_command(SSD1306_CHARGEPUMP)
        self._write_command(0x14)
        
        # Set memory addressing mode to horizontal
        self._write_command(SSD1306_MEMORYMODE)
        self._write_command(0x00)
        
        # Set segment re-map (A0 = column 0 mapped to SEG0)
        self._write_command(SSD1306_SEGREMAP | 0x1)
        
        # Set COM output scan direction (C8 = scan from COM[N-1] to COM0)
        self._write_command(SSD1306_COMSCANDEC)
        
        # Set COM pins configuration
        self._write_command(SSD1306_SETCOMPINS)
        if self._height == 32:
            self._write_command(0x02)
        else:
            self._write_command(0x12)
        
        # Set contrast
        self._write_command(SSD1306_SETCONTRAST)
        self._write_command(0x8F)
        
        # Set pre-charge period
        self._write_command(SSD1306_SETPRECHARGE)
        self._write_command(0xF1)
        
        # Set VCOMH deselect level
        self._write_command(SSD1306_SETVCOMDETECT)
        self._write_command(0x40)
        
        # Display all on resume
        self._write_command(SSD1306_DISPLAYALLON_RESUME)
        
        # Normal display (not inverted)
        self._write_command(SSD1306_NORMALDISPLAY)
        
        # Deactivate scrolling
        self._write_command(SSD1306_DEACTIVATE_SCROLL)
        
        # Turn on display
        self._write_command(SSD1306_DISPLAYON)
    
    def close(self) -> None:
        """Close the display connection."""
        if self._bus or self._i2c_file:
            try:
                # Turn off display before closing
                self._write_command(SSD1306_DISPLAYOFF)
            except:
                pass  # Ignore errors during cleanup
            try:
                if self._use_direct_i2c and self._i2c_file:
                    # Close direct I2C file
                    self._i2c_file.close()
                elif self._bus:
                    # Close I2C bus to release it
                    self._bus.close()
            except:
                pass  # Ignore errors during cleanup
        self._bus = None
        self._i2c_file = None
        self._use_direct_i2c = False
        self._image = None
        self._draw = None
        self._font = None
    
    def __enter__(self) -> "OledDisplay":
        """Context manager entry."""
        if self._bus is None:
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
        if self._bus is None:
            self.open()
        
        # Convert PIL image to bytes
        pixels = list(self._image.getdata())
        buffer = bytearray()
        
        # Convert 8-bit pixels to 8-pixel pages
        for page in range(self._height // 8):
            for col in range(self._width):
                byte = 0
                for bit in range(8):
                    y = page * 8 + bit
                    if y < self._height:
                        pixel = pixels[y * self._width + col]
                        if pixel:
                            byte |= (1 << bit)
                buffer.append(byte)
        
        # Set column address
        self._write_command(SSD1306_COLUMNADDR)
        self._write_command(0)
        self._write_command(self._width - 1)
        
        # Set page address
        self._write_command(SSD1306_PAGEADDR)
        self._write_command(0)
        self._write_command((self._height // 8) - 1)
        
        # Write display data
        self._write_data(bytes(buffer))
    
    # ----------------------------- High-level Drawing APIs ----------------------------
    
    def draw_border(self, thickness: int = 1) -> None:
        """Draw a border around the display."""
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
        """Draw text on the display."""
        if self._draw is None:
            self.open()
        if font is None:
            font = self._font
        self._draw.text((x, y), text, font=font, fill=fill)
        # Note: Don't call show() here - let caller batch updates
    
    def draw_centered_text(
        self,
        text: str,
        y: int = None,
        *,
        font=None,
        fill: int = 1,
    ) -> None:
        """Draw centered text on the display."""
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
        # Note: Don't call show() here - let caller batch updates
    
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
        """Draw a rectangle."""
        if self._draw is None:
            self.open()
        self._draw.rectangle(
            (x, y, x + width - 1, y + height - 1),
            outline=outline,
            fill=fill
        )
        # Note: Don't call show() here - let caller batch updates
    
    def draw_circle(
        self,
        x: int,
        y: int,
        radius: int,
        *,
        outline: int = 1,
        fill: int = 0,
    ) -> None:
        """Draw a circle."""
        if self._draw is None:
            self.open()
        self._draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            outline=outline,
            fill=fill
        )
        # Note: Don't call show() here - let caller batch updates
    
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
        """Draw a line."""
        if self._draw is None:
            self.open()
        self._draw.line((x1, y1, x2, y2), fill=fill, width=width)
        # Note: Don't call show() here - let caller batch updates


if __name__ == "__main__":
    print("OLED Simple Driver Test")
    print("=" * 40)
    
    if not SMBUS_AVAILABLE:
        print("ERROR: smbus2 not available. Install with: pip install smbus2")
        exit(1)
    
    if not PIL_AVAILABLE:
        print("ERROR: PIL/Pillow not available. Install with: pip install Pillow")
        exit(1)
    
    oled = OledDisplay(lazy_hw=True)
    try:
        oled.open()
        print("OLED initialized successfully")
        
        # Test clear
        oled.clear()
        print("Display cleared")
        time.sleep(1)
        
        # Test text
        oled.clear()
        oled.draw_text("Hello", 0, 0)
        oled.draw_text("World!", 0, 10)
        oled.show()
        print("Text displayed")
        time.sleep(2)
        
        # Test centered text
        oled.clear()
        oled.draw_centered_text("Test", 8)
        oled.draw_centered_text("OLED", 20)
        oled.show()
        print("Centered text displayed")
        time.sleep(2)
        
        # Test border
        oled.clear()
        oled.draw_border(1)
        print("Border drawn")
        time.sleep(2)
        
        oled.clear()
        print("Test complete")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        oled.close()

