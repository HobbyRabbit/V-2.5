from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import ACInfinityCoordinator

DOMAIN = "ac_infinity"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    address = entry.data["address"]
    name = entry.title

    coordinator = ACInfinityCoordinator(hass, address, name)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(
        entry,
        ["switch", "fan", "sensor"],
    )

    return True
