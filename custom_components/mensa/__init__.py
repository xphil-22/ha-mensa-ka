"""The Mensa integration."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL, add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CARD_URL_PATH,
    CARD_VERSION,
    CONF_PROVIDER,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import MensaConfigEntry, MensaCoordinator, MensaRuntimeData
from .providers import PROVIDERS, MensaApiError

_LOGGER = logging.getLogger(__name__)

CARD_JS_PATH = Path(__file__).parent / "www" / "mensa-card.js"
_CARD_REGISTERED_KEY = f"{DOMAIN}_card_registered"


async def _async_register_frontend_card(hass: HomeAssistant) -> None:
    """Serve the bundled Lovelace card and auto-register it as a resource.

    Runs once per hass lifetime so users don't have to add a Lovelace
    resource by hand. Skipped when http or frontend aren't set up (e.g. in
    unit tests, or a minimal hass without a UI), since there is nothing to
    serve the file from or register the resource with then.
    """
    if hass.data.get(_CARD_REGISTERED_KEY):
        return
    if getattr(hass, "http", None) is None or DATA_EXTRA_MODULE_URL not in hass.data:
        _LOGGER.debug("HTTP or frontend component not available, skipping card registration")
        return

    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL_PATH, str(CARD_JS_PATH), cache_headers=False)]
    )
    add_extra_js_url(hass, f"{CARD_URL_PATH}?v={CARD_VERSION}")
    hass.data[_CARD_REGISTERED_KEY] = True


async def async_setup_entry(hass: HomeAssistant, entry: MensaConfigEntry) -> bool:
    """Set up the Mensa integration from a config entry."""
    await _async_register_frontend_card(hass)

    provider = PROVIDERS[entry.data[CONF_PROVIDER]]
    session = async_get_clientsession(hass)
    try:
        canteens = await provider.async_get_canteens(session)
    except MensaApiError as err:
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = MensaCoordinator(hass, entry, provider, DEFAULT_UPDATE_INTERVAL)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = MensaRuntimeData(
        coordinator=coordinator,
        canteen_names={
            canteen.id: canteen.name
            for canteen in canteens
            if canteen.id in coordinator.canteen_ids
        },
        provider_name=provider.display_name,
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
