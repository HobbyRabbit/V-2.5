from __future__ import annotations

import asyncio
import logging

from bleak import BleakClient
from bleak_retry_connector import establish_connection

from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


TOTAL_PORTS = 8

SERVICE_UUID = "0000fe61-0000-1000-8000-00805f9b34fb"
WRITE_UUID   = "0000fe62-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID  = "0000fe63-0000-1000-8000-00805f9b34fb"


# ============================================================
# PACKET LOGGER SWITCH
# ============================================================

DEBUG_PACKETS = True   # <--- flip to False when done


def _hex(data: bytes) -> str:
    return " ".join(f"{b:02X}" for b in data)


# ============================================================
# Coordinator
# ============================================================

class ACInfinityCoordinator(DataUpdateCoordinator):
    """BLE connection + packet logger + state manager."""

    def __init__(self, hass, mac: str):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=30,
        )

        self.mac = mac
        self.client = None
        self._lock = asyncio.Lock()

        self.data = {
            port: {"power": False, "speed": 0}
            for port in range(1, TOTAL_PORTS + 1)
        }

    # ========================================================
    # CONNECT
    # ========================================================

    async def _ensure_connected(self):
        if self.client and self.client.is_connected:
            return

        device = async_ble_device_from_address(self.hass, self.mac)
        if not device:
            raise UpdateFailed(f"BLE device not found: {self.mac}")

        self.client = await establish_connection(
            BleakClient,
            device,
            self.mac,
        )

        await self.client.start_notify(NOTIFY_UUID, self._notify)

        _LOGGER.info("AC Infinity connected: %s", self.mac)

    # ========================================================
    # NOTIFY (RX packets)
    # ========================================================

    def _notify(self, _, data: bytearray):

        if DEBUG_PACKETS:
            _LOGGER.warning("RX  <- %s", _hex(data))

        if len(data) < 3:
            return

        port = data[0] + 1
        power = bool(data[1])
        speed = int(data[2])

        if port in self.data:
            self.data[port]["power"] = power
            self.data[port]["speed"] = speed
            self.async_set_updated_data(self.data)

    # ========================================================
    # UPDATE
    # ========================================================

    async def _async_update_data(self):
        try:
            await self._ensure_connected()

            # ask for state refresh
            await self._write(b"\xFF")

            await asyncio.sleep(0.2)

            return self.data

        except Exception as err:
            raise UpdateFailed(err) from err

    # ========================================================
    # WRITE (TX packets)
    # ========================================================

    async def _write(self, payload: bytes):

        if DEBUG_PACKETS:
            _LOGGER.warning("TX  -> %s", _hex(payload))

        await self.client.write_gatt_char(
            WRITE_UUID,
            payload,
            response=True,
        )

    # ========================================================
    # PUBLIC API
    # ========================================================

    async def async_set_power(self, port: int, power: bool):
        async with self._lock:
            await self._ensure_connected()

            value = 1 if power else 0
            packet = bytes([port - 1, 0x01, value])

            await self._write(packet)

    async def async_set_speed(self, port: int, percentage: int):
        async with self._lock:
            await self._ensure_connected()

            percentage = max(0, min(100, percentage))

            packet = bytes([port - 1, 0x02, percentage])

            await self._write(packet)
