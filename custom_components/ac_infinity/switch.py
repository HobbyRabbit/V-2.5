from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

PORTS = 8


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        ACInfinityPortSwitch(coordinator, i)
        for i in range(PORTS)
    ]

    async_add_entities(entities)


class ACInfinityPortSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, index):
        super().__init__(coordinator)
        self.index = index
        self._attr_name = f"AC Infinity Port {index+1} Power"

    @property
    def is_on(self):
        return self.coordinator.data["power"][self.index]

    async def async_turn_on(self):
        await self.coordinator.set_power(self.index, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self):
        await self.coordinator.set_power(self.index, False)
        await self.coordinator.async_request_refresh()
