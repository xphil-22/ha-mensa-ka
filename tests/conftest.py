"""Fixtures for the Mensa integration tests."""

import pycares
import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(scope="session", autouse=True)
def _warm_up_pycares_shutdown_thread():
    """Pre-start pycares' background channel-shutdown daemon thread.

    homeassistant's aiohttp client uses pycares (via aiodns) for DNS
    resolution. Destroying the first resolver channel lazily spawns a
    permanent daemon thread inside pycares. Without this, the first test
    that touches a (real or aioclient_mock) ClientSession spawns that
    thread and gets incorrectly flagged by verify_cleanup as leaking it.
    """
    channel = pycares.Channel()
    del channel


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading this custom component in every test."""
    yield
