from __future__ import annotations

from typing import Any, Dict

from . import simulated, adc


class SensorBase:
    """Abstract base class for sensor readers."""

    name = "base"

    def read(self) -> Dict[str, Any]:
        raise NotImplementedError


SENSOR_BUILDERS = {
    "simulated": simulated.Sensor,
    "adc": adc.Sensor,
}


def list_sensors() -> list[str]:
    return sorted(SENSOR_BUILDERS.keys())


def build_sensor(sensor_type: str, **kwargs) -> SensorBase:
    sensor_type = sensor_type.lower()
    if sensor_type not in SENSOR_BUILDERS:
        raise ValueError(
            f"Unknown sensor '{sensor_type}'. Available: {', '.join(list_sensors())}"
        )
    return SENSOR_BUILDERS[sensor_type](**kwargs)

