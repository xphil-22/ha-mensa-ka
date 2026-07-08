"""Tests for custom_components.mensa_ka.config_flow."""

from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mensa_ka.api import Canteen, MensaApiError
from custom_components.mensa_ka.const import CONF_CANTEENS, CONF_FORECAST_DAYS, DOMAIN

FAKE_CANTEENS = [
    Canteen(id="aaa", name="Mensa Adenauerring"),
    Canteen(id="bbb", name="Mensa Moltke"),
]


async def test_user_flow_creates_entry(hass: HomeAssistant):
    with patch(
        "custom_components.mensa_ka.config_flow.async_get_canteens",
        return_value=FAKE_CANTEENS,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_CANTEENS: ["aaa"], CONF_FORECAST_DAYS: 7},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_CANTEENS: ["aaa"], CONF_FORECAST_DAYS: 7.0}


async def test_user_flow_requires_at_least_one_canteen(hass: HomeAssistant):
    with patch(
        "custom_components.mensa_ka.config_flow.async_get_canteens",
        return_value=FAKE_CANTEENS,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_CANTEENS: [], CONF_FORECAST_DAYS: 7},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "no_canteens_selected"}


async def test_user_flow_aborts_when_api_unreachable(hass: HomeAssistant):
    with patch(
        "custom_components.mensa_ka.config_flow.async_get_canteens",
        side_effect=MensaApiError("down"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"


async def test_user_flow_aborts_when_already_configured(hass: HomeAssistant):
    # manifest.json sets single_config_entry, so HA's flow manager aborts this
    # itself (reason "single_instance_allowed") before our own fallback check
    # (which produces "already_configured" on HA versions without that key)
    # ever runs.
    MockConfigEntry(domain=DOMAIN, data={CONF_CANTEENS: ["aaa"]}).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_options_flow_updates_canteens(hass: HomeAssistant):
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_CANTEENS: ["aaa"]})
    entry.add_to_hass(hass)

    with patch(
        "custom_components.mensa_ka.config_flow.async_get_canteens",
        return_value=FAKE_CANTEENS,
    ):
        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] is FlowResultType.FORM

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {CONF_CANTEENS: ["aaa", "bbb"], CONF_FORECAST_DAYS: 5},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_CANTEENS: ["aaa", "bbb"], CONF_FORECAST_DAYS: 5.0}
