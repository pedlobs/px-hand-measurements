"""Global configuration module for the PX-HAND Host Application"""

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class SerialConfig:
    default_baudrate: int = 115200
    baudrate_options: Tuple[int, ...] = (
        9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600
    )
    timeout_s: float = 0.1


@dataclass(frozen=True)
class HardwareConfig:
    num_sensors: int = 4
    num_leds: int = 4
    adc_max_value: int = 4095  # 12-bit STM32WB55
    led_threshold_default: int = 2048


@dataclass(frozen=True)
class UIConfig:
    title: str = "PX-HAND | Telemetry & Control Monitor"
    geometry: str = "720x480"
    refresh_rate_ms: int = 30


@dataclass(frozen=True)
class AppConfig:
    ui: UIConfig = field(default_factory=UIConfig)
    serial: SerialConfig = field(default_factory=SerialConfig)
    hardware: HardwareConfig = field(default_factory=HardwareConfig)
