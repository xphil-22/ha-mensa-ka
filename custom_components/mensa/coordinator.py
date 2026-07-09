"""Data update coordinator for the Mensa integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import CONF_CANTEENS, CONF_FORECAST_DAYS, DEFAULT_FORECAST_DAYS, DOMAIN
from .providers.base import MensaApiError, Provider
from .providers.models import MealDay

_LOGGER = logging.getLogger(__name__)


def pick_current_meal_day(meal_days: list[MealDay]) -> MealDay | None:
    """Pick the meal day to expose as the current dashboard view."""
    today = dt_util.now().date()

    for meal_day in meal_days:
        if meal_day.day < today:
            continue
        if meal_day.day == today:
            if meal_day.meals:
                return meal_day
            continue
        if meal_day.meals:
            return meal_day

    return None


class MensaCoordinator(DataUpdateCoordinator[dict[str, list[MealDay]]]):
    """Fetches the meal plan of all configured canteens on a schedule."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        provider: Provider,
        update_interval: timedelta,
    ) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)
        self._entry = entry
        self._provider = provider
        self._session = async_get_clientsession(hass)

    @property
    def canteen_ids(self) -> list[str]:
        """Canteen ids currently configured for this entry."""
        return self._entry.options.get(
            CONF_CANTEENS, self._entry.data.get(CONF_CANTEENS, [])
        )

    @property
    def forecast_days(self) -> int:
        """Number of days ahead the meal plan is fetched for."""
        return self._entry.options.get(CONF_FORECAST_DAYS, DEFAULT_FORECAST_DAYS)

    async def _async_update_data(self) -> dict[str, list[MealDay]]:
        canteen_ids = self.canteen_ids
        today = date.today()
        days = [today + timedelta(days=offset) for offset in range(self.forecast_days)]

        try:
            return await self._provider.async_get_meal_plans(self._session, canteen_ids, days)
        except MensaApiError as err:
            raise UpdateFailed(str(err)) from err


@dataclass
class MensaRuntimeData:
    """Data stored on the config entry at runtime."""

    coordinator: MensaCoordinator
    canteen_names: dict[str, str]
    provider_name: str


type MensaConfigEntry = ConfigEntry[MensaRuntimeData]
