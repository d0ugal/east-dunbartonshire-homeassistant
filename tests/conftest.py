"""Stub out homeassistant before any integration module is imported."""

import sys
import types


def _add(name: str, **attrs) -> types.ModuleType:
    mod = sys.modules.get(name) or types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    sys.modules[name] = mod
    return mod


class _ConfigEntry:
    data: dict = {}
    entry_id: str = ""
    title: str = ""


class _HomeAssistant:
    pass


class _Platform:
    CALENDAR = "calendar"
    SENSOR = "sensor"


class _DataUpdateCoordinatorMeta(type):
    def __getitem__(cls, item):
        return cls


class _DataUpdateCoordinator(metaclass=_DataUpdateCoordinatorMeta):
    def __init__(self, *args, **kwargs):
        pass


class _UpdateFailed(Exception):
    pass


_add("homeassistant")
_add("homeassistant.config_entries", ConfigEntry=_ConfigEntry)
_add("homeassistant.const", Platform=_Platform)
_add("homeassistant.core", HomeAssistant=_HomeAssistant)
_add("homeassistant.helpers")
_add("homeassistant.helpers.aiohttp_client", async_get_clientsession=lambda *a, **k: None)
_add(
    "homeassistant.helpers.update_coordinator",
    DataUpdateCoordinator=_DataUpdateCoordinator,
    UpdateFailed=_UpdateFailed,
)
_add("homeassistant.helpers.device_registry", DeviceInfo=dict)
_add("homeassistant.helpers.entity_platform")
_add("homeassistant.components")
_add(
    "homeassistant.components.sensor",
    SensorDeviceClass=types.SimpleNamespace(DATE="date"),
    SensorEntity=object,
)
_add("homeassistant.components.calendar", CalendarEntity=object, CalendarEvent=dict)
_add("homeassistant.helpers.selector")
_add("homeassistant.data_entry_flow")
