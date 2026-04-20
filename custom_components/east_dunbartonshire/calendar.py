"""Calendar platform for the East Dunbartonshire integration."""

from __future__ import annotations

import datetime

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BinCollection, EastDunbartonshireCoordinator
from .school_holidays import SchoolHolidayEvent, SchoolHolidaysCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN]
    entities: list[CalendarEntity] = [BinCollectionsCalendar(data[entry.entry_id], entry)]
    if "school_holidays" in data:
        entities += [
            SchoolHolidaysCalendar(data["school_holidays"]),
            InServiceDaysCalendar(data["school_holidays"]),
        ]
    async_add_entities(entities)


# ---------------------------------------------------------------------------
# Bin collections
# ---------------------------------------------------------------------------


class BinCollectionsCalendar(CoordinatorEntity[EastDunbartonshireCoordinator], CalendarEntity):
    _attr_has_entity_name = True
    _attr_name = "Bin collections"

    def __init__(self, coordinator: EastDunbartonshireCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_calendar"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
        )

    @property
    def event(self) -> CalendarEvent | None:
        if not self.coordinator.data:
            return None
        today = datetime.date.today()
        upcoming = [c for c in self.coordinator.data if c.next_date >= today]
        if not upcoming:
            return None
        return _make_bin_event(min(upcoming, key=lambda c: c.next_date))

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
    ) -> list[CalendarEvent]:
        if not self.coordinator.data:
            return []
        start = start_date.date()
        end = end_date.date()
        return [_make_bin_event(c) for c in self.coordinator.data if start <= c.next_date < end]


def _make_bin_event(collection: BinCollection) -> CalendarEvent:
    return CalendarEvent(
        start=collection.next_date,
        end=collection.next_date + datetime.timedelta(days=1),
        summary=f"{collection.name} collection",
    )


# ---------------------------------------------------------------------------
# School holidays
# ---------------------------------------------------------------------------


class _SchoolCalendarBase(CoordinatorEntity[SchoolHolidaysCoordinator], CalendarEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: SchoolHolidaysCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "east_dunbartonshire_school_holidays")},
            name="East Dunbartonshire Schools",
        )

    def _relevant_events(self) -> list[SchoolHolidayEvent]:
        raise NotImplementedError

    @property
    def event(self) -> CalendarEvent | None:
        today = datetime.date.today()
        for e in self._relevant_events():
            if e.start <= today < e.end:
                return _make_school_event(e)
        upcoming = [e for e in self._relevant_events() if e.start > today]
        return _make_school_event(upcoming[0]) if upcoming else None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
    ) -> list[CalendarEvent]:
        start = start_date.date()
        end = end_date.date()
        return [
            _make_school_event(e)
            for e in self._relevant_events()
            if e.start < end and e.end > start
        ]


class SchoolHolidaysCalendar(_SchoolCalendarBase):
    _attr_name = "School holidays"
    _attr_unique_id = "east_dunbartonshire_school_holidays_calendar"

    def _relevant_events(self) -> list[SchoolHolidayEvent]:
        if not self.coordinator.data:
            return []
        return [e for e in self.coordinator.data.events if not e.is_in_service_day]


class InServiceDaysCalendar(_SchoolCalendarBase):
    _attr_name = "In-service days"
    _attr_unique_id = "east_dunbartonshire_in_service_days_calendar"

    def _relevant_events(self) -> list[SchoolHolidayEvent]:
        if not self.coordinator.data:
            return []
        return [e for e in self.coordinator.data.events if e.is_in_service_day]


def _make_school_event(event: SchoolHolidayEvent) -> CalendarEvent:
    return CalendarEvent(
        start=event.start,
        end=event.end,
        summary=event.summary,
    )
