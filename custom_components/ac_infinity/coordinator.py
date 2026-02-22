from homeassistant.core import HomeAssistant


class ACInfinityCoordinator:
    def __init__(self, hass: HomeAssistant, mac: str):
        self.hass = hass
        self.mac = mac

        self.ports = {i: False for i in range(1, 9)}

    async def async_setup(self):
        # Connect BLE/USB here later
        return True

    async def set_port(self, port: int, state: bool):
        """
        Replace this with BLE/USB write
        """
        print(f"SET PORT {port} -> {state}")

        self.ports[port] = state

    def get_port(self, port: int):
        return self.ports.get(port, False)
