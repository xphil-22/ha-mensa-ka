"""Config flow for the Mensa integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import NumberSelector, NumberSelectorConfig, NumberSelectorMode

from .const import (
    CONF_CANTEENS,
    CONF_FORECAST_DAYS,
    CONF_PROVIDER,
    DEFAULT_FORECAST_DAYS,
    DOMAIN,
    MAX_FORECAST_DAYS,
    MIN_FORECAST_DAYS,
)
from .providers import PROVIDERS, Canteen, MensaApiError

_LOGGER = logging.getLogger(__name__)


async def _async_fetch_canteen_choices(hass: Any, provider_key: str) -> dict[str, str]:
    """Return a mapping of canteen id to display name, sorted by name."""
    session = async_get_clientsession(hass)
    canteens: list[Canteen] = await PROVIDERS[provider_key].async_get_canteens(session)
    return dict(sorted(((c.id, c.name) for c in canteens), key=lambda item: item[1]))


def _provider_schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_PROVIDER): vol.In(
                {key: provider.display_name for key, provider in PROVIDERS.items()}
            )
        }
    )


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


class MensaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the config flow for the Mensa integration.

    Multiple entries are allowed (one per provider, or several for the same
    provider tracking different canteens), so the first step picks a
    provider and the second step picks that provider's canteens.
    """

    VERSION = 1

    def __init__(self) -> None:
        self._provider_key: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user pick a data source."""
        if user_input is not None:
            self._provider_key = user_input[CONF_PROVIDER]
            return await self.async_step_canteens()

        return self.async_show_form(step_id="user", data_schema=_provider_schema())

    async def async_step_canteens(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user pick which canteens to track for the chosen provider."""
        assert self._provider_key is not None
        provider = PROVIDERS[self._provider_key]

        errors: dict[str, str] = {}
        try:
            choices = await _async_fetch_canteen_choices(self.hass, self._provider_key)
        except MensaApiError:
            _LOGGER.exception("Failed to fetch canteens from %s", provider.display_name)
            return self.async_abort(reason="cannot_connect")

        if user_input is not None:
            if not user_input[CONF_CANTEENS]:
                errors["base"] = "no_canteens_selected"
            else:
                return self.async_create_entry(
                    title=f"{provider.display_name} Mensen",
                    data={CONF_PROVIDER: self._provider_key, **user_input},
                )

        return self.async_show_form(
            step_id="canteens",
            data_schema=_canteens_schema(choices, defaults=[]),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> MensaOptionsFlow:
        return MensaOptionsFlow()


class MensaOptionsFlow(OptionsFlow):
    """Allow changing the tracked canteens and forecast window after setup."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        provider_key = self.config_entry.data[CONF_PROVIDER]
        provider = PROVIDERS[provider_key]

        errors: dict[str, str] = {}
        try:
            choices = await _async_fetch_canteen_choices(self.hass, provider_key)
        except MensaApiError:
            _LOGGER.exception("Failed to fetch canteens from %s", provider.display_name)
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
