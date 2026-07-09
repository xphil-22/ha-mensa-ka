"""Tests for custom_components.mensa.sensor and shared meal-day helpers."""

from datetime import date, datetime
from unittest.mock import patch

from custom_components.mensa.coordinator import pick_current_meal_day
from custom_components.mensa.providers.models import Meal, MealDay, Price
from custom_components.mensa.sensor import _group_by_line, _meal_to_attr


def _meal(
    *,
    meal_id: str,
    name: str,
    line_name: str,
    meal_type: str = "VEGAN",
    student: int = 360,
    employee: int = 460,
    guest: int = 520,
    pupil: int = 400,
    allergens: list[str] | None = None,
    additives: list[str] | None = None,
    images: list[str] | None = None,
) -> Meal:
    return Meal(
        id=meal_id,
        name=name,
        line_name=line_name,
        meal_type=meal_type,
        price=Price(
            student=student,
            employee=employee,
            guest=guest,
            pupil=pupil,
        ),
        allergens=allergens or [],
        additives=additives or [],
        images=images or [],
    )


def test_meal_to_attr_resolves_labels_icons_prices_and_annotations():
    meal = _meal(
        meal_id="m1",
        name="Chili sin Carne",
        line_name="Linie 1",
        meal_type="VEGAN",
        allergens=["SO", "WE", "UNKNOWN"],
        additives=["PHOSPHATE", "UNKNOWN"],
        images=["https://api.mensa-ka.de/image/example.jpg"],
    )

    assert _meal_to_attr(meal) == {
        "name": "Chili sin Carne",
        "diet_label": "Vegan",
        "diet_icon": "\U0001f331",
        "price_student": 3.6,
        "price_employee": 4.6,
        "price_guest": 5.2,
        "price_pupil": 4.0,
        "allergens": ["Soya", "Wheat / gluten"],
        "additives": ["Phosphate"],
        "image_url": "https://api.mensa-ka.de/image/example.jpg",
        "images": ["https://api.mensa-ka.de/image/example.jpg"],
    }


def test_meal_to_attr_uses_default_icon_and_unknown_label_for_unmapped_food_type():
    meal = _meal(
        meal_id="m2",
        name="Mystery Meal",
        line_name="Linie 3",
        meal_type="NOT_A_REAL_TYPE",
    )

    assert _meal_to_attr(meal)["diet_label"] == "Unknown"
    assert _meal_to_attr(meal)["diet_icon"] == "\U0001f356"
    assert _meal_to_attr(meal)["image_url"] is None
    assert _meal_to_attr(meal)["images"] == []


def test_group_by_line_groups_meals_in_line_structure():
    meal_day = MealDay(
        day=date(2026, 7, 9),
        meals=[
            _meal(
                meal_id="m1",
                name="Chili sin Carne",
                line_name="Linie 1",
                meal_type="VEGAN",
                images=["https://api.mensa-ka.de/image/chili.jpg"],
            ),
            _meal(
                meal_id="m2",
                name="Pasta al Pomodoro",
                line_name="Linie 1",
                meal_type="VEGETARIAN",
                student=330,
                employee=430,
                guest=490,
                pupil=370,
            ),
            _meal(
                meal_id="m3",
                name="Rindergulasch",
                line_name="Linie 2",
                meal_type="BEEF",
                allergens=["EI"],
                additives=["ALCOHOL"],
            ),
        ],
    )

    assert _group_by_line(meal_day) == [
        {
            "line": "Linie 1",
            "meals": [
                {
                    "name": "Chili sin Carne",
                    "diet_label": "Vegan",
                    "diet_icon": "\U0001f331",
                    "price_student": 3.6,
                    "price_employee": 4.6,
                    "price_guest": 5.2,
                    "price_pupil": 4.0,
                    "allergens": [],
                    "additives": [],
                    "image_url": "https://api.mensa-ka.de/image/chili.jpg",
                    "images": ["https://api.mensa-ka.de/image/chili.jpg"],
                },
                {
                    "name": "Pasta al Pomodoro",
                    "diet_label": "Vegetarian",
                    "diet_icon": "\U0001f955",
                    "price_student": 3.3,
                    "price_employee": 4.3,
                    "price_guest": 4.9,
                    "price_pupil": 3.7,
                    "allergens": [],
                    "additives": [],
                    "image_url": None,
                    "images": [],
                },
            ],
        },
        {
            "line": "Linie 2",
            "meals": [
                {
                    "name": "Rindergulasch",
                    "diet_label": "Beef",
                    "diet_icon": "\U0001f356",
                    "price_student": 3.6,
                    "price_employee": 4.6,
                    "price_guest": 5.2,
                    "price_pupil": 4.0,
                    "allergens": ["Eggs"],
                    "additives": ["May contain alcohol"],
                    "image_url": None,
                    "images": [],
                }
            ],
        },
    ]


def test_pick_current_meal_day_prefers_today_when_today_has_meals():
    meal_days = [
        MealDay(day=date(2026, 7, 8), meals=[_meal(meal_id="past", name="Past", line_name="L1")]),
        MealDay(day=date(2026, 7, 9), meals=[_meal(meal_id="today", name="Today", line_name="L1")]),
        MealDay(day=date(2026, 7, 10), meals=[_meal(meal_id="next", name="Next", line_name="L1")]),
    ]

    with patch(
        "custom_components.mensa.coordinator.dt_util.now",
        return_value=datetime(2026, 7, 9, 8, 0, 0),
    ):
        assert pick_current_meal_day(meal_days) == meal_days[1]


def test_pick_current_meal_day_uses_next_non_empty_day_when_today_is_empty():
    meal_days = [
        MealDay(day=date(2026, 7, 9), meals=[]),
        MealDay(day=date(2026, 7, 10), meals=[_meal(meal_id="next", name="Next", line_name="L1")]),
        MealDay(
            day=date(2026, 7, 11),
            meals=[_meal(meal_id="later", name="Later", line_name="L2")],
        ),
    ]

    with patch(
        "custom_components.mensa.coordinator.dt_util.now",
        return_value=datetime(2026, 7, 9, 8, 0, 0),
    ):
        assert pick_current_meal_day(meal_days) == meal_days[1]


def test_pick_current_meal_day_returns_none_when_all_days_are_empty():
    meal_days = [
        MealDay(day=date(2026, 7, 9), meals=[]),
        MealDay(day=date(2026, 7, 10), meals=[]),
        MealDay(day=date(2026, 7, 11), meals=[]),
    ]

    with patch(
        "custom_components.mensa.coordinator.dt_util.now",
        return_value=datetime(2026, 7, 9, 8, 0, 0),
    ):
        assert pick_current_meal_day(meal_days) is None
