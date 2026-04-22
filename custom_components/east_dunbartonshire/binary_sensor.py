"""Binary sensor platform for the East Dunbartonshire integration."""

from __future__ import annotations

import datetime

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .school_holidays import SchoolHolidaysCoordinator

_SCHOOL_DEVICE = DeviceInfo(
    identifiers={(DOMAIN, "east_dunbartonshire_school_holidays")},
    name="East Dunbartonshire Schools",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN]
    if "school_holidays" not in data:
        return
    sc: SchoolHolidaysCoordinator = data["school_holidays"]
    async_add_entities(
        [
            SchoolHolidayTodaySensor(sc),
            InServiceDayTodaySensor(sc),
        ]
    )


class SchoolHolidayTodaySensor(
    CoordinatorEntity[SchoolHolidaysCoordinator], BinarySensorEntity
):
    _attr_has_entity_name = True
    _attr_name = "School holiday today"
    _attr_unique_id = "east_dunbartonshire_school_holiday_today"
    _attr_device_info = _SCHOOL_DEVICE

    @property
    def is_on(self) -> bool:
        if not self.coordinator.data:
            return False
        today = datetime.date.today()
        return any(
            e.start <= today < e.end
            for e in self.coordinator.data.events
            if not e.is_in_service_day
        )


class InServiceDayTodaySensor(
    CoordinatorEntity[SchoolHolidaysCoordinator], BinarySensorEntity
):
    _attr_has_entity_name = True
    _attr_name = "In-service day today"
    _attr_unique_id = "east_dunbartonshire_in_service_day_today"
    _attr_device_info = _SCHOOL_DEVICE

    @property
    def is_on(self) -> bool:
        if not self.coordinator.data:
            return False
        today = datetime.date.today()
        return any(
            e.start <= today < e.end
            for e in self.coordinator.data.events
            if e.is_in_service_day
        )
