"""The Karlsruher Mensen integration."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MensaApiError, async_get_canteens
from .const import DEFAULT_UPDATE_INTERVAL, PLATFORMS
from .coordinator import MensaConfigEntry, MensaKaCoordinator, MensaRuntimeData


async def async_setup_entry(hass: HomeAssistant, entry: MensaConfigEntry) -> bool:
    """Set up the Karlsruher Mensen integration from a config entry."""
    session = async_get_clientsession(hass)
    try:
        canteens = await async_get_canteens(session)
    except MensaApiError as err:
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = MensaKaCoordinator(hass, entry, DEFAULT_UPDATE_INTERVAL)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = MensaRuntimeData(
        coordinator=coordinator,
        canteen_names={
            canteen.id: canteen.name
            for canteen in canteens
            if canteen.id in coordinator.canteen_ids
        },
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MensaConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(hass: HomeAssistant, entry: MensaConfigEntry) -> None:
    """Reload the entry when its options change (e.g. canteen selection)."""
    await hass.config_entries.async_reload(entry.entry_id)
