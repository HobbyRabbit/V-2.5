from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import ACInfinityCoordinator
from . import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):

    coordinator: ACInfinityCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        ACInfinityTemperatureSensor(coordinator),
        ACInfinityHumiditySensor(coordinator),
    ]

    async_add_entities(entities)


class ACInfinityTemperatureSensor(CoordinatorEntity, SensorEntity):

    _attr_name = "AC Infinity Temperature"
    _attr_native_unit_of_measurement = "°C"

    def __init__(self, coordinator):
        super().__init__(coordinator)

    @property
    def native_value(self):
        return self.coordinator.data.get("temperature")


class ACInfinityHumiditySensor(CoordinatorEntity, SensorEntity):

    _attr_name = "AC Infinity Humidity"
    _attr_native_unit_of_measurement = "%"

    def __init__(self, coordinator):
        super().__init__(coordinator)

    @property
    def native_value(self):
        return self.coordinator.data.get("humidity")
