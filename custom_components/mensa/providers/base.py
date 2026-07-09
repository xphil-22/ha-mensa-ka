"""Shared provider protocol for the Mensa integration.

A `Provider` is a source of canteens and meal plans (e.g. one university's own
API, or an aggregator like OpenMensa). Adding support for a new source means
adding one new module implementing this protocol and registering it in
`providers/__init__.py`, without touching the config flow, coordinator, or
entity platforms.
"""

from __future__ import annotations

from datetime import date
from typing import Protocol

import aiohttp

from .models import Canteen, MealDay


class MensaApiError(Exception):
    """Raised when a mensa data source is unreachable or returns an error."""


class Provider(Protocol):
    """A source of canteens and meal plans."""

    display_name: str

    # Set for providers whose canteen catalog is too large for a plain
    # multi-select (e.g. OpenMensa's ~1300 canteens): the config flow inserts
    # an extra text-filter step before the canteen picker.
    requires_search: bool = False

    async def async_get_canteens(self, session: aiohttp.ClientSession) -> list[Canteen]:
        """Fetch the list of all available canteens."""
        ...

    async def async_get_meal_plans(
        self, session: aiohttp.ClientSession, canteen_ids: list[str], days: list[date]
    ) -> dict[str, list[MealDay]]:
        """Fetch the meal plan of every given canteen for every given day."""
        ...
