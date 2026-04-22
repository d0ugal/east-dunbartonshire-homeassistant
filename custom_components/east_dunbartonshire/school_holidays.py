"""School holidays data for East Dunbartonshire."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

SCHOOL_HOLIDAYS_PAGE_URL = (
    "https://www.eastdunbarton.gov.uk/services/a-z-of-services/"
    "primary-secondary-and-early-years-education/school-holidays/"
)

_IN_SERVICE_KEYWORDS = ("in-service", "teachers return")


@dataclass
class SchoolHolidayEvent:
    summary: str
    start: date
    end: date  # exclusive end per iCal convention
    is_in_service_day: bool

    @property
    def inclusive_end(self) -> date:
        return self.end - timedelta(days=1)


@dataclass
class SchoolHolidaysData:
    events: list[SchoolHolidayEvent]
    available_years: list[str]  # e.g. ["25-26", "26-27"]


class SchoolHolidaysCoordinator(DataUpdateCoordinator[SchoolHolidaysData]):
    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="east_dunbartonshire_school_holidays",
            update_interval=timedelta(hours=24),
        )
        self.session = async_get_clientsession(hass)

    async def _async_update_data(self) -> SchoolHolidaysData:
        try:
            return await _fetch_school_holidays(self.session)
        except Exception as err:
            raise UpdateFailed(f"Error fetching school holidays: {err}") from err


async def _fetch_school_holidays(session) -> SchoolHolidaysData:
    async with session.get(SCHOOL_HOLIDAYS_PAGE_URL) as resp:
        resp.raise_for_status()
        html = await resp.text()

    ics_urls = re.findall(r'href="([^"]+school-holidays[^"]+\.ics)"', html, re.IGNORECASE)
    # Make absolute
    ics_urls = [
        u if u.startswith("http") else f"https://www.eastdunbarton.gov.uk{u}" for u in ics_urls
    ]

    available_years = [_year_from_url(u) for u in ics_urls]

    events: list[SchoolHolidayEvent] = []
    for url in ics_urls:
        async with session.get(url) as resp:
            resp.raise_for_status()
            ics_text = await resp.text()
        events.extend(_parse_ics(ics_text))

    events.sort(key=lambda e: e.start)
    return SchoolHolidaysData(events=events, available_years=available_years)


def _year_from_url(url: str) -> str:
    m = re.search(r"school-holidays-(\d{2}-\d{2})", url, re.IGNORECASE)
    return m.group(1) if m else url


def _parse_ics(ics_text: str) -> list[SchoolHolidayEvent]:
    events = []
    for block in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", ics_text, re.DOTALL):
        summary_m = re.search(r"SUMMARY:(.*)", block)
        start_m = re.search(r"DTSTART(?:;VALUE=DATE)?:(\d{8})", block)
        end_m = re.search(r"DTEND(?:;VALUE=DATE)?:(\d{8})", block)

        if not (summary_m and start_m):
            continue

        summary = summary_m.group(1).strip()
        start = _parse_date(start_m.group(1))
        end = _parse_date(end_m.group(1)) if end_m else start + timedelta(days=1)

        is_in_service = any(k in summary.lower() for k in _IN_SERVICE_KEYWORDS)
        events.append(
            SchoolHolidayEvent(
                summary=summary,
                start=start,
                end=end,
                is_in_service_day=is_in_service,
            )
        )
    return events


def _parse_date(s: str) -> date:
    return datetime.strptime(s[:8], "%Y%m%d").date()
