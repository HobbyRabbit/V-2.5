from __future__ import annotations

import logging
from datetime import timedelta

from bleak_retry_connector import establish_connection
from bleak import BleakClient

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import UPDATE_INTERVAL, CHAR_UUID

_LOGGER = logging.getLogger(__name__)

PORTS = 8


class ACInfinityCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, mac: str):
        self.mac = mac
        self.client: BleakClient | None = None

        self._power = [False] * PORTS
        self._speed = [0] * PORTS

        super().__init__(
            hass,
            _LOGGER,
            name=f"AC Infinity {mac}",
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def _ensure_connected(self):
        if self.client and self.client.is_connected:
            return

        try:
            self.client = await establish_connection(
                BleakClient,
                self.mac,
                name="ACInfinity",
            )
        except Exception as err:
            raise UpdateFailed(f"BLE connect failed: {err}") from err

    # ---------- packet helpers ----------

    def _build_payload(self):
        p = [1 if x else 0 for x in self._power]
        s = self._speed
        return bytes(p + s)

    # ---------- polling ----------

    async def _async_update_data(self):
        await self._ensure_connected()

        try:
            data = await self.client.read_gatt_char(CHAR_UUID)

            for i in range(PORTS):
                self._power[i] = bool(data[i])
                self._speed[i] = int(data[i + PORTS])

            return {
                "power": self._power,
                "speed": self._speed,
            }

        except Exception as err:
            raise UpdateFailed(str(err)) from err

    # ---------- commands ----------

    async def set_power(self, index: int, state: bool):
        self._power[index] = state
        await self.client.write_gatt_char(CHAR_UUID, self._build_payload())

    async def set_speed(self, index: int, speed: int):
        self._speed[index] = speed
        await self.client.write_gatt_char(CHAR_UUID, self._build_payload())
