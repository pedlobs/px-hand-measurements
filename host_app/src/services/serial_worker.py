"""Serial comm service in background"""

import json
import math
import queue
import threading
import time
from typing import List, Optional
import serial
import serial.tools.list_ports

from src.config import HardwareConfig, SerialConfig
from src.models.telemetry import HandTelemetry


class SerialWorker:
    """Manages the UART connexion"""

    def __init__(
        self,
        data_queue: queue.Queue,
        serial_config: SerialConfig = SerialConfig(),
        hw_config: HardwareConfig = HardwareConfig(),
    ):
        self.data_queue = data_queue
        self._serial_config = serial_config
        self._hw_config = hw_config

        self._serial: Optional[serial.Serial] = None
        self._running = False
        self._simulating = False
        self._thread: Optional[threading.Thread] = None

    @staticmethod
    def list_available_ports() -> List[str]:
        """REturns the availables ports"""
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect(self, port: str, baudrate: int) -> None:
        """Opens and begins the reading thread for the selected port"""
        self.disconnect()
        self._serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=self._serial_config.timeout_s,
        )
        self._simulating = False
        self._running = True
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def start_simulation(self) -> None:
        """Starts the simulatoion of data"""
        self.disconnect()
        self._simulating = True
        self._running = True
        self._thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self._thread.start()

    def disconnect(self) -> None:
        """Closes the reading thread and closes the serial portsafely"""
        self._running = False
        self._simulating = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)
        if self._serial and self._serial.is_open:
            self._serial.close()
        self._serial = None

    def send_command(self, cmd: str) -> bool:
        """Sends a command to STM32 via UART"""
        if self._serial and self._serial.is_open:
            try:
                payload = f"{cmd.strip()}\n".encode("utf-8")
                self._serial.write(payload)
                return True
            except serial.SerialException:
                return False
        return False

    def _read_loop(self) -> None:
        """Seral reading loop for the port"""
        while self._running and self._serial and self._serial.is_open:
            try:
                raw_bytes = self._serial.readline()
                if not raw_bytes:
                    continue
                line = raw_bytes.decode("utf-8", errors="ignore").strip()
                if line:
                    telemetry = self._parse_line(line)
                    if telemetry:
                        self._push_to_queue(telemetry)
            except serial.SerialException:
                break

    def _simulation_loop(self) -> None:
        """For simulation, generates data to validate interafce"""
        t0 = time.time()
        max_adc = self._hw_config.adc_max_value
        threshold = self._hw_config.led_threshold_default

        while self._running and self._simulating:
            elapsed = time.time() - t0
            sensors = []
            leds = []
            for i in range(self._hw_config.num_sensors):
                val = int((math.sin(elapsed * 2.0 + i) + 1.0) * (max_adc / 2))
                sensors.append(val)
                leds.append(val >= threshold)

            fake_json = json.dumps({"s": sensors, "l": [int(x) for x in leds]})
            telemetry = HandTelemetry(
                sensors=sensors,
                leds=leds,
                raw_line=f"[SIM] {fake_json}",
            )
            self._push_to_queue(telemetry)
            time.sleep(0.05)

    def _push_to_queue(self, item: HandTelemetry) -> None:
        """Inserts in the queue and and removes the oldest item IF FULL"""
        if self.data_queue.full():
            try:
                self.data_queue.get_nowait()
            except queue.Empty:
                pass
        self.data_queue.put_nowait(item)

    def _parse_line(self, line: str) -> Optional[HandTelemetry]:
        """PArses a JSON or CSV line received vua UART"""
        num_s = self._hw_config.num_sensors
        num_l = self._hw_config.num_leds
        threshold = self._hw_config.led_threshold_default

        if line.startswith("{") and line.endswith("}"):
            try:
                data = json.loads(line)
                raw_s = data.get("s") or data.get("sensors", [])
                raw_l = data.get("l") or data.get("leds", [])

                sensors = [int(x) for x in raw_s[:num_s]]
                while len(sensors) < num_s:
                    sensors.append(0)

                if raw_l:
                    leds = [bool(int(x)) for x in raw_l[:num_l]]
                else:
                    leds = [val >= threshold for val in sensors]

                while len(leds) < num_l:
                    leds.append(False)

                return HandTelemetry(sensors=sensors, leds=leds, raw_line=line)
            except (ValueError, KeyError, TypeError):
                return None

        try:
            normalized = line.replace(",", " ").replace(";", " ")
            parts = [int(float(p)) for p in normalized.split() if p]
            if len(parts) >= num_s:
                sensors = parts[:num_s]
                if len(parts) >= num_s + num_l:
                    leds = [bool(x) for x in parts[num_s : num_s + num_l]]
                else:
                    leds = [val >= threshold for val in sensors]
                return HandTelemetry(sensors=sensors, leds=leds, raw_line=line)
        except ValueError:
            pass

        return None
