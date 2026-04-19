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

from .const import CONF_ADDRESS, CONF_COUNCIL, CONF_UPRN, COUNCILS, DOMAIN
from .coordinator import fetch_east_dunbartonshire_uprns

_LOGGER = logging.getLogger(__name__)


def _format_address(item: dict) -> str:
    parts = [item.get("addressLine1", ""), item.get("town", "")]
    if item.get("postcode"):
        parts.append(item["postcode"])
    return ", ".join(p for p in parts if p)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._council: str | None = None
        self._uprn_options: dict[str, str] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            self._council = user_input[CONF_COUNCIL]
            return await self.async_step_address()

        schema = vol.Schema(
            {
                vol.Required(CONF_COUNCIL): SelectSelector(
                    SelectSelectorConfig(
                        options=[SelectOptionDict(value=k, label=v) for k, v in COUNCILS.items()],
                        mode=SelectSelectorMode.LIST,
                    )
                )
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_address(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            try:
                session = async_get_clientsession(self.hass)
                results = await fetch_east_dunbartonshire_uprns(session, address)
                if not results:
                    errors["base"] = "no_results"
                else:
                    self._uprn_options = {item["uprn"]: _format_address(item) for item in results}
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

    async def async_step_select_uprn(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            uprn = user_input[CONF_UPRN]
            address = self._uprn_options[uprn]
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
            SelectOptionDict(value=uprn, label=addr) for uprn, addr in self._uprn_options.items()
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
