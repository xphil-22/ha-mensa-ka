"""Tests for custom_components.mensa.calendar helper functions."""

from datetime import date

from custom_components.mensa.calendar import _build_event, _format_description
from custom_components.mensa.providers.models import Meal, MealDay, Price

MEAL = Meal(
    id="m1",
    name="Chili sin Carne",
    line_name="Linie 1",
    meal_type="VEGAN",
    price=Price(student=360, employee=460, guest=520, pupil=400),
    allergens=["SO", "WE"],
    additives=["PHOSPHATE"],
    images=[],
)


def test_build_event_returns_none_for_empty_day():
    empty_day = MealDay(day=date(2026, 7, 8))
    assert _build_event("Mensa Test", empty_day) is None


def test_build_event_builds_all_day_event():
    meal_day = MealDay(day=date(2026, 7, 8), meals=[MEAL])
    event = _build_event("Mensa Test", meal_day)

    assert event is not None
    assert event.start == date(2026, 7, 8)
    assert event.end == date(2026, 7, 9)  # end is exclusive for all-day events
    assert "Mensa Test" in event.summary
    assert "1 meal" in event.summary
    assert "Chili sin Carne" in event.description


def test_format_description_groups_by_line_and_includes_labels():
    meal_day = MealDay(day=date(2026, 7, 8), meals=[MEAL])
    description = _format_description(meal_day)

    assert "Linie 1" in description
    assert "3,60" not in description  # price is formatted with a dot, not a comma
    assert "3.60" in description
    assert "Vegan" in description
    assert "Soya" in description
    assert "Wheat / gluten" in description
    assert "Phosphate" in description
