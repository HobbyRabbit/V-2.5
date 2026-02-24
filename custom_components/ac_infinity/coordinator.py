from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from bleak import BleakClient, BleakError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

DOMAIN = "ac_infinity"

_LOGGER = logging.getLogger(__name__)

# Hunterjm-discovered primary service UUID (advertised FE61)
AC_INFINITY_SERVICE_UUID = "0000fe61-0000-1000-8000-00805f9b34fb"

# Polling interval (safe & slow while reverse engineering)
SCAN_INTERVAL = timedelta(seconds=30)


class ACInfinityCoordinator(DataUpdateCoordinator):
    """Coordinator for AC Infinity BLE devices."""

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        address: str,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=SCAN_INTERVAL,
        )

        self.address = address
        self.client: BleakClient | None = None

    async def _ensure_connected(self) -> None:
        """Ensure BLE client is connected."""
        if self.client and self.client.is_connected:
            return

        _LOGGER.debug("Connecting to AC Infinity device at %s", self.address)

        try:
            self.client = BleakClient(self.address)
            await self.client.connect(timeout=15.0)

            if not self.client.is_connected:
                raise BleakError("BLE connection failed")

            _LOGGER.info(
                "Connected to AC Infinity device %s",
                self.address,
            )

        except Exception as err:
            self.client = None
            raise UpdateFailed(f"BLE connect failed: {err}") from err

    async def _async_update_data(self) -> dict:
        """Fetch data from device (minimal, safe stub)."""

        try:
            await self._ensure_connected()

            # 🔎 For now we return connection status only
            # Real GATT parsing comes next
            return {
                "connected": True,
                "address": self.address,
            }

        except Exception as err:
            _LOGGER.error(
                "Unexpected error fetching AC Infinity %s data",
                self.name,
                exc_info=True,
            )
            raise UpdateFailed(err) from err

    async def async_shutdown(self) -> None:
        """Disconnect BLE on shutdown."""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            _LOGGER.debug("Disconnected BLE device %s", self.address)
