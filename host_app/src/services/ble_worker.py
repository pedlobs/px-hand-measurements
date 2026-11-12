"""BLE communication service for communication with STM32WB55"""

import asyncio
import queue
import struct
import threading
from typing import Callable, List, Optional, Tuple

from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic

from src.config import BleConfig, HardwareConfig
from src.models.telemetry import HandTelemetry


class BleWorker:
    """Manages the BLE connection and notifications from STM32WB55"""

    def __init__(
        self,
        data_queue: queue.Queue,
        ble_config: BleConfig = BleConfig(),
        hw_config: HardwareConfig = HardwareConfig(),
        on_status_change: Optional[Callable[[bool, str], None]] = None,
    ) -> None:
        self.data_queue = data_queue
        self._ble_config = ble_config
        self._hw_config = hw_config
        self._on_status_change = on_status_change
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._stop_event: Optional[asyncio.Event] = None
        self._client: Optional[BleakClient] = None

    @property
    def is_connected(self) -> bool:
        return bool(self._client and self._client.is_connected)

    @staticmethod
    def scan_devices(timeout: float = 5.0) -> List[Tuple[str, str]]:
        """
        Synchronous helper to list nearby BLE devices as (name, address) tuples.
        Can be called from a background thread to populate a UI combobox.
        """

        async def _scan() -> List[Tuple[str, str]]:
            devices = await BleakScanner.discover(timeout=timeout)
            return [(d.name or "Unknown", d.address) for d in devices if d.name]

        return asyncio.run(_scan())

    def connect(self, address_or_name: Optional[str] = None) -> None:
        """Starts the background BLE thread and connects to STM32WB55"""
        self.disconnect()
        target = address_or_name or self._ble_config.device_name
        self._running = True
        self._thread = threading.Thread(
            target=self._run_async_loop,
            args=(target,),
            daemon=True,
        )
        self._thread.start()

    def disconnect(self) -> None:
        """Signals the async loop to stop and closes the BLE connection safely"""
        self._running = False
        if self._loop and self._stop_event and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._stop_event.set)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        self._thread = None
        self._loop = None
        self._client = None

    def read_once(self) -> bool:
        """Triggers an explicit GATT READ on the Force_Data characteristic"""
        if not (self._loop and self._loop.is_running() and self.is_connected):
            return False

        asyncio.run_coroutine_threadsafe(self._async_read_once(), self._loop)
        return True

    def _run_async_loop(self, target: str) -> None:
        """Dedicated asyncio event loop running inside the daemon thread"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._stop_event = asyncio.Event()
        try:
            self._loop.run_until_complete(self._ble_main(target))
        finally:
            self._loop.close()

    async def _ble_main(self, target: str) -> None:
        """Finds the STM32WB55, connects, and subscribes to notifications"""
        try:
            self._notify_status(False, f"Scanning for '{target}'...")

            device = await BleakScanner.find_device_by_name(
                target, timeout=self._ble_config.scan_timeout_s
            )
            if device is None:
                device = await BleakScanner.find_device_by_address(
                    target, timeout=self._ble_config.scan_timeout_s
                )

            if device is None:
                self._notify_status(False, f"Device '{target}' not found via BLE.")
                self._running = False
                return

            def _on_disconnect(_client: BleakClient) -> None:
                if self._running:
                    self._notify_status(False, "BLE device disconnected.")
                if self._stop_event and not self._stop_event.is_set():
                    self._stop_event.set()

            async with BleakClient(
                device, disconnected_callback=_on_disconnect
            ) as client:
                self._client = client
                self._notify_status(
                    True, f"Connected to {device.name} ({device.address})"
                )

                await client.start_notify(
                    self._ble_config.force_char_uuid,
                    self._notification_handler,
                )

                if self._stop_event:
                    await self._stop_event.wait()

                if client.is_connected:
                    await client.stop_notify(self._ble_config.force_char_uuid)

        except Exception as exc:
            self._notify_status(False, f"BLE Error: {exc}")
        finally:
            self._running = False
            self._client = None
            self._notify_status(False, "BLE Disconnected.")

    async def _async_read_once(self) -> None:
        """Performs a single GATT READ and processes the 8-byte payload"""
        if self._client and self._client.is_connected:
            try:
                raw_bytes = await self._client.read_gatt_char(
                    self._ble_config.force_char_uuid
                )
                telemetry = self._parse_payload(bytes(raw_bytes))
                if telemetry:
                    self._push_to_queue(telemetry)
            except Exception:
                pass

    def _notification_handler(
        self, _characteristic: BleakGATTCharacteristic, data: bytearray
    ) -> None:
        """Callback triggered automatically on every BLE NOTIFY packet"""
        telemetry = self._parse_payload(bytes(data))
        if telemetry:
            self._push_to_queue(telemetry)

    def _parse_payload(self, payload: bytes) -> Optional[HandTelemetry]:
        """Unpacks 8 bytes (Little-endian, 4 x uint16) into a HandTelemetry object."""
        if len(payload) != self._ble_config.payload_size_bytes:
            return None

        try:
            unpacked = struct.unpack(self._ble_config.struct_format, payload)
            sensors = list(unpacked[: self._hw_config.num_sensors])

            threshold = self._hw_config.led_threshold_default
            leds = [val >= threshold for val in sensors[: self._hw_config.num_leds]]

            hex_str = payload.hex(" ").upper()
            raw_line = f"[BLE] {sensors} | HEX: {hex_str}"

            return HandTelemetry(
                sensors=sensors,
                leds=leds,
                raw_line=raw_line,
            )
        except struct.error:
            return None

    def _push_to_queue(self, item: HandTelemetry) -> None:
        """Inserts in the queue and removes the oldest item if full"""
        if self.data_queue.full():
            try:
                self.data_queue.get_nowait()
            except queue.Empty:
                pass
        self.data_queue.put_nowait(item)

    def _notify_status(self, connected: bool, message: str) -> None:
        if self._on_status_change:
            self._on_status_change(connected, message)
