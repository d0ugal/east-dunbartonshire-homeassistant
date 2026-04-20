"""Config flow for the Scottish Bins integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_ADDRESS,
    CONF_COUNCIL,
    CONF_UPRN,
    COUNCIL_CLACKMANNANSHIRE,
    COUNCIL_EAST_DUNBARTONSHIRE,
    COUNCIL_EAST_RENFREWSHIRE,
    COUNCIL_FALKIRK,
    COUNCIL_NORTH_AYRSHIRE,
    COUNCIL_SOUTH_AYRSHIRE,
    COUNCIL_WEST_LOTHIAN,
    COUNCILS,
    DOMAIN,
)
from .coordinator import (
    fetch_clackmannanshire_properties,
    fetch_east_dunbartonshire_uprns,
    fetch_east_renfrewshire_properties,
    fetch_falkirk_properties,
    fetch_north_ayrshire_uprns,
    fetch_south_ayrshire_properties,
    fetch_west_lothian_properties,
    format_east_dun_address,
)

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._council: str | None = None
        self._property_options: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            self._council = user_input[CONF_COUNCIL]
            return await self.async_step_address()

        schema = vol.Schema(
            {
                vol.Required(CONF_COUNCIL): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(value=k, label=v)
                            for k, v in COUNCILS.items()
                        ],
                        mode=SelectSelectorMode.LIST,
                    )
                )
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_address(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            query = user_input[CONF_ADDRESS]
            try:
                session = async_get_clientsession(self.hass)
                options = await self._search_properties(session, query)
                if not options:
                    errors["base"] = "no_results"
                else:
                    self._property_options = dict(options)
                    return await self.async_step_select_uprn()
            except Exception:
                _LOGGER.exception("Error looking up address")
                errors["base"] = "cannot_connect"

        schema = vol.Schema(
            {
                vol.Required(CONF_ADDRESS): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
                )
            }
        )
        return self.async_show_form(
            step_id="address",
            data_schema=schema,
            errors=errors,
        )

    async def _search_properties(self, session, query: str) -> list[tuple[str, str]]:
        if self._council == COUNCIL_EAST_DUNBARTONSHIRE:
            results = await fetch_east_dunbartonshire_uprns(session, query)
            return [(item["uprn"], format_east_dun_address(item)) for item in results]
        if self._council == COUNCIL_CLACKMANNANSHIRE:
            return await fetch_clackmannanshire_properties(session, query)
        if self._council == COUNCIL_FALKIRK:
            return await fetch_falkirk_properties(session, query)
        if self._council == COUNCIL_NORTH_AYRSHIRE:
            return await fetch_north_ayrshire_uprns(session, query)
        if self._council == COUNCIL_WEST_LOTHIAN:
            return await fetch_west_lothian_properties(session, query)
        if self._council == COUNCIL_EAST_RENFREWSHIRE:
            return await fetch_east_renfrewshire_properties(session, query)
        if self._council == COUNCIL_SOUTH_AYRSHIRE:
            return await fetch_south_ayrshire_properties(session, query)
        return []

    async def async_step_select_uprn(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            uprn = user_input[CONF_UPRN]
            address = self._property_options[uprn]
            await self.async_set_unique_id(f"{self._council}_{uprn}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=address,
                data={
                    CONF_COUNCIL: self._council,
                    CONF_UPRN: uprn,
                    CONF_ADDRESS: address,
                },
            )

        options = [
            SelectOptionDict(value=pid, label=name)
            for pid, name in self._property_options.items()
        ]
        schema = vol.Schema(
            {
                vol.Required(CONF_UPRN): SelectSelector(
                    SelectSelectorConfig(
                        options=options,
                        mode=SelectSelectorMode.LIST,
                    )
                )
            }
        )
        return self.async_show_form(step_id="select_uprn", data_schema=schema)
