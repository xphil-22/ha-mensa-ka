"""Tests for custom_components.mensa_ka.api."""

from datetime import date

import aiohttp
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.mensa_ka.api import (
    Canteen,
    MealDay,
    MensaApiError,
    async_get_canteens,
    async_get_meal_plans,
)
from custom_components.mensa_ka.const import API_URL


async def test_async_get_canteens(hass: HomeAssistant, aioclient_mock):
    aioclient_mock.post(
        API_URL,
        json={
            "data": {
                "getCanteens": [
                    {"id": "aaa", "name": "Mensa Adenauerring"},
                    {"id": "bbb", "name": "Mensa Moltke"},
                ]
            }
        },
    )

    canteens = await async_get_canteens(async_get_clientsession(hass))

    assert canteens == [
        Canteen(id="aaa", name="Mensa Adenauerring"),
        Canteen(id="bbb", name="Mensa Moltke"),
    ]


async def test_async_get_canteens_graphql_error(hass: HomeAssistant, aioclient_mock):
    aioclient_mock.post(API_URL, json={"errors": [{"message": "boom"}]})

    with pytest.raises(MensaApiError):
        await async_get_canteens(async_get_clientsession(hass))


async def test_async_get_canteens_unreachable(hass: HomeAssistant, aioclient_mock):
    aioclient_mock.post(API_URL, exc=aiohttp.ClientConnectionError("down"))

    with pytest.raises(MensaApiError):
        await async_get_canteens(async_get_clientsession(hass))


async def test_async_get_meal_plans_parses_lines_and_days(
    hass: HomeAssistant, aioclient_mock
):
    aioclient_mock.post(
        API_URL,
        json={
            "data": {
                "c0": {
                    "id": "aaa",
                    "lines": [
                        {
                            "name": "Linie 1",
                            "d0": [
                                {
                                    "id": "m1",
                                    "name": "Chili sin Carne",
                                    "mealType": "VEGAN",
                                    "price": {
                                        "student": 360,
                                        "employee": 460,
                                        "guest": 520,
                                        "pupil": 400,
                                    },
                                    "allergens": ["SO"],
                                    "additives": [],
                                }
                            ],
                            "d1": [],
                        },
                        {
                            "name": "Linie 2",
                            "d0": [],
                            "d1": [
                                {
                                    "id": "m2",
                                    "name": "Schnitzel",
                                    "mealType": "PORK",
                                    "price": {
                                        "student": 420,
                                        "employee": 520,
                                        "guest": 600,
                                        "pupil": 460,
                                    },
                                    "allergens": [],
                                    "additives": ["PHOSPHATE"],
                                }
                            ],
                        },
                    ],
                }
            }
        },
    )

    days = [date(2026, 7, 8), date(2026, 7, 9)]
    result = await async_get_meal_plans(async_get_clientsession(hass), ["aaa"], days)

    assert list(result.keys()) == ["aaa"]
    meal_days = result["aaa"]
    assert [d.day for d in meal_days] == days
    assert [m.name for m in meal_days[0].meals] == ["Chili sin Carne"]
    assert [m.name for m in meal_days[1].meals] == ["Schnitzel"]
    assert meal_days[1].meals[0].line_name == "Linie 2"


async def test_async_get_meal_plans_empty_input_returns_empty_days(
    hass: HomeAssistant, aioclient_mock
):
    result = await async_get_meal_plans(async_get_clientsession(hass), ["aaa"], [])
    assert result == {"aaa": []}


async def test_async_get_meal_plans_missing_canteen_returns_empty_days(
    hass: HomeAssistant, aioclient_mock
):
    aioclient_mock.post(API_URL, json={"data": {"c0": None}})

    result = await async_get_meal_plans(
        async_get_clientsession(hass), ["aaa"], [date(2026, 7, 8)]
    )

    assert result["aaa"] == [MealDay(day=date(2026, 7, 8))]
