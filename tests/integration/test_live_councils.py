"""Integration tests: real HTTP requests against live council websites.

Each test performs the full property-search → collection-fetch flow for one
council using a known residential postcode/address. Failures here mean the
council's website or API has changed and the integration needs updating.

Run with: uv run --extra integration pytest tests/integration/ -v
"""

import pytest

from custom_components.east_dunbartonshire.coordinator import (
    _fetch_clackmannanshire,
    _fetch_east_dunbartonshire,
    _fetch_east_renfrewshire,
    _fetch_falkirk,
    _fetch_north_ayrshire,
    _fetch_south_ayrshire,
    _fetch_west_lothian,
    fetch_clackmannanshire_properties,
    fetch_east_dunbartonshire_uprns,
    fetch_east_renfrewshire_properties,
    fetch_falkirk_properties,
    fetch_north_ayrshire_uprns,
    fetch_south_ayrshire_properties,
    fetch_west_lothian_properties,
)

pytestmark = pytest.mark.integration


async def test_east_dunbartonshire(session):
    properties = await fetch_east_dunbartonshire_uprns(session, "Bearsden")
    assert properties, "No properties found for East Dunbartonshire"
    uprn = properties[0]["uprn"]
    collections = await _fetch_east_dunbartonshire(session, uprn)
    assert collections, f"No bin collections for East Dunbartonshire UPRN {uprn}"


async def test_clackmannanshire(session):
    properties = await fetch_clackmannanshire_properties(session, "FK10 1HA")
    assert properties, "No properties found for Clackmannanshire"
    property_id, _ = properties[0]
    collections = await _fetch_clackmannanshire(session, property_id)
    assert collections, f"No bin collections for Clackmannanshire property {property_id}"


async def test_falkirk(session):
    properties = await fetch_falkirk_properties(session, "FK1 1AA")
    assert properties, "No properties found for Falkirk"
    uprn, _ = properties[0]
    collections = await _fetch_falkirk(session, uprn)
    assert isinstance(collections, list), f"Unexpected result type for Falkirk UPRN {uprn}"


async def test_north_ayrshire(session):
    properties = await fetch_north_ayrshire_uprns(session, "KA12 0")
    assert properties, "No properties found for North Ayrshire"
    uprn, _ = properties[0]
    collections = await _fetch_north_ayrshire(session, uprn)
    assert isinstance(collections, list), f"Unexpected result type for North Ayrshire UPRN {uprn}"


async def test_west_lothian(session):
    properties = await fetch_west_lothian_properties(session, "EH54 5AG")
    assert properties, "No properties found for West Lothian"
    uprn, _ = properties[0]
    collections = await _fetch_west_lothian(session, uprn)
    assert collections, f"No bin collections for West Lothian UPRN {uprn}"


async def test_east_renfrewshire(session):
    properties = await fetch_east_renfrewshire_properties(session, "G77 6QF")
    assert properties, "No properties found for East Renfrewshire"
    uprn, address = properties[0]
    collections = await _fetch_east_renfrewshire(session, uprn, address)
    assert collections, f"No bin collections for East Renfrewshire UPRN {uprn}"


async def test_south_ayrshire(session):
    properties = await fetch_south_ayrshire_properties(session, "KA8 0NE")
    assert properties, "No properties found for South Ayrshire"
    uprn, address = properties[0]
    collections = await _fetch_south_ayrshire(session, uprn, address)
    assert collections, f"No bin collections for South Ayrshire UPRN {uprn}"
