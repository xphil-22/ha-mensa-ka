"""OpenMensa provider: async REST client for the community-run OpenMensa aggregator (openmensa.org).

OpenMensa covers ~1300 German canteens with community-maintained feeds of
varying freshness and completeness (no images, no discrete allergen codes,
price tiers other than "students" are frequently absent). Staleness is
detected reactively per canteen via `/canteens/{id}/days` rather than
pre-filtered in the canteen picker, since checking all ~1300 canteens'
freshness up front would mean over a thousand requests per config-flow render.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

import aiohttp

from .base import MensaApiError
from .models import Canteen, Meal, MealDay, Price

_LOGGER = logging.getLogger(__name__)

API_BASE = "https://openmensa.org/api/v2"

_REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)


async def _get(session: aiohttp.ClientSession, url: str, **params: Any) -> Any:
    """GET a JSON endpoint. Returns `None` for a 404 (unknown canteen/date)."""
    try:
        async with session.get(url, params=params, timeout=_REQUEST_TIMEOUT) as response:
            if response.status == 404:
                return None
            response.raise_for_status()
            return await response.json()
    except aiohttp.ClientError as err:
        raise MensaApiError(f"Could not reach {url}: {err}") from err


def _to_cents(amount: float | None) -> int | None:
    return None if amount is None else round(amount * 100)


def _parse_meal(raw: dict[str, Any]) -> Meal:
    prices = raw.get("prices") or {}
    return Meal(
        id=str(raw["id"]),
        name=raw["name"],
        line_name=raw.get("category") or "",
        meal_type="UNKNOWN",
        price=Price(
            student=_to_cents(prices.get("students")),
            employee=_to_cents(prices.get("employees")),
            guest=_to_cents(prices.get("others")),
            pupil=_to_cents(prices.get("pupils")),
        ),
        allergens=[],
        additives=[],
        images=[],
        notes=list(raw.get("notes") or []),
    )


class OpenMensaProvider:
    """Meal plans for any canteen registered on OpenMensa."""

    display_name = "OpenMensa"
    requires_search = True

    async def async_get_canteens(self, session: aiohttp.ClientSession) -> list[Canteen]:
        """Fetch the full paginated canteen catalog.

        Cities are appended to the name since many canteens share generic
        names like "Mensa" and are otherwise indistinguishable in a picker.
        """
        canteens: list[Canteen] = []
        page = 1
        total_pages = 1
        while page <= total_pages:
            url = f"{API_BASE}/canteens"
            try:
                async with session.get(
                    url, params={"page": page}, timeout=_REQUEST_TIMEOUT
                ) as response:
                    response.raise_for_status()
                    total_pages = int(response.headers.get("X-Total-Pages", 1))
                    data = await response.json()
            except aiohttp.ClientError as err:
                raise MensaApiError(f"Could not reach {url}: {err}") from err

            canteens.extend(
                Canteen(id=str(c["id"]), name=f"{c['name']} ({c['city']})") for c in data
            )
            page += 1

        return canteens

    async def _async_get_known_days(
        self, session: aiohttp.ClientSession, canteen_id: str
    ) -> dict[date, bool]:
        """Return the canteen's published days (date -> closed), if any."""
        data = await _get(session, f"{API_BASE}/canteens/{canteen_id}/days")
        if not data:
            return {}
        return {date.fromisoformat(entry["date"]): entry["closed"] for entry in data}

    async def async_get_meal_plans(
        self, session: aiohttp.ClientSession, canteen_ids: list[str], days: list[date]
    ) -> dict[str, list[MealDay]]:
        """Fetch the meal plan of every given canteen for every given day.

        Only fetches meals for days the canteen has published as open;
        unpublished or closed days are returned empty without a request.
        A canteen with no published days at all is logged as a likely stale
        feed instead of failing the whole update.
        """
        if not canteen_ids or not days:
            return {canteen_id: [] for canteen_id in canteen_ids}

        result: dict[str, list[MealDay]] = {}
        for canteen_id in canteen_ids:
            known_days = await self._async_get_known_days(session, canteen_id)
            if not known_days:
                _LOGGER.warning(
                    "Canteen %s has no published days on OpenMensa (feed may be stale)",
                    canteen_id,
                )

            meal_days = []
            for day in days:
                meal_day = MealDay(day=day)
                if known_days.get(day) is False:
                    raw_meals = await _get(
                        session, f"{API_BASE}/canteens/{canteen_id}/days/{day.isoformat()}/meals"
                    )
                    meal_day.meals.extend(_parse_meal(m) for m in raw_meals or [])
                meal_days.append(meal_day)

            result[canteen_id] = meal_days

        return result
