from __future__ import annotations

import logging
from datetime import timedelta

from bleak import BleakClient
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=5)
PORT_COUNT = 8


class ACInfinityCoordinator(DataUpdateCoordinator):
    """AC Infinity BLE coordinator."""

    def __init__(self, hass, address: str, name: str):
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=UPDATE_INTERVAL,
        )

        self.address = address  # ✅ FIX (was mac)
        self.name = name
        self.client: BleakClient | None = None

        # Safe defaults (prevents KeyError + min/max issues)
        self.data = {
            "temperature": 0.0,
            "humidity": 0.0,
            "ports": {
                i: {
                    "power": False,
                    "speed": 0,
                }
                for i in range(1, PORT_COUNT + 1)
            },
        }

    # --------------------------------------------------
    # BLE
    # --------------------------------------------------

    async def _ensure_connected(self):
        if self.client and self.client.is_connected:
            return

        try:
            self.client = BleakClient(self.address)
            await self.client.connect()
        except Exception as err:
            raise UpdateFailed(f"BLE connect failed: {err}") from err

    # --------------------------------------------------
    # Poll
    # --------------------------------------------------

    async def _async_update_data(self):
        """Fetch latest device state."""

        await self._ensure_connected()

        try:
            # TODO:
            # Replace with real read command when packet decoded.
            # For now we keep safe defaults so HA doesn't crash.
            return self.data

        except Exception as err:
            raise UpdateFailed(str(err)) from err

    # --------------------------------------------------
    # Controls
    # --------------------------------------------------

    async def set_port_power(self, port: int, on: bool):
        """Toggle outlet/fan."""
        await self._ensure_connected()

        cmd = bytearray([0xA5, port, 0x01 if on else 0x00])

        await self.client.write_gatt_char(
            "0000fff2-0000-1000-8000-00805f9b34fb",
            cmd,
            response=True,
        )

        self.data["ports"][port]["power"] = on
        await self.async_request_refresh()

    async def set_port_speed(self, port: int, percent: int):
        """Set fan speed (0-100%)."""
        await self._ensure_connected()

        percent = max(0, min(100, percent))

        cmd = bytearray([0xA6, port, percent])

        await self.client.write_gatt_char(
            "0000fff2-0000-1000-8000-00805f9b34fb",
            cmd,
            response=True,
        )

        self.data["ports"][port]["speed"] = percent
        await self.async_request_refresh()
