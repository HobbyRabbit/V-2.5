from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        ACInfinityPortSwitch(coordinator, port)
        for port in range(1, 9)
    ]

    async_add_entities(entities)


class ACInfinityPortSwitch(CoordinatorEntity, SwitchEntity):
    """One outlet port switch."""

    def __init__(self, coordinator, port: int):
        super().__init__(coordinator)

        self._port = port
        self._attr_name = f"AC Infinity Port {port}"
        self._attr_unique_id = f"{coordinator.mac}_port_{port}"
        self._attr_has_entity_name = True

    # -----------------------
    # STATE
    # -----------------------

    @property
    def is_on(self):
        return self.coordinator.data.get(self._port, False)

    # -----------------------
    # COMMANDS
    # -----------------------

    async def async_turn_on(self, **kwargs):
        await self.coordinator.set_port(self._port, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.coordinator.set_port(self._port, False)
        await self.coordinator.async_request_refresh()
