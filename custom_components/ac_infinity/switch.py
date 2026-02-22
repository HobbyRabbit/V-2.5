from homeassistant.components.switch import SwitchEntity

from .const import DOMAIN, PORT_COUNT


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        ACInfinityPortSwitch(coordinator, port)
        for port in range(1, PORT_COUNT + 1)
    ]

    async_add_entities(entities)


class ACInfinityPortSwitch(SwitchEntity):
    def __init__(self, coordinator, port):
        self.coordinator = coordinator
        self.port = port

        self._attr_name = f"AC Infinity Port {port}"
        self._attr_unique_id = f"ac_infinity_port_{port}"

    @property
    def is_on(self):
        return self.coordinator.get_port(self.port)

    async def async_turn_on(self, **kwargs):
        await self.coordinator.set_port(self.port, True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        await self.coordinator.set_port(self.port, False)
        self.async_write_ha_state()
