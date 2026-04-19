"""Data coordinator for the Scottish Bins integration."""

from __future__ import annotations

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


# ---------------------------------------------------------------------------
# Clackmannanshire
# ---------------------------------------------------------------------------


async def fetch_clackmannanshire_properties(session, postcode: str) -> list[tuple[str, str]]:
    """Search by postcode; returns [(property_id, display_name)]."""
    async with session.get(CLACKS_SEARCH_URL, params={"pc": postcode}) as resp:
        resp.raise_for_status()
        html = await resp.text()

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

    matches = re.findall(
        r'href="/collections/(\d+)">(.*?)</a>',
        html,
    )
    return [(m[0], m[1].strip()) for m in matches]


async def _fetch_falkirk(session, uprn: str) -> list[BinCollection]:
    today = date.today()
    async with session.get(f"{FALKIRK_API_URL}{uprn}", allow_redirects=True) as resp:
        resp.raise_for_status()
        data = await resp.json()

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
