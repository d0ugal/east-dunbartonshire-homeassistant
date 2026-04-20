"""Sensor platform for the East Dunbartonshire integration."""

from __future__ import annotations

import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import BIN_TYPES, DOMAIN
from .coordinator import EastDunbartonshireCoordinator
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
    coordinator: EastDunbartonshireCoordinator = data[entry.entry_id]
    entities: list[SensorEntity] = [
        BinSensor(coordinator, entry, bin_class, name) for bin_class, name in BIN_TYPES.items()
    ]
    if "school_holidays" in data:
        entities.append(SchoolHolidayYearsSensor(data["school_holidays"]))
    async_add_entities(entities)


# ---------------------------------------------------------------------------
# Bin sensors
# ---------------------------------------------------------------------------


class BinSensor(CoordinatorEntity[EastDunbartonshireCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.DATE

    def __init__(
        self,
        coordinator: EastDunbartonshireCoordinator,
        entry: ConfigEntry,
        bin_class: str,
        name: str,
    ) -> None:
        super().__init__(coordinator)
        self._bin_class = bin_class
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{bin_class}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
        )

    @property
    def native_value(self) -> datetime.date | None:
        if not self.coordinator.data:
            return None
        for collection in self.coordinator.data:
            if collection.bin_class == self._bin_class:
                return collection.next_date
        return None

    @property
    def extra_state_attributes(self) -> dict:
        if not self.coordinator.data:
            return {}
        for collection in self.coordinator.data:
            if collection.bin_class == self._bin_class:
                days = (collection.next_date - datetime.date.today()).days
                return {"days_until": days}
        return {}


# ---------------------------------------------------------------------------
# School holiday sensors
# ---------------------------------------------------------------------------


class SchoolHolidayYearsSensor(CoordinatorEntity[SchoolHolidaysCoordinator], SensorEntity):
    """Tracks which academic years' data is available. Automating on state change detects new releases."""

    _attr_has_entity_name = True
    _attr_name = "School holiday years available"
    _attr_unique_id = "east_dunbartonshire_school_holiday_years"
    _attr_device_info = _SCHOOL_DEVICE

    @property
    def native_value(self) -> str | None:
        if not self.coordinator.data:
            return None
        return ", ".join(self.coordinator.data.available_years)
