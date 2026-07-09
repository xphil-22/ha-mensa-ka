"""Data models shared by every mensa data provider."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class Canteen:
    """A canteen/cafeteria as returned by a provider's canteen listing."""

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
