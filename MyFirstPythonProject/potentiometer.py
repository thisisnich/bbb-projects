import time
from typing import Optional, Tuple


class Potentiometer:
    """Driver for a potentiometer controlled via ADC.

    Reads voltage, percentage, and raw ADC values with optional calibration.
    """

    def __init__(
        self,
        pin: str = "P9_37",
        *,
        voltage_range: Tuple[float, float] = (0.0, 1.8),
        calibrated_min: Optional[float] = None,
        calibrated_max: Optional[float] = None,
        smoothing_samples: int = 1,
        lazy_hw: bool = False,
    ) -> None:
        """Initialize the potentiometer.

        Args:
            pin: ADC pin identifier (default: P9_37)
            voltage_range: Expected voltage range (min_voltage, max_voltage), default (0.0, 1.8)
            calibrated_min: Calibrated minimum voltage (None = use voltage_range min)
            calibrated_max: Calibrated maximum voltage (None = use voltage_range max)
            smoothing_samples: Number of samples for averaging (1 = no smoothing)
            lazy_hw: If True, don't initialize hardware until open() is called
        """
        self._pin = pin
        self._voltage_range = voltage_range
        self._smoothing_samples = smoothing_samples
        self._lazy_hw = lazy_hw

        self._calibrated_min = calibrated_min if calibrated_min is not None else voltage_range[0]
        self._calibrated_max = calibrated_max if calibrated_max is not None else voltage_range[1]

        if self._calibrated_min >= self._calibrated_max:
            raise ValueError("calibrated_min must be less than calibrated_max")

        self._ADC = None  # type: ignore[var-annotated]
        self._sample_buffer = []

        if not self._lazy_hw:
            self.open()

    def open(self) -> None:
        """Open the ADC connection and initialize."""
        if self._ADC is not None:
            return

        import Adafruit_BBIO.ADC as ADC  # type: ignore

        self._ADC = ADC
        ADC.setup()

    def close(self) -> None:
        """Close the ADC connection."""
        self._ADC = None
        self._sample_buffer.clear()

    def __enter__(self) -> "Potentiometer":
        """Context manager entry."""
        if self._ADC is None:
            self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Context manager exit."""
        self.close()

    def read_raw(self) -> float:
        """Read raw ADC digital value.

        Returns:
            Raw ADC value (0.0 - 1.0)
        """
        if self._ADC is None:
            self.open()
        return self._ADC.read(self._pin)  # type: ignore[attr-defined]

    def read_raw_voltage(self) -> float:
        """Read raw ADC voltage without calibration.

        Returns:
            Raw ADC voltage (0.0 - 1.8V typically)
        """
        digital_value = self.read_raw()
        return digital_value * 1.8  # Convert to voltage

    def read_voltage(self) -> float:
        """Read voltage with calibration applied.

        Returns:
            Calibrated voltage in volts
        """
        raw_voltage = self.read_raw_voltage()

        # Apply smoothing if enabled
        if self._smoothing_samples > 1:
            self._sample_buffer.append(raw_voltage)
            if len(self._sample_buffer) > self._smoothing_samples:
                self._sample_buffer.pop(0)
            voltage = sum(self._sample_buffer) / len(self._sample_buffer)
        else:
            voltage = raw_voltage

        # Apply calibration (scale from raw range to calibrated range)
        raw_range = self._voltage_range[1] - self._voltage_range[0]
        cal_range = self._calibrated_max - self._calibrated_min

        if raw_range > 0:
            # Normalize to 0-1 range
            normalized = (voltage - self._voltage_range[0]) / raw_range
            # Scale to calibrated range
            calibrated = self._calibrated_min + (normalized * cal_range)
        else:
            calibrated = voltage

        return calibrated

    def read_percentage(self) -> float:
        """Read percentage based on calibrated voltage range.

        Returns:
            Percentage (0.0 - 100.0)
        """
        voltage = self.read_voltage()
        cal_range = self._calibrated_max - self._calibrated_min

        if cal_range > 0:
            percentage = ((voltage - self._calibrated_min) / cal_range) * 100.0
        else:
            percentage = 0.0

        # Clamp to 0-100
        return max(0.0, min(100.0, percentage))

    def calibrate_min(self) -> None:
        """Set current reading as minimum voltage."""
        current_voltage = self.read_raw_voltage()
        self._calibrated_min = current_voltage
        print(f"Calibrated minimum: {current_voltage:.3f}V")

    def calibrate_max(self) -> None:
        """Set current reading as maximum voltage."""
        current_voltage = self.read_raw_voltage()
        self._calibrated_max = current_voltage
        print(f"Calibrated maximum: {current_voltage:.3f}V")

    def reset_calibration(self) -> None:
        """Reset calibration to voltage_range defaults."""
        self._calibrated_min = self._voltage_range[0]
        self._calibrated_max = self._voltage_range[1]
        print(f"Calibration reset to range: {self._voltage_range}")

    def get_calibration(self) -> Tuple[float, float]:
        """Get current calibration range.

        Returns:
            Tuple of (min_voltage, max_voltage)
        """
        return (self._calibrated_min, self._calibrated_max)


def _print_menu() -> None:
    """Print the test menu."""
    print("\nPotentiometer test menu:")
    print("  1) read_voltage")
    print("  2) read_percentage")
    print("  3) read_raw")
    print("  4) read_raw_voltage")
    print("  5) calibrate_min")
    print("  6) calibrate_max")
    print("  7) reset_calibration")
    print("  8) get_calibration")
    print("  9) poll_loop [interval_s] [count]")
    print("  q) quit")


if __name__ == "__main__":
    pot = Potentiometer()
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
                    voltage = pot.read_voltage()
                    print(f"Voltage: {voltage:.3f}V")
                elif cmd == "2":
                    percentage = pot.read_percentage()
                    print(f"Percentage: {percentage:.1f}%")
                elif cmd == "3":
                    raw = pot.read_raw()
                    print(f"Raw ADC value: {raw:.3f}")
                elif cmd == "4":
                    raw_voltage = pot.read_raw_voltage()
                    print(f"Raw voltage: {raw_voltage:.3f}V")
                elif cmd == "5":
                    pot.calibrate_min()
                elif cmd == "6":
                    pot.calibrate_max()
                elif cmd == "7":
                    pot.reset_calibration()
                elif cmd == "8":
                    min_v, max_v = pot.get_calibration()
                    print(f"Calibration range: ({min_v:.3f}V, {max_v:.3f}V)")
                elif cmd == "9":
                    interval = float(parts[1]) if len(parts) > 1 else 0.3
                    count = int(parts[2]) if len(parts) > 2 else 10
                    print(f"Polling loop (interval={interval}s, count={count})...")
                    for i in range(count):
                        voltage = pot.read_voltage()
                        percentage = pot.read_percentage()
                        raw = pot.read_raw()
                        print(f"[{i+1}] Voltage: {voltage:.3f}V, Percentage: {percentage:.1f}%, Raw: {raw:.3f}")
                        time.sleep(interval)
                else:
                    print("unknown command")
            except Exception as e:
                print(f"error: {e}")
    finally:
        pot.close()
        print("\nPotentiometer closed")


# ============================================================================
# ORIGINAL CODE (commented for reference)
# ============================================================================
# #potentiometer code
# import time
# import Adafruit_BBIO.ADC as ADC
#
# ADC.setup()
#
# while True:
#     DigitalValue = ADC.read("P9_37")
#     AnalogVoltage = DigitalValue * 1.8
#     print("Digital Value: %f, Analog Voltage: %f" % (DigitalValue, AnalogVoltage))
#     time.sleep(0.3)

