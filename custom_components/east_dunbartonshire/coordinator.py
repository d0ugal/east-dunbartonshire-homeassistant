"""Data coordinator for the East Dunbartonshire integration."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_UPRN, DOMAIN

_LOGGER = logging.getLogger(__name__)

EAST_DUNBARTONSHIRE_URL = (
    "https://www.eastdunbarton.gov.uk/services/a-z-of-services/"
    "bins-waste-and-recycling/bins-and-recycling/collections/"
)
EAST_DUNBARTONSHIRE_UPRN_URL = "https://www.eastdunbarton.gov.uk/umbraco/api/bincollection/GetUPRNs"


@dataclass
class BinCollection:
    bin_class: str
    name: str
    next_date: date


class EastDunbartonshireCoordinator(DataUpdateCoordinator[list[BinCollection]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=24),
        )
        self._entry = entry
        self.session = async_get_clientsession(hass)

    async def _async_update_data(self) -> list[BinCollection]:
        uprn = self._entry.data[CONF_UPRN]
        try:
            return await _fetch_collections(self.session, uprn)
        except Exception as err:
            raise UpdateFailed(f"Error fetching bin collections: {err}") from err


async def _fetch_collections(session, uprn: str) -> list[BinCollection]:
    async with session.get(EAST_DUNBARTONSHIRE_URL, params={"uprn": uprn}) as resp:
        resp.raise_for_status()
        html = await resp.text()
    return _parse_html(html)


def _parse_html(html: str) -> list[BinCollection]:
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


async def fetch_uprns(session, address: str) -> list[dict]:
    async with session.get(EAST_DUNBARTONSHIRE_UPRN_URL, params={"address": address}) as resp:
        resp.raise_for_status()
        return await resp.json()


def format_address(item: dict) -> str:
    parts = [item.get("addressLine1", ""), item.get("town", "")]
    if item.get("postcode"):
        parts.append(item["postcode"])
    return ", ".join(p for p in parts if p)
