from __future__ import annotations

import random
from datetime import datetime
from typing import Any, Dict


class Sensor:
    name = "simulated"

    def __init__(self, min_value: int = 100, max_value: int = 4000):
        self.min_value = min_value
        self.max_value = max_value

    def read(self) -> Dict[str, Any]:
        value = random.randint(self.min_value, self.max_value)
        return {
            "value": value,
            "unit": "raw",
            "timestamp": datetime.utcnow().isoformat(),
        }

