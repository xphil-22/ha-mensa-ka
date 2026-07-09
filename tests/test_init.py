"""End-to-end test of setting up a config entry: coordinator + entities."""

import aiohttp
from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMockResponse

from custom_components.mensa.const import (
    CARD_URL_PATH,
    CARD_VERSION,
    CONF_CANTEENS,
    CONF_FORECAST_DAYS,
    CONF_PROVIDER,
    DOMAIN,
)
from custom_components.mensa.providers.karlsruhe import API_URL

CANTEENS_RESPONSE = {
    "data": {
        "getCanteens": [
            {"id": "aaa", "name": "Mensa Adenauerring"},
            {"id": "bbb", "name": "Mensa Moltke"},
        ]
    }
}

MEAL_PLAN_RESPONSE = {
    "data": {
        "c0": {"id": "aaa", "lines": []},
    }
}


def _mock_api(aioclient_mock) -> None:
    """Answer getCanteens with the canteen list, everything else as an empty meal plan."""

    async def respond(method, url, data):
        payload = CANTEENS_RESPONSE if "getCanteens" in data["query"] else MEAL_PLAN_RESPONSE
        return AiohttpClientMockResponse(method, url, json=payload)

    aioclient_mock.post(API_URL, side_effect=respond)


async def test_setup_entry_creates_calendar_and_sensor_per_canteen(
    hass: HomeAssistant, aioclient_mock
):
    _mock_api(aioclient_mock)

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_PROVIDER: "karlsruhe", CONF_CANTEENS: ["aaa"], CONF_FORECAST_DAYS: 3},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert hass.states.get("calendar.mensa_adenauerring") is not None
    assert hass.states.get("sensor.mensa_adenauerring_meal_plan") is not None

    # Only the configured canteen gets entities.
    assert hass.states.get("calendar.mensa_moltke") is None
    assert hass.states.get("sensor.mensa_moltke_meal_plan") is None


async def test_setup_entry_registers_lovelace_card(hass: HomeAssistant, aioclient_mock):
    _mock_api(aioclient_mock)
    assert await async_setup_component(hass, "http", {})
    # Avoids depending on the (large, separately packaged) home-assistant-frontend
    # component just to exercise add_extra_js_url's storage.
    hass.data[DATA_EXTRA_MODULE_URL] = set()

    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_PROVIDER: "karlsruhe", CONF_CANTEENS: ["aaa"]}
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert f"{CARD_URL_PATH}?v={CARD_VERSION}" in hass.data[DATA_EXTRA_MODULE_URL]


async def test_setup_entry_not_ready_when_api_unreachable(hass: HomeAssistant, aioclient_mock):
    aioclient_mock.post(API_URL, exc=aiohttp.ClientConnectionError("down"))

    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_PROVIDER: "karlsruhe", CONF_CANTEENS: ["aaa"]}
    )
    entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload_entry(hass: HomeAssistant, aioclient_mock):
    _mock_api(aioclient_mock)

    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_PROVIDER: "karlsruhe", CONF_CANTEENS: ["aaa"]}
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED
    # HA marks entities of an unloaded entry "unavailable" rather than removing them.
    assert hass.states.get("calendar.mensa_adenauerring").state == "unavailable"
    assert hass.states.get("sensor.mensa_adenauerring_meal_plan").state == "unavailable"
