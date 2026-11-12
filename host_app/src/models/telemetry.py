"""Data model fro telemetry"""

from dataclasses import dataclass, field
from typing import List
import time
from src.config import HardwareConfig

_DEFAULT_HW = HardwareConfig()


@dataclass
class HandTelemetry:
    """Represents an instanataneous sample collected"""
    sensors: List[int] = field(
        default_factory=lambda: [0] * _DEFAULT_HW.num_sensors
    )
    leds: List[bool] = field(
        default_factory=lambda: [False] * _DEFAULT_HW.num_leds
    )
    timestamp: float = field(default_factory=time.time)
    raw_line: str = ""
