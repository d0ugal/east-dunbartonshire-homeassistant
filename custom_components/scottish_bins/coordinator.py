"""Data coordinator for the Scottish Bins integration."""

from __future__ import annotations

import base64
import html as html_lib
import json
import logging
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_COUNCIL,
    CONF_UPRN,
    COUNCIL_CLACKMANNANSHIRE,
    COUNCIL_EAST_DUNBARTONSHIRE,
    COUNCIL_FALKIRK,
    COUNCIL_NORTH_AYRSHIRE,
    COUNCIL_WEST_LOTHIAN,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

EAST_DUNBARTONSHIRE_URL = (
    "https://www.eastdunbarton.gov.uk/services/a-z-of-services/"
    "bins-waste-and-recycling/bins-and-recycling/collections/"
)
EAST_DUNBARTONSHIRE_UPRN_URL = "https://www.eastdunbarton.gov.uk/umbraco/api/bincollection/GetUPRNs"

CLACKS_BASE_URL = "https://www.clacks.gov.uk"
CLACKS_SEARCH_URL = f"{CLACKS_BASE_URL}/environment/wastecollection/"

FALKIRK_SEARCH_URL = "https://recycling.falkirk.gov.uk/search/"
FALKIRK_API_URL = "https://recycling.falkirk.gov.uk/api/collections/"

NORTH_AYRSHIRE_ADDRESS_URL = (
    "https://www.maps.north-ayrshire.gov.uk/arcgis/rest/services/AGOL/CAG_VIEW/MapServer/0/query"
)
NORTH_AYRSHIRE_BINS_URL = (
    "https://www.maps.north-ayrshire.gov.uk/arcgis/rest/services/AGOL/YourLocationLive/MapServer/8/query"
)

WEST_LOTHIAN_BASE_URL = "https://www.westlothian.gov.uk"
WEST_LOTHIAN_BIN_URL = f"{WEST_LOTHIAN_BASE_URL}/bin-collections"
WEST_LOTHIAN_POSTCODE_URL = f"{WEST_LOTHIAN_BASE_URL}/apiserver/postcode"


@dataclass
class BinCollection:
    bin_class: str
    name: str
    next_date: date


class ScottishBinsCoordinator(DataUpdateCoordinator[list[BinCollection]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=6),
        )
        self._entry = entry
        self.session = async_get_clientsession(hass)

    async def _async_update_data(self) -> list[BinCollection]:
        council = self._entry.data[CONF_COUNCIL]
        property_id = self._entry.data[CONF_UPRN]

        try:
            if council == COUNCIL_EAST_DUNBARTONSHIRE:
                return await _fetch_east_dunbartonshire(self.session, property_id)
            if council == COUNCIL_CLACKMANNANSHIRE:
                return await _fetch_clackmannanshire(self.session, property_id)
            if council == COUNCIL_FALKIRK:
                return await _fetch_falkirk(self.session, property_id)
            if council == COUNCIL_NORTH_AYRSHIRE:
                return await _fetch_north_ayrshire(self.session, property_id)
            if council == COUNCIL_WEST_LOTHIAN:
                return await _fetch_west_lothian(self.session, property_id)
        except Exception as err:
            raise UpdateFailed(f"Error fetching bin collections: {err}") from err

        raise UpdateFailed(f"Unknown council: {council}")


# ---------------------------------------------------------------------------
# East Dunbartonshire
# ---------------------------------------------------------------------------


async def _fetch_east_dunbartonshire(session, uprn: str) -> list[BinCollection]:
    async with session.get(EAST_DUNBARTONSHIRE_URL, params={"uprn": uprn}) as resp:
        resp.raise_for_status()
        html = await resp.text()
    return _parse_east_dunbartonshire_html(html)


def _parse_east_dunbartonshire_html(html: str) -> list[BinCollection]:
    rows = re.findall(
        r'<td class="([^"]+)">([^<]+)</td>\s*<td>.*?<span>([^<]+)</span>',
        html,
        re.DOTALL,
    )
    collections = []
    for css_class, name, date_str in rows:
        try:
            next_date = datetime.strptime(date_str.strip(), "%A, %d %B %Y").date()
            collections.append(
                BinCollection(
                    bin_class=css_class.strip(),
                    name=name.strip(),
                    next_date=next_date,
                )
            )
        except ValueError:
            _LOGGER.warning("Could not parse bin collection date: %s", date_str)
    return collections


async def fetch_east_dunbartonshire_uprns(session, address: str) -> list[dict]:
    async with session.get(EAST_DUNBARTONSHIRE_UPRN_URL, params={"address": address}) as resp:
        resp.raise_for_status()
        return await resp.json()


def format_east_dun_address(item: dict) -> str:
    parts = [item.get("addressLine1", ""), item.get("town", "")]
    if item.get("postcode"):
        parts.append(item["postcode"])
    return ", ".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# Clackmannanshire
# ---------------------------------------------------------------------------


async def fetch_clackmannanshire_properties(session, postcode: str) -> list[tuple[str, str]]:
    """Search by postcode; returns [(property_id, display_name)]."""
    async with session.get(CLACKS_SEARCH_URL, params={"pc": postcode}) as resp:
        resp.raise_for_status()
        html = await resp.text()
    return _parse_clackmannanshire_search(html)


def _parse_clackmannanshire_search(html: str) -> list[tuple[str, str]]:
    matches = re.findall(
        r'href="/environment/wastecollection/id/(\d+)/">(.*?)</a>',
        html,
    )
    return [(m[0], m[1].strip()) for m in matches]


async def _fetch_clackmannanshire(session, property_id: str) -> list[BinCollection]:
    url = f"{CLACKS_BASE_URL}/environment/wastecollection/id/{property_id}/"
    async with session.get(url) as resp:
        resp.raise_for_status()
        html = await resp.text()

    # Extract the primary ICS URL (first .ics link, which is the main calendar)
    ics_paths = re.findall(r'href="(/document/[^"]+\.ics)"', html)
    if not ics_paths:
        _LOGGER.warning("No ICS calendar found for Clackmannanshire property %s", property_id)
        return []

    ics_url = CLACKS_BASE_URL + ics_paths[0]
    async with session.get(ics_url) as resp:
        resp.raise_for_status()
        ics_text = await resp.text()

    return _parse_ics_collections(ics_text, date.today())


def _parse_ics_collections(ics_text: str, today: date) -> list[BinCollection]:
    """Parse iCal text with simple WEEKLY RRULE to find next upcoming dates."""
    events = re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", ics_text, re.DOTALL)
    collections = []
    for event in events:
        m_summary = re.search(r"SUMMARY:(.*)", event)
        m_dtstart = re.search(r"DTSTART(?:;VALUE=DATE)?:(\d{8})", event)
        if not (m_summary and m_dtstart):
            continue

        summary = m_summary.group(1).strip()
        raw = m_dtstart.group(1)
        dtstart = date(int(raw[:4]), int(raw[4:6]), int(raw[6:8]))

        m_rrule = re.search(r"RRULE:(.*)", event)
        if m_rrule:
            rrule = m_rrule.group(1)
            m_interval = re.search(r"INTERVAL=(\d+)", rrule)
            m_until = re.search(r"UNTIL=(\d{8})", rrule)
            interval = int(m_interval.group(1)) if m_interval else 1
            until: date | None = None
            if m_until:
                u = m_until.group(1)
                until = date(int(u[:4]), int(u[4:6]), int(u[6:8]))

            step = timedelta(weeks=interval)
            current = dtstart
            while current < today:
                current += step
            if until is not None and current > until:
                continue
        else:
            current = dtstart
            if current < today:
                continue

        collections.append(BinCollection(bin_class=summary, name=summary, next_date=current))

    return collections


# ---------------------------------------------------------------------------
# Falkirk
# ---------------------------------------------------------------------------


async def fetch_falkirk_properties(session, query: str) -> list[tuple[str, str]]:
    """Search by postcode or address; returns [(uprn, display_name)]."""
    async with session.get(FALKIRK_SEARCH_URL, params={"query": query}) as resp:
        resp.raise_for_status()
        html = await resp.text()
    return _parse_falkirk_search(html)


def _parse_falkirk_search(html: str) -> list[tuple[str, str]]:
    matches = re.findall(
        r'href="/collections/(\d+)">(.*?)</a>',
        html,
    )
    return [(m[0], m[1].strip()) for m in matches]


async def _fetch_falkirk(session, uprn: str) -> list[BinCollection]:
    async with session.get(f"{FALKIRK_API_URL}{uprn}", allow_redirects=True) as resp:
        resp.raise_for_status()
        data = await resp.json()
    return _parse_falkirk_json(data, date.today())


def _parse_falkirk_json(data: dict, today: date) -> list[BinCollection]:
    collections = []
    for item in data.get("collections", []):
        bin_type = item.get("type", "")
        dates = [
            date.fromisoformat(d) for d in item.get("dates", []) if date.fromisoformat(d) >= today
        ]
        if dates:
            collections.append(
                BinCollection(
                    bin_class=bin_type,
                    name=bin_type,
                    next_date=min(dates),
                )
            )
    return collections


# ---------------------------------------------------------------------------
# North Ayrshire
# ---------------------------------------------------------------------------


async def fetch_north_ayrshire_uprns(session, query: str) -> list[tuple[str, str]]:
    """Search by postcode or address; returns [(uprn, display_name)]."""
    params = {
        "where": f"UPPER(ADDRESS) LIKE UPPER('%{query}%')",
        "outFields": "ADDRESS,UPRN",
        "orderByFields": "ADDRESS ASC",
        "returnGeometry": "false",
        "f": "json",
    }
    async with session.get(NORTH_AYRSHIRE_ADDRESS_URL, params=params) as resp:
        resp.raise_for_status()
        data = await resp.json()
    features = data.get("features", [])
    return [(str(f["attributes"]["UPRN"]), f["attributes"]["ADDRESS"]) for f in features]


async def _fetch_north_ayrshire(session, uprn: str) -> list[BinCollection]:
    params = {
        "where": f"UPRN='{uprn.lstrip('0')}'",
        "outFields": "*",
        "f": "json",
    }
    async with session.get(NORTH_AYRSHIRE_BINS_URL, params=params) as resp:
        resp.raise_for_status()
        data = await resp.json()
    features = data.get("features", [])
    if not features:
        return []
    return _parse_north_ayrshire_attrs(features[0]["attributes"])


def _parse_north_ayrshire_attrs(attrs: dict) -> list[BinCollection]:
    fields = [
        ("BLUE_DATE_TEXT", "blue_bin", "Blue bin"),
        ("GREY_DATE_TEXT", "grey_bin", "Grey bin"),
        ("PURPLE_DATE_TEXT", "purple_bin", "Purple bin"),
        ("BROWN_DATE_TEXT", "brown_bin", "Brown bin"),
    ]
    collections = []
    for field, bin_class, name in fields:
        date_str = attrs.get(field)
        if not date_str:
            continue
        try:
            next_date = datetime.strptime(date_str, "%d/%m/%Y").date()
            collections.append(BinCollection(bin_class=bin_class, name=name, next_date=next_date))
        except ValueError:
            _LOGGER.warning("Could not parse North Ayrshire date: %s", date_str)
    return collections


# ---------------------------------------------------------------------------
# West Lothian
# ---------------------------------------------------------------------------


async def fetch_west_lothian_properties(session, postcode: str) -> list[tuple[str, str]]:
    """Search by postcode; returns [(udprn, display_name)]."""
    params = {
        "jsonrpc": json.dumps(
            {"id": 1, "method": "postcodeSearch", "params": {"provider": "EndPoint", "postcode": postcode}}
        ),
        "callback": "cb",
    }
    async with session.get(WEST_LOTHIAN_POSTCODE_URL, params=params) as resp:
        resp.raise_for_status()
        text = await resp.text()
    match = re.search(r"cb\((.*)\)", text, re.DOTALL)
    if not match:
        return []
    results = json.loads(match.group(1))
    return _parse_west_lothian_addresses(results)


def _parse_west_lothian_addresses(results: list[dict]) -> list[tuple[str, str]]:
    output = []
    for item in results:
        udprn = str(item.get("udprn", ""))
        parts = [item.get(f"line{i}", "") for i in range(1, 6)]
        parts.extend([item.get("town", ""), item.get("postcode", "")])
        address = ", ".join(p for p in parts if p)
        if udprn:
            output.append((udprn, address))
    return output


async def _fetch_west_lothian(session, uprn: str) -> list[BinCollection]:
    # Step 1: GET form page to extract session tokens
    async with session.get(WEST_LOTHIAN_BIN_URL) as resp:
        resp.raise_for_status()
        html = await resp.text()
    form_data, action_url = _parse_west_lothian_form(html)

    # Step 2+3: POST triggers the GOSSForms cookie challenge (303 → verifycookie → 303 → form).
    # aiohttp follows all redirects automatically and the session jar captures the cookie.
    async with session.post(action_url, data=form_data, allow_redirects=True) as resp:
        resp.raise_for_status()
        html = await resp.text()

    # Step 4: Re-parse the form — the nonce (fsn) has rotated after the cookie dance.
    form_data, action_url = _parse_west_lothian_form(html)
    form_data["WLBINCOLLECTION_PAGE1_UPRN"] = uprn
    form_data["WLBINCOLLECTION_FORMACTION_NEXT"] = "WLBINCOLLECTION_PAGE1_NAVBUTTONS"

    # Step 5: Submit PAGE1 with the chosen UPRN to get PAGE2 collection data.
    async with session.post(action_url, data=form_data, allow_redirects=True) as resp:
        resp.raise_for_status()
        page2_html = await resp.text()

    return _parse_west_lothian_page2(page2_html)


def _parse_west_lothian_form(html: str) -> tuple[dict, str]:
    action_match = re.search(
        r'action="(/apiserver/formsservice/http/processsubmission[^"]+)"', html
    )
    action_url = (
        WEST_LOTHIAN_BASE_URL + html_lib.unescape(action_match.group(1))
        if action_match
        else WEST_LOTHIAN_BIN_URL
    )

    form_data: dict[str, str] = {}
    for tag in re.findall(r"<input[^>]+>", html, re.DOTALL):
        name_m = re.search(r'name="([^"]+)"', tag)
        value_m = re.search(r'value="([^"]*)"', tag)
        if name_m and name_m.group(1).startswith("WLBINCOLLECTION_"):
            form_data[name_m.group(1)] = value_m.group(1) if value_m else ""

    return form_data, action_url


def _parse_west_lothian_page2(html: str) -> list[BinCollection]:
    match = re.search(r'var WLBINCOLLECTIONFormData\s*=\s*"([^"]+)"', html)
    if not match:
        _LOGGER.warning("West Lothian: could not find WLBINCOLLECTIONFormData in PAGE2")
        return []

    data = json.loads(base64.b64decode(match.group(1)).decode())
    collections_data = data.get("PAGE2_1", {}).get("COLLECTIONS", [])

    result = []
    for item in collections_data:
        bin_type = item.get("binType", "")
        iso_date = item.get("nextCollectionISO", "")
        bin_name = item.get("binName", bin_type)
        if not (bin_type and iso_date):
            continue
        try:
            result.append(BinCollection(bin_class=bin_type, name=bin_name, next_date=date.fromisoformat(iso_date)))
        except ValueError:
            _LOGGER.warning("Could not parse West Lothian date: %s", iso_date)
    return result
