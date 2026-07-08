"""Config flow for the KIT Mensa integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import NumberSelector, NumberSelectorConfig, NumberSelectorMode

from .api import Canteen, MensaApiError, async_get_canteens
from .const import (
    CONF_CANTEENS,
    CONF_FORECAST_DAYS,
    DEFAULT_FORECAST_DAYS,
    DOMAIN,
    MAX_FORECAST_DAYS,
    MIN_FORECAST_DAYS,
)

_LOGGER = logging.getLogger(__name__)


async def _async_fetch_canteen_choices(hass: Any) -> dict[str, str]:
    """Return a mapping of canteen id to display name, sorted by name."""
    session = async_get_clientsession(hass)
    canteens: list[Canteen] = await async_get_canteens(session)
    return dict(sorted(((c.id, c.name) for c in canteens), key=lambda item: item[1]))


def _canteens_schema(choices: dict[str, str], defaults: list[str]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_CANTEENS, default=defaults): cv.multi_select(choices),
            vol.Required(
                CONF_FORECAST_DAYS, default=DEFAULT_FORECAST_DAYS
            ): NumberSelector(
                NumberSelectorConfig(
                    min=MIN_FORECAST_DAYS, max=MAX_FORECAST_DAYS, mode=NumberSelectorMode.BOX
                )
            ),
        }
    )


class MensaKaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the (single) config flow for the KIT Mensa integration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user pick which canteens to track."""
        # A single config entry manages all tracked canteens, see options flow.
        # (manifest.json also sets single_config_entry for HA versions that support it)
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        errors: dict[str, str] = {}
        try:
            choices = await _async_fetch_canteen_choices(self.hass)
        except MensaApiError:
            _LOGGER.exception("Failed to fetch canteens from the KIT Mensa API")
            return self.async_abort(reason="cannot_connect")

        if user_input is not None:
            if not user_input[CONF_CANTEENS]:
                errors["base"] = "no_canteens_selected"
            else:
                return self.async_create_entry(title="KIT Mensa", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_canteens_schema(choices, defaults=[]),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> MensaKaOptionsFlow:
        return MensaKaOptionsFlow()


class MensaKaOptionsFlow(OptionsFlow):
    """Allow changing the tracked canteens and forecast window after setup."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        try:
            choices = await _async_fetch_canteen_choices(self.hass)
        except MensaApiError:
            _LOGGER.exception("Failed to fetch canteens from the KIT Mensa API")
            return self.async_abort(reason="cannot_connect")

        current = self.config_entry.options.get(
            CONF_CANTEENS, self.config_entry.data.get(CONF_CANTEENS, [])
        )

        if user_input is not None:
            if not user_input[CONF_CANTEENS]:
                errors["base"] = "no_canteens_selected"
            else:
                return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_canteens_schema(choices, defaults=current),
            errors=errors,
        )
