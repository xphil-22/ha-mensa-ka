"""Sensor platform for the Karlsruher Mensen integration."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import Meal, MealDay
from .const import (
    ADDITIVE_LABELS,
    ALLERGEN_LABELS,
    DOMAIN,
    FOOD_TYPE_ICONS,
    FOOD_TYPE_LABELS,
)
from .coordinator import MensaConfigEntry, MensaKaCoordinator, pick_current_meal_day


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MensaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one meal plan sensor per configured canteen."""
    runtime_data = entry.runtime_data
    async_add_entities(
        MensaKaSensor(runtime_data.coordinator, canteen_id, canteen_name)
        for canteen_id, canteen_name in runtime_data.canteen_names.items()
    )


def _food_type_icon(meal_type: str) -> str:
    normalized = meal_type.lower()
    if normalized == "vegan":
        return FOOD_TYPE_ICONS["vegan"]
    if normalized == "vegetarian":
        return FOOD_TYPE_ICONS["vegetarian"]
    return FOOD_TYPE_ICONS["default"]


def _meal_to_attr(meal: Meal) -> dict:
    """Convert a meal into stable sensor attributes."""
    return {
        "name": meal.name,
        "diet_label": FOOD_TYPE_LABELS.get(meal.meal_type, FOOD_TYPE_LABELS["UNKNOWN"]),
        "diet_icon": _food_type_icon(meal.meal_type),
        "price_student": meal.price.student / 100,
        "price_employee": meal.price.employee / 100,
        "price_guest": meal.price.guest / 100,
        "price_pupil": meal.price.pupil / 100,
        "allergens": [
            ALLERGEN_LABELS[allergen]
            for allergen in meal.allergens
            if allergen in ALLERGEN_LABELS
        ],
        "additives": [
            ADDITIVE_LABELS[additive]
            for additive in meal.additives
            if additive in ADDITIVE_LABELS
        ],
        "image_url": meal.images[0] if meal.images else None,
        "images": meal.images,
    }


def _group_by_line(meal_day: MealDay) -> list[dict]:
    """Group meals by serving line for compact dashboard attributes."""
    grouped: dict[str, list[dict]] = {}
    for meal in meal_day.meals:
        grouped.setdefault(meal.line_name, []).append(_meal_to_attr(meal))
    return [
        {"line": line_name, "meals": meals}
        for line_name, meals in grouped.items()
    ]


class MensaKaSensor(CoordinatorEntity[MensaKaCoordinator], SensorEntity):
    """Sensor entity exposing the selected meal day of one canteen."""

    _attr_has_entity_name = True
    _attr_name = "Meal plan"
    _attr_native_unit_of_measurement = "meals"

    def __init__(
        self, coordinator: MensaKaCoordinator, canteen_id: str, canteen_name: str
    ) -> None:
        super().__init__(coordinator)
        self._canteen_id = canteen_id
        self._attr_unique_id = f"{DOMAIN}_{canteen_id}_sensor"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, canteen_id)},
            name=canteen_name,
            manufacturer="Studierendenwerk Karlsruhe",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> int:
        """Return the number of meals for the selected meal day."""
        meal_day = pick_current_meal_day(self.coordinator.data.get(self._canteen_id, []))
        if meal_day is None:
            return 0
        return len(meal_day.meals)

    @property
    def extra_state_attributes(self) -> dict:
        """Return the selected day and grouped meals."""
        meal_day = pick_current_meal_day(self.coordinator.data.get(self._canteen_id, []))
        if meal_day is None:
            return {"lines": []}

        return {
            "day": meal_day.day.isoformat(),
            "lines": _group_by_line(meal_day),
        }
