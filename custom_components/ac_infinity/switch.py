from __future__ import annotations
import logging
from typing import List

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import ACInfinityDataUpdateCoordinator
from .device import ACInfinityController
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up AC Infinity switches for each port."""
    address = entry.data["address"]
    data = hass.data[DOMAIN][address]
    controller: ACInfinityController = data["controller"]
    coordinator: ACInfinityDataUpdateCoordinator = data["coordinator"]

    switches: List[ACInfinityPortSwitch] = [
        ACInfinityPortSwitch(controller, coordinator, port)
        for port in range(8)
    ]

    async_add_entities(switches, True)


class ACInfinityPortSwitch(SwitchEntity):
    """Representation of a single AC Infinity port as a switch."""

    def __init__(self, controller: ACInfinityController, coordinator: ACInfinityDataUpdateCoordinator, port: int):
        self._controller = controller
        self._coordinator = coordinator
        self._port = port
        self._attr_name = f"{controller.address} Port {port+1}"
        self._attr_unique_id = f"{controller.address}_port_{port+1}"
        self._state = controller.ports[port]

    @property
    def is_on(self) -> bool:
        """Return if the switch is on."""
        return self._controller.ports[self._port]

    async def async_turn_on(self, **kwargs):
        """Turn the port on."""
        await self._controller.set_port_enabled(self._port, True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the port off."""
        await self._controller.set_port_enabled(self._port, False)
        self.async_write_ha_state()

    async def async_update(self):
        """Fetch latest state from the controller."""
        await self._coordinator.async_refresh_controller()
