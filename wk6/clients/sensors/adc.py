from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List


class Sensor:
    name = "adc"

    def __init__(self, adc_channel: int = 2):
        self.adc_channel = adc_channel
        self.paths = self._build_paths(adc_channel)

    @staticmethod
    def _build_paths(channel: int) -> List[str]:
        base = "/sys/bus/iio/devices/iio:device0"
        return [
            os.path.join(base, f"in_voltage{channel}_raw"),
        ]

    def _read_sysfs(self) -> int:
        for path in self.paths:
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    value = int(handle.read().strip())
                    return value
            except FileNotFoundError:
                continue
            except (ValueError, OSError) as exc:
                print(f"[ADC] Failed to read {path}: {exc}")
        raise RuntimeError("ADC path not found or unreadable")

    def read(self) -> Dict[str, Any]:
        value = self._read_sysfs()
        return {
            "value": value,
            "unit": "raw",
            "adc_channel": self.adc_channel,
            "timestamp": datetime.utcnow().isoformat(),
        }

