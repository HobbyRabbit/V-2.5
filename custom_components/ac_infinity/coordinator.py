"""AC Infinity BLE Coordinator."""

from __future__ import annotations

import logging
from datetime import timedelta

from bleak import BleakClient

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=10)

# BLE UUIDs
SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"


class ACInfinityCoordinator(DataUpdateCoordinator):
    """Coordinator for AC Infinity controller."""

    def __init__(self, hass, mac: str, name: str):
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=UPDATE_INTERVAL,
        )

        self.mac = mac
        self.name = name
        self.client = BleakClient(mac)

        # Data store
        self.data = {
            "temperature": None,
            "humidity": None,
            "ports": {i: False for i in range(1, 9)},
        }

    async def _ensure_connected(self):
        """Ensure BLE connection."""
        if not self.client.is_connected:
            _LOGGER.debug("Connecting to AC Infinity %s", self.mac)
            await self.client.connect()

            await self.client.start_notify(
                NOTIFY_UUID,
                self._handle_notification,
            )

    async def _async_update_data(self):
        """Fetch data from device."""
        try:
            await self._ensure_connected()
            return self.data

        except Exception as err:
            raise UpdateFailed(f"BLE error: {err}") from err

    def _handle_notification(self, sender: int, data: bytearray):
        """Handle BLE notification packets."""
        try:

            if len(data) < 16:
                return

            # Validate packet header
            if data[0:5] != b"JGQUA":
                return

            # ---- Temperature decode
            temp_raw = (data[9] << 8) | data[10]
            temperature = round(temp_raw / 36, 1)

            # ---- Humidity decode
            humidity_raw = data[11]
            humidity = int(humidity_raw / 3)

            self.data["temperature"] = temperature
            self.data["humidity"] = humidity

            # ---- Port state decode
            port = data[13]
            state = data[15]

            if 1 <= port <= 8:
                self.data["ports"][port] = bool(state)

            _LOGGER.debug(
                "AC Infinity packet decoded | Temp=%sF Humidity=%s%% Port=%s State=%s",
                temperature,
                humidity,
                port,
                state,
            )

        except Exception as err:
            _LOGGER.error("AC Infinity packet parse error: %s", err)
