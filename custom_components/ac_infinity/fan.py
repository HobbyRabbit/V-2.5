from __future__ import annotations

from homeassistant.components.fan import (
    FanEntity,
    FanEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


TOTAL_PORTS = 8


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        ACInfinityPortFan(coordinator, port)
        for port in range(1, TOTAL_PORTS + 1)
    ]

    async_add_entities(entities)


class ACInfinityPortFan(CoordinatorEntity, FanEntity):
    """Single combined Fan entity per port (power + speed)."""

    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )

    _attr_percentage_step = 10

    def __init__(self, coordinator, port: int) -> None:
        super().__init__(coordinator)

        self._port = port

        self._attr_name = f"AC Infinity Port {port}"
        self._attr_unique_id = f"ac_infinity_port_{port}"

    # -------------------------
    # Helpers
    # -------------------------

    def _state(self):
        """Safely get port state from coordinator."""
        return self.coordinator.data.get(self._port, {})

    # -------------------------
    # HA properties
    # -------------------------

    @property
    def is_on(self) -> bool:
        return self._state().get("power", False)

    @property
    def percentage(self) -> int:
        return self._state().get("speed", 0)

    # -------------------------
    # Commands
    # -------------------------

    async def async_turn_on(self, percentage: int | None = None, **kwargs):
        if percentage is None:
            percentage = 100

        await self.coordinator.async_set_speed(self._port, percentage)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_power(self._port, False)

    async def async_set_percentage(self, percentage: int):
        await self.coordinator.set_port_speed(self._port, percentage)
