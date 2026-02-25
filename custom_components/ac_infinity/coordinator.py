from __future__ import annotations

import asyncio
import logging
import time

from bleak import BleakClient
from bleak_retry_connector import establish_connection

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)

# ==============================
# USER SETTINGS
# ==============================

PORT_COUNT = 8
LEARNING_MODE = True        # <<< TURN ON/OFF HERE
PACKET_LOGGER = True

UPDATE_INTERVAL = 10


# ==============================
# AC INFINITY UUIDs (hunterjm)
# ==============================

SERVICE_UUID = "0000fe61-0000-1000-8000-00805f9b34fb"
WRITE_UUID   = "0000fe62-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID  = "0000fe63-0000-1000-8000-00805f9b34fb"


# =========================================================
# COORDINATOR
# =========================================================

class ACInfinityCoordinator(DataUpdateCoordinator):

    def __init__(self, hass: HomeAssistant, mac: str, name: str):
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=None,
        )

        self.mac = mac
        self._client: BleakClient | None = None
        self._connected = False

        self.data = {
            port: {
                "power": False,
                "speed": 0,
            }
            for port in range(1, PORT_COUNT + 1)
        }

        # learning mode tracking
        self._last_packet = None
        self._last_time = 0

    # =====================================================
    # CONNECTION
    # =====================================================

    async def _ensure_connected(self):
        if self._connected and self._client:
            return

        try:
            self._client = await establish_connection(
                BleakClient,
                self.mac,
                name="AC Infinity",
            )

            await self._client.start_notify(NOTIFY_UUID, self._notify)

            self._connected = True
            _LOGGER.info("Connected to %s", self.mac)

        except Exception as err:
            raise UpdateFailed(f"BLE connect failed: {err}") from err

    # =====================================================
    # LEARNING MODE
    # =====================================================

    def _learn(self, data: bytes):
        if not LEARNING_MODE:
            return

        now = time.time()

        if self._last_packet and now - self._last_time < 2:
            _LOGGER.warning("=== LEARN DIFF ===")

            for i, (a, b) in enumerate(zip(self._last_packet, data)):
                if a != b:
                    _LOGGER.warning(
                        "byte[%d] %02X -> %02X",
                        i,
                        a,
                        b,
                    )

            _LOGGER.warning("=================")

        self._last_packet = data
        self._last_time = now

    # =====================================================
    # PACKET LOGGER
    # =====================================================

    def _log_packet(self, prefix: str, data: bytes):
        if PACKET_LOGGER:
            _LOGGER.warning("%s %s", prefix, data.hex(" "))

    # =====================================================
    # NOTIFY HANDLER
    # =====================================================

    def _notify(self, _: int, data: bytearray):

        raw = bytes(data)

        self._log_packet("RX", raw)
        self._learn(raw)

        try:
            # hunterjm protocol:
            # [port, power, speed]

            port = raw[0]

            if 1 <= port <= PORT_COUNT:

                power = bool(raw[1])
                speed = int(raw[2])

                self.data[port]["power"] = power
                self.data[port]["speed"] = speed

                self.async_set_updated_data(self.data)

        except Exception:
            _LOGGER.debug("Packet parse failed")

    # =====================================================
    # COMMANDS
    # =====================================================

    async def _write(self, payload: bytes):
        await self._ensure_connected()
        self._log_packet("TX", payload)
        await self._client.write_gatt_char(WRITE_UUID, payload)

    async def set_power(self, port: int, on: bool):
        payload = bytes([port, 1 if on else 0, 0])
        await self._write(payload)

    async def set_speed(self, port: int, speed: int):
        speed = max(0, min(100, speed))
        payload = bytes([port, 1, speed])
        await self._write(payload)

    # =====================================================
    # POLL (optional)
    # =====================================================

    async def _async_update_data(self):
        await self._ensure_connected()
        return self.data
