"""End-to-end test of setting up a config entry: coordinator + calendar entity."""

import aiohttp
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMockResponse

from custom_components.mensa_ka.const import API_URL, CONF_CANTEENS, CONF_FORECAST_DAYS, DOMAIN

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


async def test_setup_entry_creates_calendar_per_canteen(hass: HomeAssistant, aioclient_mock):
    _mock_api(aioclient_mock)

    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_CANTEENS: ["aaa"], CONF_FORECAST_DAYS: 3}
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    state = hass.states.get("calendar.mensa_adenauerring")
    assert state is not None

    # only the "aaa" canteen was configured, "bbb" must not get an entity
    assert hass.states.get("calendar.mensa_moltke") is None


async def test_setup_entry_not_ready_when_api_unreachable(hass: HomeAssistant, aioclient_mock):
    aioclient_mock.post(API_URL, exc=aiohttp.ClientConnectionError("down"))

    entry = MockConfigEntry(domain=DOMAIN, data={CONF_CANTEENS: ["aaa"]})
    entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload_entry(hass: HomeAssistant, aioclient_mock):
    _mock_api(aioclient_mock)

    entry = MockConfigEntry(domain=DOMAIN, data={CONF_CANTEENS: ["aaa"]})
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED
    # HA marks entities of an unloaded entry "unavailable" rather than removing them
    assert hass.states.get("calendar.mensa_adenauerring").state == "unavailable"
