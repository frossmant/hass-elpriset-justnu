"""Config flow for Elpriset Just Nu integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_NAME,
    CONF_PRICE_ZONE,
    CONF_SURCHARGE_ELCERT,
    CONF_SURCHARGE_OTHER,
    CONF_SURCHARGE_SPOT_MARKUP,
    CONF_SURCHARGE_VARIABLE_COSTS,
    CONF_UPDATE_INTERVAL,
    CONF_VAT_PERCENT,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_VAT_PERCENT,
    DOMAIN,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    PRICE_ZONES,
)

_LOGGER = logging.getLogger(__name__)


async def _validate_zone(hass: HomeAssistant, zone: str) -> bool:
    """Validate that we can fetch data for the given zone."""
    from datetime import date
    today = date.today()
    url = (
        f"https://www.elprisetjustnu.se/api/v1/prices/"
        f"{today.year}/{today.month:02d}-{today.day:02d}_{zone}.json"
    )
    session = aiohttp.ClientSession()
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            return resp.status == 200
    except Exception:
        return False
    finally:
        await session.close()


class ElprisetJustNuConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Elpriset Just Nu."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 1: choose price zone and friendly name."""
        errors: dict[str, str] = {}

        if user_input is not None:
            zone = user_input[CONF_PRICE_ZONE]
            name = user_input.get(CONF_NAME, "").strip() or PRICE_ZONES[zone]

            await self.async_set_unique_id(zone)
            self._abort_if_unique_id_configured()

            try:
                valid = await _validate_zone(self.hass, zone)
                if not valid:
                    errors["base"] = "cannot_connect"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception during zone validation")
                errors["base"] = "unknown"

            if not errors:
                self._data = {CONF_PRICE_ZONE: zone, CONF_NAME: name}
                return await self.async_step_surcharges()

        schema = vol.Schema(
            {
                vol.Required(CONF_PRICE_ZONE): vol.In(PRICE_ZONES),
                vol.Optional(CONF_NAME, default=""): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_surcharges(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 2: optional contract surcharges (påslag + moms)."""
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title=self._data[CONF_NAME], data=self._data)

        schema = vol.Schema(
            {
                vol.Optional(CONF_SURCHARGE_SPOT_MARKUP, default=0.0): vol.Coerce(float),
                vol.Optional(CONF_SURCHARGE_VARIABLE_COSTS, default=0.0): vol.Coerce(float),
                vol.Optional(CONF_SURCHARGE_ELCERT, default=0.0): vol.Coerce(float),
                vol.Optional(CONF_SURCHARGE_OTHER, default=0.0): vol.Coerce(float),
                vol.Optional(CONF_VAT_PERCENT, default=DEFAULT_VAT_PERCENT): vol.All(
                    vol.Coerce(float), vol.Range(min=0.0, max=100.0)
                ),
            }
        )

        return self.async_show_form(
            step_id="surcharges",
            data_schema=schema,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "ElprisetJustNuOptionsFlow":
        """Get the options flow."""
        return ElprisetJustNuOptionsFlow()


class ElprisetJustNuOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Elpriset Just Nu.

    Note: self.config_entry is set automatically by OptionsFlow base class
    in HA 2024.x+. Do not pass it via __init__.
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage update interval and surcharge overrides."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data = self.config_entry.data
        opts = self.config_entry.options

        def _get(key: str, default: Any) -> Any:
            return opts.get(key, data.get(key, default))

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_UPDATE_INTERVAL,
                    default=_get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                ),
                vol.Optional(
                    CONF_SURCHARGE_SPOT_MARKUP,
                    default=_get(CONF_SURCHARGE_SPOT_MARKUP, 0.0),
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_SURCHARGE_VARIABLE_COSTS,
                    default=_get(CONF_SURCHARGE_VARIABLE_COSTS, 0.0),
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_SURCHARGE_ELCERT,
                    default=_get(CONF_SURCHARGE_ELCERT, 0.0),
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_SURCHARGE_OTHER,
                    default=_get(CONF_SURCHARGE_OTHER, 0.0),
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_VAT_PERCENT,
                    default=_get(CONF_VAT_PERCENT, DEFAULT_VAT_PERCENT),
                ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=100.0)),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
