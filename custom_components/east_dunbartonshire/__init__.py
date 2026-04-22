"""The East Dunbartonshire integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import EastDunbartonshireCoordinator
from .planning import PlanningCoordinator
from .school_holidays import SchoolHolidaysCoordinator

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.CALENDAR,
    Platform.GEO_LOCATION,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    domain_data = hass.data.setdefault(DOMAIN, {})

    # Bins coordinator — per config entry (per address)
    bins_coordinator = EastDunbartonshireCoordinator(hass, entry)
    await bins_coordinator.async_config_entry_first_refresh()
    domain_data[entry.entry_id] = bins_coordinator

    # School holidays coordinator — shared across all entries, set up once
    if "school_holidays" not in domain_data:
        school_coordinator = SchoolHolidaysCoordinator(hass)
        await school_coordinator.async_config_entry_first_refresh()
        domain_data["school_holidays"] = school_coordinator

    # Planning coordinator — proximity is relative to the HA home location
    planning_coordinator = PlanningCoordinator(
        hass, hass.config.latitude, hass.config.longitude
    )
    await planning_coordinator.async_config_entry_first_refresh()
    domain_data[f"{entry.entry_id}_planning"] = planning_coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        domain_data = hass.data[DOMAIN]
        domain_data.pop(entry.entry_id)
        domain_data.pop(f"{entry.entry_id}_planning", None)
        domain_data.pop(f"{entry.entry_id}_planning_geo", None)
        # Remove shared coordinator only when the last entry is removed
        if not any(k for k in domain_data if k not in ("school_holidays",)):
            domain_data.pop("school_holidays", None)
    return unload_ok
