"""Registry of available mensa data providers.

Adding a new source (e.g. OpenMensa) means adding one module here that
implements `Provider` and registering it in `PROVIDERS` below.
"""

from __future__ import annotations

from .base import MensaApiError, Provider
from .karlsruhe import KarlsruheProvider
from .models import Canteen, Meal, MealDay, Price

PROVIDERS: dict[str, Provider] = {
    "karlsruhe": KarlsruheProvider(),
}

__all__ = [
    "PROVIDERS",
    "Provider",
    "MensaApiError",
    "Canteen",
    "Meal",
    "MealDay",
    "Price",
]
