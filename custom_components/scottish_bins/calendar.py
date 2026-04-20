"""Calendar platform for the Scottish Bins integration."""

from __future__ import annotations

import datetime

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BinCollection, ScottishBinsCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ScottishBinsCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ScottishBinsCalendar(coordinator, entry)])


class ScottishBinsCalendar(CoordinatorEntity[ScottishBinsCoordinator], CalendarEntity):
    _attr_has_entity_name = True
    _attr_name = "Bin collections"

    def __init__(
        self, coordinator: ScottishBinsCoordinator, entry: ConfigEntry
    ) -> None:
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
        return _make_event(min(upcoming, key=lambda c: c.next_date))

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
        return [
            _make_event(c) for c in self.coordinator.data if start <= c.next_date < end
        ]


def _make_event(collection: BinCollection) -> CalendarEvent:
    return CalendarEvent(
        start=collection.next_date,
        end=collection.next_date + datetime.timedelta(days=1),
        summary=f"{collection.name} collection",
    )
