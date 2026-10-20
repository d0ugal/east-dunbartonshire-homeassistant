"""Unit tests for config entry setup."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.east_dunbartonshire import DOMAIN, PLATFORMS, async_setup_entry


class _FakeCoordinator:
    """Stands in for a coordinator; records which refresh method setup used."""

    def __init__(self, *args, fail_first_refresh=False, **kwargs):
        self.fail_first_refresh = fail_first_refresh
        self.refreshed = False

    async def async_config_entry_first_refresh(self):
        if self.fail_first_refresh:
            raise RuntimeError("first refresh failed")
        self.refreshed = True

    async def async_refresh(self):
        # Never raises: a failed update is recorded on the coordinator instead.
        self.refreshed = True


class _FailingFirstRefresh(_FakeCoordinator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, fail_first_refresh=True, **kwargs)


def _hass():
    return SimpleNamespace(
        data={},
        config=SimpleNamespace(latitude=55.9, longitude=-4.2),
        config_entries=SimpleNamespace(async_forward_entry_setups=AsyncMock()),
    )


def _entry():
    return SimpleNamespace(entry_id="entry1", title="Home")


def _setup(hass, *, bins, school, planning):
    base = "custom_components.east_dunbartonshire"
    with (
        patch(f"{base}.EastDunbartonshireCoordinator", bins),
        patch(f"{base}.SchoolHolidaysCoordinator", school),
        patch(f"{base}.PlanningCoordinator", planning),
    ):
        return asyncio.run(async_setup_entry(hass, _entry()))


def test_setup_succeeds_when_optional_sources_fail():
    """A planning or school holiday outage must not stop the bin sensors loading."""
    hass = _hass()

    assert _setup(
        hass, bins=_FakeCoordinator, school=_FailingFirstRefresh, planning=_FailingFirstRefresh
    )

    domain_data = hass.data[DOMAIN]
    assert domain_data["entry1"].refreshed
    assert domain_data["school_holidays"].refreshed
    assert domain_data["entry1_planning"].refreshed
    hass.config_entries.async_forward_entry_setups.assert_awaited_once()
    assert hass.config_entries.async_forward_entry_setups.await_args.args[1] == PLATFORMS


def test_setup_still_fails_when_bins_source_fails():
    """The bin collections are the integration's core data, so they stay required."""
    hass = _hass()

    with pytest.raises(RuntimeError, match="first refresh failed"):
        _setup(hass, bins=_FailingFirstRefresh, school=_FakeCoordinator, planning=_FakeCoordinator)

    hass.config_entries.async_forward_entry_setups.assert_not_awaited()
