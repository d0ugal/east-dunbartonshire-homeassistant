"""Config flow for the East Dunbartonshire integration."""

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

from .const import CONF_ADDRESS, CONF_UPRN, DOMAIN
from .coordinator import fetch_uprns, format_address

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._property_options: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        return await self.async_step_address(user_input)

    async def async_step_address(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            query = user_input[CONF_ADDRESS]
            try:
                session = async_get_clientsession(self.hass)
                results = await fetch_uprns(session, query)
                options = [(item["uprn"], format_address(item)) for item in results]
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

    async def async_step_select_uprn(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            uprn = user_input[CONF_UPRN]
            address = self._property_options[uprn]
            await self.async_set_unique_id(uprn)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=address,
                data={CONF_UPRN: uprn, CONF_ADDRESS: address},
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
