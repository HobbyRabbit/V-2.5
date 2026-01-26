from __future__ import annotations
import logging
from typing import List

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import TEMP_CELSIUS, PERCENTAGE, REVOLUTIONS_PER_MINUTE

from .coordinator import ACInfinityDataUpdateCoordinator
from .device import ACInfinityController
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up AC Infinity sensors (RPM, temperature, humidity)."""
    address = entry.data["address"]
    data = hass.data[DOMAIN][address]
    controller: ACInfinityController = data["controller"]
    coordinator: ACInfinityDataUpdateCoordinator = data["coordinator"]

    sensors: List[ACInfinitySensor] = [
        ACInfinitySensor(controller, coordinator, "fan_rpm", "Fan RPM", REVOLUTIONS_PER_MINUTE),
        ACInfinitySensor(controller, coordinator, "temperature", "Temperature", TEMP_CELSIUS),
        ACInfinitySensor(controller, coordinator, "humidity", "Humidity", PERCENTAGE),
    ]

    async_add_entities(sensors, True)


class ACInfinitySensor(SensorEntity):
    """Representation of a single AC Infinity sensor."""

    def __init__(self, controller: ACInfinityController, coordinator: ACInfinityDataUpdateCoordinator, key: str, name: str, unit: str):
        self._controller = controller
        self._coordinator = coordinator
        self._key = key
        self._attr_name = f"{controller.address} {name}"
        self._attr_unique_id = f"{controller.address}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._state = None

    @property
    def native_value(self):
        """Return the current value."""
        value = self._controller.state.get(self._key)
        if isinstance(value, (int, float)):
            return value
        return None

    async def async_update(self):
        """Fetch latest state from the controller."""
        await self._coordinator.async_refresh_controller()
