"""Geo location platform for East Dunbartonshire planning applications."""

from __future__ import annotations

from homeassistant.components.geo_location import GeolocationEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .planning import PlanningApplication, PlanningCoordinator

_SOURCE = "east_dunbartonshire_planning"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN]
    planning_key = f"{entry.entry_id}_planning"
    if planning_key not in data:
        return

    coordinator: PlanningCoordinator = data[planning_key]
    manager = _PlanningGeoManager(hass, coordinator, entry, async_add_entities)
    data[f"{entry.entry_id}_planning_geo"] = manager
    # Trigger initial population if data is already available
    manager.async_handle_update()


class _PlanningGeoManager:
    """Manages the lifecycle of PlanningApplicationGeoLocation entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: PlanningCoordinator,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
    ) -> None:
        self._hass = hass
        self._coordinator = coordinator
        self._entry = entry
        self._async_add_entities = async_add_entities
        self._entities: dict[str, PlanningApplicationGeoLocation] = {}
        coordinator.async_add_listener(self.async_handle_update)

    @callback
    def async_handle_update(self) -> None:
        if not self._coordinator.data:
            return

        new_apps = {
            a.reference: a
            for a in self._coordinator.data.applications
            if a.latitude is not None and a.longitude is not None
        }
        current_refs = set(self._entities)

        # Remove applications no longer nearby
        for ref in current_refs - new_apps.keys():
            entity = self._entities.pop(ref)
            self._hass.async_create_task(entity.async_remove())

        # Update existing entities
        for ref in current_refs & new_apps.keys():
            self._entities[ref].async_update_from_application(new_apps[ref])

        # Add new applications
        to_add = [
            PlanningApplicationGeoLocation(app, self._entry)
            for ref, app in new_apps.items()
            if ref not in current_refs
        ]
        if to_add:
            for entity in to_add:
                self._entities[entity.unique_id or entity._app.reference] = entity
            self._async_add_entities(to_add)


class PlanningApplicationGeoLocation(GeolocationEvent):
    """A single planning application shown as a map pin."""

    _attr_should_poll = False
    _attr_source = _SOURCE
    _attr_has_entity_name = True

    def __init__(self, app: PlanningApplication, entry: ConfigEntry) -> None:
        self._app = app
        self._attr_unique_id = f"{entry.entry_id}_geo_{app.reference}"
        self._attr_name = app.reference
        self._attr_latitude = app.latitude
        self._attr_longitude = app.longitude
        self._attr_distance = (app.distance_m or 0) / 1000.0  # km

    @callback
    def async_update_from_application(self, app: PlanningApplication) -> None:
        self._app = app
        self._attr_latitude = app.latitude
        self._attr_longitude = app.longitude
        self._attr_distance = (app.distance_m or 0) / 1000.0
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "address": self._app.address,
            "description": self._app.description,
            "date_modified": (
                self._app.date_modified.isoformat() if self._app.date_modified else None
            ),
            "url": self._app.url,
        }
