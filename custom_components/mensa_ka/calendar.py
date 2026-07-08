"""Calendar platform for the KIT Mensa integration.

Each configured canteen gets one calendar entity with one all-day event per
day it serves meals. The event description lists every meal offered that
day, grouped by line, with price, food type and allergen/additive info.
"""

from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .api import Meal, MealDay
from .const import ADDITIVE_LABELS, ALLERGEN_LABELS, DOMAIN, FOOD_TYPE_LABELS
from .coordinator import MensaConfigEntry, MensaKaCoordinator, pick_current_meal_day

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MensaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one calendar entity per configured canteen."""
    runtime_data = entry.runtime_data
    async_add_entities(
        MensaKaCalendar(runtime_data.coordinator, canteen_id, canteen_name)
        for canteen_id, canteen_name in runtime_data.canteen_names.items()
    )


def _format_meal(meal: Meal) -> str:
    parts = [f"- **{meal.name}** ({meal.price.student / 100:.2f} €)"]
    food_type = FOOD_TYPE_LABELS.get(meal.meal_type, meal.meal_type)
    tags = [food_type]
    tags.extend(ALLERGEN_LABELS.get(a, a) for a in meal.allergens)
    tags.extend(ADDITIVE_LABELS.get(a, a) for a in meal.additives)
    if tags:
        parts.append(f"  {', '.join(tags)}")
    return "\n".join(parts)


def _format_description(meal_day: MealDay) -> str:
    lines_by_name: dict[str, list[Meal]] = {}
    for meal in meal_day.meals:
        lines_by_name.setdefault(meal.line_name, []).append(meal)

    blocks = []
    for line_name, meals in lines_by_name.items():
        meal_lines = "\n".join(_format_meal(meal) for meal in meals)
        blocks.append(f"**{line_name}**\n{meal_lines}")
    return "\n\n".join(blocks)


def _build_event(canteen_name: str, meal_day: MealDay) -> CalendarEvent | None:
    if not meal_day.meals:
        return None
    meal_count = len(meal_day.meals)
    meal_label = "meal" if meal_count == 1 else "meals"
    return CalendarEvent(
        start=meal_day.day,
        end=meal_day.day,
        summary=f"{canteen_name} ({meal_count} {meal_label})",
        description=_format_description(meal_day),
    )


class MensaKaCalendar(CoordinatorEntity[MensaKaCoordinator], CalendarEntity):
    """Calendar entity exposing the meal plan of a single canteen."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self, coordinator: MensaKaCoordinator, canteen_id: str, canteen_name: str
    ) -> None:
        super().__init__(coordinator)
        self._canteen_id = canteen_id
        self._canteen_name = canteen_name
        self._attr_unique_id = f"{DOMAIN}_{canteen_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, canteen_id)},
            name=canteen_name,
            manufacturer="Studierendenwerk Karlsruhe",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def event(self) -> CalendarEvent | None:
        """Return the current or next upcoming event."""
        meal_day = pick_current_meal_day(self.coordinator.data.get(self._canteen_id, []))
        if meal_day is None:
            return None
        return _build_event(self._canteen_name, meal_day)

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Return all events within the given date range."""
        start = dt_util.as_local(start_date).date()
        end = dt_util.as_local(end_date).date()
        events = []
        for meal_day in self.coordinator.data.get(self._canteen_id, []):
            if not start <= meal_day.day < end:
                continue
            if event := _build_event(self._canteen_name, meal_day):
                events.append(event)
        return events
