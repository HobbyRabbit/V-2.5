# /config/custom_components/ac_infinity/coordinator.py

from __future__ import annotations

import asyncio
import logging

from bleak import BleakClient
from bleak_retry_connector import establish_connection

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)

SERVICE_UUID = "0000fe61-0000-1000-8000-00805f9b34fb"


class ACInfinityCoordinator(DataUpdateCoordinator):
    """AC Infinity BLE coordinator with auto characteristic discovery."""

    def __init__(self, hass, mac: str):
        super().__init__(
            hass,
            _LOGGER,
            name="AC Infinity",
            update_interval=None,
        )

        self.mac = mac
        self.client: BleakClient | None = None
        self._write_char = None
        self._notify_char = None
        self._notify_event = asyncio.Event()
        self._last_payload: bytes | None = None

        # 8 ports default
        self.ports = {i: False for i in range(1, 9)}

    # -------------------------------------------------------
    # CONNECTION
    # -------------------------------------------------------

    async def _ensure_connected(self):
        """Connect + auto discover chars."""

        if self.client and self.client.is_connected:
            return

        self.client = await establish_connection(
            BleakClient,
            self.mac,
            name="ACInfinity",
        )

        services = await self.client.get_services()

        service = services.get_service(SERVICE_UUID)
        if not service:
            raise UpdateFailed("FE61 service not found")

        for char in service.characteristics:
            props = char.properties

            if not self._write_char and (
                "write" in props or "write-without-response" in props
            ):
                self._write_char = char

            if not self._notify_char and "notify" in props:
                self._notify_char = char

        if not self._write_char or not self._notify_char:
            raise UpdateFailed("write/notify characteristics not found")

        await self.client.start_notify(self._notify_char, self._notification)

        _LOGGER.debug(
            "Auto discovered chars write=%s notify=%s",
            self._write_char.uuid,
            self._notify_char.uuid,
        )

    # -------------------------------------------------------
    # NOTIFY
    # -------------------------------------------------------

    def _notification(self, _, data: bytearray):
        self._last_payload = bytes(data)
        self._notify_event.set()

    # -------------------------------------------------------
    # LOW LEVEL SEND
    # -------------------------------------------------------

    async def _send(self, payload: bytes, wait_reply=True):
        await self._ensure_connected()

        self._notify_event.clear()

        await self.client.write_gatt_char(
            self._write_char,
            payload,
            response=False,
        )

        if wait_reply:
            try:
                await asyncio.wait_for(self._notify_event.wait(), 3)
            except asyncio.TimeoutError:
                raise UpdateFailed("No BLE reply")

            return self._last_payload

    # -------------------------------------------------------
    # PUBLIC API
    # -------------------------------------------------------

    async def set_port(self, port: int, state: bool):
        """
        hunterjm compatible packet:
        [AA 55][port][01/00][checksum]
        """

        cmd = 0x01 if state else 0x00

        packet = bytearray([0xAA, 0x55, port, cmd])
        packet.append(sum(packet) & 0xFF)

        await self._send(packet)

        self.ports[port] = state

    async def toggle_port(self, port: int):
        await self.set_port(port, not self.ports[port])

    # -------------------------------------------------------
    # HA UPDATE
    # -------------------------------------------------------

    async def _async_update_data(self):
        """HA just needs state."""
        return self.ports
