"""The Karlsruher Mensen integration."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MensaApiError, async_get_canteens
from .const import CARD_URL_PATH, CARD_VERSION, DEFAULT_UPDATE_INTERVAL, DOMAIN, PLATFORMS
from .coordinator import MensaConfigEntry, MensaKaCoordinator, MensaRuntimeData

_LOGGER = logging.getLogger(__name__)

CARD_JS_PATH = Path(__file__).parent / "www" / "mensa-ka-card.js"
_CARD_REGISTERED_KEY = f"{DOMAIN}_card_registered"


async def _async_register_frontend_card(hass: HomeAssistant) -> None:
    """Serve the bundled Lovelace card and auto-register it as a resource.

    Runs once per hass lifetime so users don't have to add a Lovelace
    resource by hand. Skipped when the http component isn't loaded (e.g. in
    unit tests), since there is nothing to serve the file from then.
    """
    if hass.data.get(_CARD_REGISTERED_KEY):
        return
    if getattr(hass, "http", None) is None:
        _LOGGER.debug("HTTP component not available, skipping card registration")
        return

    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL_PATH, str(CARD_JS_PATH), cache_headers=False)]
    )
    add_extra_js_url(hass, f"{CARD_URL_PATH}?v={CARD_VERSION}")
    hass.data[_CARD_REGISTERED_KEY] = True


async def async_setup_entry(hass: HomeAssistant, entry: MensaConfigEntry) -> bool:
    """Set up the Karlsruher Mensen integration from a config entry."""
    await _async_register_frontend_card(hass)

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
