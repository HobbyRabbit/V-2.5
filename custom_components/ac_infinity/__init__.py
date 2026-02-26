from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import ACInfinityCoordinator

PLATFORMS = ["switch", "fan"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    mac = entry.data["mac"]
    name = entry.title  # <- REQUIRED

    coordinator = ACInfinityCoordinator(
        hass,
        mac,
        name,   # ← THIS WAS MISSING
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault("ac_infinity", {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data["ac_infinity"].pop(entry.entry_id)

    return unload_ok
