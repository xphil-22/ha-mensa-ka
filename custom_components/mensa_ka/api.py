"""Minimal async GraphQL client for the KIT Mensa API (api.mensa-ka.de).

Only read-only queries are used (`getCanteens`, `getCanteen`). Mutations
(rating meals, uploading images) require a request signature whose API key
acquisition process is undocumented upstream and are intentionally not
implemented, see https://github.com/kronos-et-al/MensaApp/blob/main/doc/ApiAuth.md
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import aiohttp

from .const import API_URL

_LOGGER = logging.getLogger(__name__)

_REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)


class MensaApiError(Exception):
    """Raised when the Mensa API is unreachable or returns a GraphQL error."""


@dataclass
class Canteen:
    """A canteen/cafeteria as returned by `getCanteens`."""

    id: str
    name: str


@dataclass
class Price:
    """Price of a meal per price group, in cents."""

    student: int
    employee: int
    guest: int
    pupil: int


@dataclass
class Meal:
    """A single meal offered on one line on one day."""

    id: str
    name: str
    line_name: str
    meal_type: str
    price: Price
    allergens: list[str]
    additives: list[str]
    images: list[str]


@dataclass
class MealDay:
    """All meals offered by a canteen on a single day."""

    day: date
    meals: list[Meal] = field(default_factory=list)


_CANTEENS_QUERY = """
query {
  getCanteens {
    id
    name
  }
}
"""

_MEAL_FIELDS = """
    id
    name
    mealType
    price { student employee guest pupil }
    allergens
    additives
    images { url }
"""


async def _post(
    session: aiohttp.ClientSession, query: str
) -> dict[str, Any]:
    """Execute a GraphQL query and return its `data` payload."""
    try:
        async with session.post(
            API_URL, json={"query": query}, timeout=_REQUEST_TIMEOUT
        ) as response:
            response.raise_for_status()
            payload = await response.json()
    except aiohttp.ClientError as err:
        raise MensaApiError(f"Could not reach {API_URL}: {err}") from err

    if errors := payload.get("errors"):
        raise MensaApiError(f"GraphQL errors from {API_URL}: {errors}")

    return payload["data"]


async def async_get_canteens(session: aiohttp.ClientSession) -> list[Canteen]:
    """Fetch the list of all available canteens."""
    data = await _post(session, _CANTEENS_QUERY)
    return [Canteen(id=c["id"], name=c["name"]) for c in data["getCanteens"]]


def _build_meal_plan_query(canteen_ids: list[str], days: list[date]) -> str:
    """Build a single query fetching all lines' meals for every canteen/day.

    Canteens and days are addressed via aliases (`c<i>`, `d<j>`) so the whole
    forecast window for every configured canteen can be fetched in one
    request instead of one request per canteen per day.
    """
    canteen_blocks = []
    for i, canteen_id in enumerate(canteen_ids):
        day_fields = "\n".join(
            f'      d{j}: meals(date: "{day.isoformat()}") {{\n{_MEAL_FIELDS}      }}'
            for j, day in enumerate(days)
        )
        canteen_blocks.append(
            f'  c{i}: getCanteen(canteenId: "{canteen_id}") {{\n'
            f"    id\n"
            f"    lines {{\n"
            f"      name\n"
            f"{day_fields}\n"
            f"    }}\n"
            f"  }}"
        )
    return "query {\n" + "\n".join(canteen_blocks) + "\n}"


def _parse_meal(raw: dict[str, Any], line_name: str) -> Meal:
    price = raw["price"]
    return Meal(
        id=raw["id"],
        name=raw["name"],
        line_name=line_name,
        meal_type=raw["mealType"],
        price=Price(
            student=price["student"],
            employee=price["employee"],
            guest=price["guest"],
            pupil=price["pupil"],
        ),
        allergens=list(raw["allergens"]),
        additives=list(raw["additives"]),
        images=[image["url"] for image in raw.get("images", []) if "url" in image],
    )


async def async_get_meal_plans(
    session: aiohttp.ClientSession, canteen_ids: list[str], days: list[date]
) -> dict[str, list[MealDay]]:
    """Fetch the meal plan of every given canteen for every given day.

    Returns a mapping of canteen id to a list of `MealDay`, one per entry in
    `days`, in the same order.
    """
    if not canteen_ids or not days:
        return {canteen_id: [] for canteen_id in canteen_ids}

    query = _build_meal_plan_query(canteen_ids, days)
    data = await _post(session, query)

    result: dict[str, list[MealDay]] = {}
    for i, canteen_id in enumerate(canteen_ids):
        canteen_data = data[f"c{i}"]
        meal_days = [MealDay(day=day) for day in days]
        if canteen_data is None:
            _LOGGER.warning("Canteen %s no longer exists upstream", canteen_id)
            result[canteen_id] = meal_days
            continue

        for line in canteen_data["lines"]:
            for j, meal_day in enumerate(meal_days):
                meals = line.get(f"d{j}") or []
                meal_day.meals.extend(_parse_meal(m, line["name"]) for m in meals)

        result[canteen_id] = meal_days

    return result
