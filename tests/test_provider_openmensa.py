"""Tests for custom_components.mensa.providers.openmensa."""

from datetime import date

import aiohttp
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.mensa.providers.base import MensaApiError
from custom_components.mensa.providers.models import Canteen, MealDay
from custom_components.mensa.providers.openmensa import API_BASE, OpenMensaProvider

provider = OpenMensaProvider()


async def test_async_get_canteens_single_page(hass: HomeAssistant, aioclient_mock):
    aioclient_mock.get(
        f"{API_BASE}/canteens",
        params={"page": 1},
        json=[
            {"id": 1, "name": "Mensa Adenauerring", "city": "Karlsruhe"},
            {"id": 2, "name": "Mensa Moltke", "city": "Karlsruhe"},
        ],
        headers={"X-Total-Pages": "1"},
    )

    canteens = await provider.async_get_canteens(async_get_clientsession(hass))

    assert canteens == [
        Canteen(id="1", name="Mensa Adenauerring (Karlsruhe)"),
        Canteen(id="2", name="Mensa Moltke (Karlsruhe)"),
    ]


async def test_async_get_canteens_paginates(hass: HomeAssistant, aioclient_mock):
    aioclient_mock.get(
        f"{API_BASE}/canteens",
        params={"page": 1},
        json=[{"id": 1, "name": "Mensa A", "city": "Freiburg"}],
        headers={"X-Total-Pages": "2"},
    )
    aioclient_mock.get(
        f"{API_BASE}/canteens",
        params={"page": 2},
        json=[{"id": 2, "name": "Mensa B", "city": "Stuttgart"}],
        headers={"X-Total-Pages": "2"},
    )

    canteens = await provider.async_get_canteens(async_get_clientsession(hass))

    assert canteens == [
        Canteen(id="1", name="Mensa A (Freiburg)"),
        Canteen(id="2", name="Mensa B (Stuttgart)"),
    ]


async def test_async_get_canteens_unreachable(hass: HomeAssistant, aioclient_mock):
    aioclient_mock.get(
        f"{API_BASE}/canteens",
        params={"page": 1},
        exc=aiohttp.ClientConnectionError("down"),
    )

    with pytest.raises(MensaApiError):
        await provider.async_get_canteens(async_get_clientsession(hass))


async def test_async_get_meal_plans_fetches_open_days_only(
    hass: HomeAssistant, aioclient_mock
):
    aioclient_mock.get(
        f"{API_BASE}/canteens/aaa/days",
        json=[
            {"date": "2026-07-09", "closed": False},
            {"date": "2026-07-10", "closed": True},
        ],
    )
    aioclient_mock.get(
        f"{API_BASE}/canteens/aaa/days/2026-07-09/meals",
        json=[
            {
                "id": 1,
                "name": "Gelbes Linsen-Kokos-Curry",
                "category": "Linie 2 Vegane Linie",
                "prices": {"students": 3.8, "employees": None, "pupils": None, "others": None},
                "notes": ["Sellerie", "vegan"],
            }
        ],
    )
    # 2026-07-10 is closed - if the provider tried to fetch meals for it,
    # aioclient_mock would raise for the unmocked request.

    days = [date(2026, 7, 9), date(2026, 7, 10)]
    result = await provider.async_get_meal_plans(async_get_clientsession(hass), ["aaa"], days)

    meal_days = result["aaa"]
    assert [d.day for d in meal_days] == days
    assert meal_days[1].meals == []

    meal = meal_days[0].meals[0]
    assert meal.name == "Gelbes Linsen-Kokos-Curry"
    assert meal.line_name == "Linie 2 Vegane Linie"
    assert meal.price.student == 380
    assert meal.price.employee is None
    assert meal.price.guest is None
    assert meal.price.pupil is None
    assert meal.notes == ["Sellerie", "vegan"]
    assert meal.allergens == []
    assert meal.meal_type == "UNKNOWN"


async def test_async_get_meal_plans_handles_stale_feed_without_published_days(
    hass: HomeAssistant, aioclient_mock
):
    aioclient_mock.get(f"{API_BASE}/canteens/dead/days", json=[])

    days = [date(2026, 7, 9), date(2026, 7, 10)]
    result = await provider.async_get_meal_plans(async_get_clientsession(hass), ["dead"], days)

    assert result["dead"] == [MealDay(day=day) for day in days]


async def test_async_get_meal_plans_empty_input_returns_empty_days(
    hass: HomeAssistant, aioclient_mock
):
    result = await provider.async_get_meal_plans(async_get_clientsession(hass), ["aaa"], [])
    assert result == {"aaa": []}
