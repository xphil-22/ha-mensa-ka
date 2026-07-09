"""Tests for custom_components.mensa.config_flow."""

from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mensa.config_flow import _filter_choices
from custom_components.mensa.const import CONF_CANTEENS, CONF_FORECAST_DAYS, CONF_PROVIDER, DOMAIN
from custom_components.mensa.providers.base import MensaApiError
from custom_components.mensa.providers.models import Canteen

FAKE_CANTEENS = [
    Canteen(id="aaa", name="Mensa Adenauerring"),
    Canteen(id="bbb", name="Mensa Moltke"),
]

_PATCH_TARGET = "custom_components.mensa.providers.karlsruhe.KarlsruheProvider.async_get_canteens"
_OPENMENSA_PATCH_TARGET = (
    "custom_components.mensa.providers.openmensa.OpenMensaProvider.async_get_canteens"
)


async def _start_canteens_step(hass: HomeAssistant):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    return await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PROVIDER: "karlsruhe"}
    )


async def test_user_flow_creates_entry(hass: HomeAssistant):
    with patch(_PATCH_TARGET, return_value=FAKE_CANTEENS):
        result = await _start_canteens_step(hass)
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "canteens"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_CANTEENS: ["aaa"], CONF_FORECAST_DAYS: 7},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_PROVIDER: "karlsruhe",
        CONF_CANTEENS: ["aaa"],
        CONF_FORECAST_DAYS: 7.0,
    }


async def test_user_flow_requires_at_least_one_canteen(hass: HomeAssistant):
    with patch(_PATCH_TARGET, return_value=FAKE_CANTEENS):
        result = await _start_canteens_step(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_CANTEENS: [], CONF_FORECAST_DAYS: 7},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "no_canteens_selected"}


async def test_user_flow_aborts_when_api_unreachable(hass: HomeAssistant):
    with patch(_PATCH_TARGET, side_effect=MensaApiError("down")):
        result = await _start_canteens_step(hass)

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"


async def test_user_flow_allows_multiple_entries(hass: HomeAssistant):
    # single_config_entry was intentionally dropped so a second provider (or a
    # second entry for the same provider) can be added alongside an existing one.
    MockConfigEntry(
        domain=DOMAIN, data={CONF_PROVIDER: "karlsruhe", CONF_CANTEENS: ["aaa"]}
    ).add_to_hass(hass)

    with patch(_PATCH_TARGET, return_value=FAKE_CANTEENS):
        result = await _start_canteens_step(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_CANTEENS: ["bbb"], CONF_FORECAST_DAYS: 7},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_user_flow_inserts_search_step_for_large_catalog_providers(hass: HomeAssistant):
    with patch(_OPENMENSA_PATCH_TARGET, return_value=FAKE_CANTEENS):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_PROVIDER: "openmensa"}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "search"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"search": "adenauerring"}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "canteens"


def test_filter_choices_matches_substring_case_insensitively():
    choices = {"1": "Mensa Adenauerring (Karlsruhe)", "2": "Mensa Rempartstraße (Freiburg)"}
    assert _filter_choices(choices, "freiburg") == {"2": "Mensa Rempartstraße (Freiburg)"}


def test_filter_choices_falls_back_to_full_set_when_nothing_matches():
    choices = {"1": "Mensa Adenauerring (Karlsruhe)"}
    assert _filter_choices(choices, "nonexistent city") == choices


def test_filter_choices_returns_everything_for_empty_search():
    choices = {"1": "Mensa Adenauerring (Karlsruhe)"}
    assert _filter_choices(choices, "") == choices


async def test_options_flow_updates_canteens(hass: HomeAssistant):
    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_PROVIDER: "karlsruhe", CONF_CANTEENS: ["aaa"]}
    )
    entry.add_to_hass(hass)

    with patch(_PATCH_TARGET, return_value=FAKE_CANTEENS):
        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] is FlowResultType.FORM

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {CONF_CANTEENS: ["aaa", "bbb"], CONF_FORECAST_DAYS: 5},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_CANTEENS: ["aaa", "bbb"], CONF_FORECAST_DAYS: 5.0}
