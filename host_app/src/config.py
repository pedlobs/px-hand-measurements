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


class BleConfig:
    device_name: str = "HAND_SENSOR"
    service_uuid: str = "00000000-cc7a-482a-984a-7f2ed5b3e58f"
    force_char_uuid: str = "00000000-8e22-4541-9d4c-21edae82ed19"
    scan_timeout_s: float = 5.0
    payload_size_bytes: int = 8
    struct_format: str = "<4H"  # Little-endian, 4x uint16


@dataclass(frozen=True)
class HardwareConfig:
    num_sensors: int = 4
    num_leds: int = 4
    adc_max_value: int = 4095  
    led_threshold_default: int = 2048


@dataclass(frozen=True)
class LoggingConfig:
    data_dir: str = "data"
    merged_output_filename: str = "merged_stats.csv"
    capture_samples: int = 10
    capture_interval_s: float = 0.02
    movements: Tuple[str, ...] = ("Lateral Ulnar", "Lateral Radial", "Dorsal", "Volar", "Rotacional", "Push", "Pull")
    fingers: Tuple[str, ...] = ("Thumb", "Index", "Middle", "Ring", "Pinky").


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
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    ble: BleConfig = field(default_factory=BleConfig)
