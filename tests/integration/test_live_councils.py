"""Integration tests: real HTTP requests against live council websites.

Each test performs the full property-search → collection-fetch flow for one
council using a known residential postcode/address. Failures here mean the
council's website or API has changed and the integration needs updating.

Run with: uv run --extra integration pytest tests/integration/ -v
"""

import pytest

from custom_components.east_dunbartonshire.coordinator import (
    _fetch_collections,
    fetch_uprns,
)

pytestmark = pytest.mark.integration


async def test_east_dunbartonshire(session):
    properties = await fetch_uprns(session, "Bearsden")
    assert properties, "No properties found for East Dunbartonshire"
    uprn = properties[0]["uprn"]
    collections = await _fetch_collections(session, uprn)
    assert collections, f"No bin collections for East Dunbartonshire UPRN {uprn}"
