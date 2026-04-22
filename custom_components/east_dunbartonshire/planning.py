"""Planning applications for East Dunbartonshire via ArcGIS spatial query."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from math import asin, cos, radians, sin, sqrt

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

_ARCGIS_QUERY = (
    "https://planning.eastdunbarton.gov.uk/server/rest/services/"
    "PALIVE/LIVEUniformPA_Planning/FeatureServer/2/query"
)
_ARCGIS_REFERER = (
    "https://planning.eastdunbarton.gov.uk/portal/apps/experiencebuilder/"
    "experience/?id=fa77980e1f55476ba379d5553f6f9376"
)
_POSTCODES_IO_REVERSE = "https://api.postcodes.io/postcodes"
DEFAULT_RADIUS_M = 500
_RECENT_DAYS = 90


@dataclass
class PlanningApplication:
    reference: str
    address: str
    description: str
    date_modified: date | None
    url: str
    distance_m: int | None = None
    latitude: float | None = None
    longitude: float | None = None


@dataclass
class PlanningData:
    applications: list[PlanningApplication] = field(default_factory=list)
    search_radius_m: int = DEFAULT_RADIUS_M


class PlanningCoordinator(DataUpdateCoordinator[PlanningData]):
    def __init__(
        self,
        hass: HomeAssistant,
        lat: float,
        lon: float,
        radius_m: int = DEFAULT_RADIUS_M,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="east_dunbartonshire_planning",
            update_interval=timedelta(hours=4),
        )
        self._lat = lat
        self._lon = lon
        self._radius_m = radius_m
        self._easting: int | None = None
        self._northing: int | None = None
        self.session = async_get_clientsession(hass)

    async def _async_update_data(self) -> PlanningData:
        try:
            if self._easting is None:
                self._easting, self._northing = await _latlon_to_bng(
                    self.session, self._lat, self._lon
                )
            easting: int = self._easting
            northing: int = self._northing  # type: ignore[assignment]
            return await _fetch_nearby(
                self.session, easting, northing, self._lat, self._lon, self._radius_m
            )
        except Exception as err:
            raise UpdateFailed(f"Error fetching planning applications: {err}") from err


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6_371_000.0
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlam = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlam / 2) ** 2
    return r * 2 * asin(sqrt(a))


async def _latlon_to_bng(session, lat: float, lon: float) -> tuple[int, int]:
    """Convert WGS84 lat/lon to BNG easting/northing via postcodes.io nearest postcode."""
    async with session.get(
        _POSTCODES_IO_REVERSE, params={"lon": lon, "lat": lat, "limit": 1}
    ) as resp:
        resp.raise_for_status()
        data = await resp.json()
    results = data.get("result") or []
    if not results:
        raise ValueError(f"Could not convert ({lat}, {lon}) to BNG coordinates")
    r = results[0]
    return int(r["eastings"]), int(r["northings"])


async def _fetch_nearby(
    session,
    home_easting: int,
    home_northing: int,
    home_lat: float,
    home_lon: float,
    radius_m: int,
) -> PlanningData:
    bbox = {
        "xmin": home_easting - radius_m,
        "ymin": home_northing - radius_m,
        "xmax": home_easting + radius_m,
        "ymax": home_northing + radius_m,
    }
    cutoff_ms = int(
        (datetime.now(UTC) - timedelta(days=_RECENT_DAYS)).timestamp() * 1000
    )
    params = {
        "f": "json",
        "geometry": json.dumps(bbox, separators=(",", ":")),
        "geometryType": "esriGeometryEnvelope",
        "inSR": "27700",
        "outSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "where": f"ISPAVISIBLE=1 AND DATEMODIFIED>={cutoff_ms}",
        "outFields": "REFVAL,KEYVAL,ADDRESS,DESCRIPTION,DATEMODIFIED",
        "returnGeometry": "false",
        "returnCentroid": "true",
        "returnExceededLimitFeatures": "false",
    }
    async with session.get(
        _ARCGIS_QUERY, params=params, headers={"Referer": _ARCGIS_REFERER}
    ) as resp:
        resp.raise_for_status()
        data = await resp.json()

    nearby = []
    for feature in data.get("features", []):
        attrs = feature.get("attributes", {})
        centroid = feature.get("centroid")
        if not centroid:
            continue
        # outSR=4326: centroid x=longitude, y=latitude
        app_lon, app_lat = centroid["x"], centroid["y"]
        dist = _haversine_m(home_lat, home_lon, app_lat, app_lon)
        if dist > radius_m:
            continue
        app = _parse_feature(attrs, round(dist), app_lat, app_lon)
        if app:
            nearby.append(app)

    nearby.sort(key=lambda a: a.date_modified or date.min, reverse=True)
    return PlanningData(applications=nearby, search_radius_m=radius_m)


def _parse_feature(
    attrs: dict, distance_m: int, latitude: float, longitude: float
) -> PlanningApplication | None:
    keyval = attrs.get("KEYVAL", "")
    if not keyval:
        return None
    reference = attrs.get("REFVAL") or keyval
    address = attrs.get("ADDRESS", "").replace("\r", ", ").strip(", ")
    description = attrs.get("DESCRIPTION", "")
    date_modified: date | None = None
    raw = attrs.get("DATEMODIFIED")
    if isinstance(raw, (int, float)):
        try:
            date_modified = datetime.utcfromtimestamp(raw / 1000).date()
        except (OSError, OverflowError, ValueError):
            pass
    url = (
        "https://planning.eastdunbarton.gov.uk/online-applications/"
        f"applicationDetails.do?activeTab=summary&keyVal={keyval}"
    )
    return PlanningApplication(
        reference=reference,
        address=address,
        description=description,
        date_modified=date_modified,
        url=url,
        distance_m=distance_m,
        latitude=latitude,
        longitude=longitude,
    )
