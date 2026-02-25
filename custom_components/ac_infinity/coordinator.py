from __future__ import annotations

import asyncio
import logging

from bleak_retry_connector import establish_connection

from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


TOTAL_PORTS = 8

# --------------------------------------------------
# AC Infinity BLE UUIDs (69 Pro / Outlet controller)
# --------------------------------------------------

SERVICE_UUID = "0000fe61-0000-1000-8000-00805f9b34fb"
WRITE_UUID   = "0000fe62-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID  = "0000fe63-0000-1000-8000-00805f9b34fb"


# ==================================================
# Coordinator
# ==================================================

class ACInfinityCoordinator(DataUpdateCoordinator):
    """Central BLE connection + state manager."""

    def __init__(self, hass, mac: str):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=30,
        )

        self.mac = mac
        self.client = None

        # final HA state format
        self.data: dict[int, dict] = {
            port: {"power": False, "speed": 0}
            for port in range(1, TOTAL_PORTS + 1)
        }

        self._lock = asyncio.Lock()

    # ==================================================
    # Connection
    # ==================================================

    async def _ensure_connected(self):
        """Connect using HA bluetooth backend safely."""

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

        await self.client.start_notify(
            NOTIFY_UUID,
            self._notification_handler,
        )

        _LOGGER.debug("Connected to AC Infinity %s", self.mac)

    # ==================================================
    # Notifications
    # ==================================================

    def _notification_handler(self, _, data: bytearray):
        """Parse packets -> update coordinator state.

        Packet format (hunterjm protocol):
        byte0  = port index
        byte1  = power (0/1)
        byte2  = speed (0-100)
        """

        if len(data) < 3:
            return

        port = int(data[0]) + 1
        power = bool(data[1])
        speed = int(data[2])

        if port in self.data:
            self.data[port]["power"] = power
            self.data[port]["speed"] = speed

            self.async_set_updated_data(self.data)

    # ==================================================
    # HA polling
    # ==================================================

    async def _async_update_data(self):
        """Periodic refresh request to device."""

        try:
            await self._ensure_connected()

            # ask device for full state refresh
            await self._write(b"\xFF")

            await asyncio.sleep(0.2)

            return self.data

        except Exception as err:
            raise UpdateFailed(err) from err

    # ==================================================
    # Public API (called by fan entities)
    # ==================================================

    async def async_set_power(self, port: int, power: bool):
        async with self._lock:
            await self._ensure_connected()

            value = 1 if power else 0
            packet = bytes([port - 1, 0x01, value])

            await self._write(packet)

            self.data[port]["power"] = power
            self.async_set_updated_data(self.data)

    async def async_set_speed(self, port: int, percentage: int):
        async with self._lock:
            await self._ensure_connected()

            percentage = max(0, min(100, percentage))

            power = percentage > 0

            packet = bytes([port - 1, 0x02, percentage])

            await self._write(packet)

            self.data[port]["power"] = power
            self.data[port]["speed"] = percentage

            self.async_set_updated_data(self.data)

    # ==================================================
    # BLE write helper
    # ==================================================

    async def _write(self, payload: bytes):
        await self.client.write_gatt_char(
            WRITE_UUID,
            payload,
            response=True,
        )
