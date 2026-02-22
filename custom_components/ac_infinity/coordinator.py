import asyncio
from bleak import BleakClient

WRITE_UUID = "0000fff3-0000-1000-8000-00805f9b34fb"  # Hunter uses this


class ACInfinityCoordinator:
    def __init__(self, hass, mac: str):
        self.hass = hass
        self.mac = mac
        self.client: BleakClient | None = None

        self.ports = {i: False for i in range(1, 9)}

    # --------------------------------------------------
    # BLE CONNECT
    # --------------------------------------------------

    async def async_setup(self):
        self.client = BleakClient(self.mac)
        await self.client.connect()

    # --------------------------------------------------
    # HUNTER PACKET FORMAT
    # --------------------------------------------------

    def _build_packet(self, port: int, value: int) -> bytearray:
        """
        HunterJM compatible command

        header  : AA 55
        length  : 05
        cmd     : 02 (set port)
        port    : 01-08
        value   : 0/1 (off/on)
        crc     : sum & 0xFF
        """

        payload = bytearray([
            0xAA,
            0x55,
            0x05,
            0x02,
            port,
            value,
        ])

        crc = sum(payload) & 0xFF
        payload.append(crc)

        return payload

    # --------------------------------------------------
    # PORT CONTROL
    # --------------------------------------------------

    async def set_port(self, port: int, state: bool):
        value = 1 if state else 0

        packet = self._build_packet(port, value)

        print(f"SEND → {packet.hex(' ')}")

        await self.client.write_gatt_char(WRITE_UUID, packet)

        self.ports[port] = state

    def get_port(self, port: int):
        return self.ports.get(port, False)
