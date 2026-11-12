"""Asynchronous .xlsx Data Logger service for legacy trial schema."""

from datetime import datetime
from pathlib import Path
import threading
import time
from typing import Callable, Optional

from openpyxl import Workbook, load_workbook

from src.config import LoggingConfig
from src.models.telemetry import HandTelemetry, TrialMetadata


class DataLoggerService:
    HEADERS = [
        "Timestamp", "Name", "DOB", "Age", "Description",
        "Movement", "Finger", "C0", "C1", "C2", "C3",
    ]

    def __init__(self, config: LoggingConfig) -> None:
        self._config = config
        self._current_file: Optional[Path] = None
        self._lock = threading.Lock()
        self._is_capturing = False

    @property
    def current_file(self) -> Optional[Path]:
        return self._current_file

    @property
    def is_capturing(self) -> bool:
        return self._is_capturing

    def create_session_workbook(self, target_dir: Optional[Path] = None) -> Path:
        base_dir = target_dir or Path(self._config.data_dir)
        base_dir.mkdir(parents=True, exist_ok=True)

        filename = f"hand_measurements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        file_path = base_dir / filename

        wb = Workbook()
        ws = wb.active
        ws.append(self.HEADERS)
        wb.save(file_path)

        with self._lock:
            self._current_file = file_path
        return file_path

    def start_capture(
        self,
        metadata: TrialMetadata,
        sample_provider: Callable[[], HandTelemetry],
        on_progress: Optional[Callable[[int, int], None]] = None,
        on_complete: Optional[Callable[[bool, str], None]] = None,
    ) -> bool:
        if self._current_file is None or not self._current_file.exists():
            if on_complete:
                on_complete(False, "Ceates an excl file before starting capture")
            return False

        if self._is_capturing:
            if on_complete:
                on_complete(False, "Capture ongoing already")
            return False

        self._is_capturing = True
        threading.Thread(
            target=self._capture_worker,
            args=(metadata, sample_provider, on_progress, on_complete),
            daemon=True,
        ).start()
        return True

    def _capture_worker(
        self,
        metadata: TrialMetadata,
        sample_provider: Callable[[], HandTelemetry],
        on_progress: Optional[Callable[[int, int], None]],
        on_complete: Optional[Callable[[bool, str], None]],
    ) -> None:
        total = self._config.capture_samples
        try:
            with self._lock:
                wb = load_workbook(self._current_file)
                ws = wb.active

                for idx in range(1, total + 1):
                    sample = sample_provider()
                    c0, c1, c2, c3 = sample.sensors[:4]

                    if metadata.movement.strip().lower() == "lateral":
                        sensor_cols = [c0, c1, c2, "-"]
                    else:
                        sensor_cols = ["-", "-", "-", c3]

                    row = [
                        datetime.now().isoformat(),
                        metadata.name,
                        metadata.dob,
                        metadata.age,
                        metadata.description,
                        metadata.movement,
                        metadata.finger,
                        *sensor_cols,
                    ]
                    ws.append(row)

                    if on_progress:
                        on_progress(idx, total)

                    if idx < total:
                        time.sleep(self._config.capture_interval_s)

                wb.save(self._current_file)

            if on_complete:
                on_complete(True, f"Capture finished ({total} samples saved).")
        except Exception as exc:
            if on_complete:
                on_complete(False, f"Error in capture: {exc}")
        finally:
            self._is_capturing = False
