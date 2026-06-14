"""The Elpriset Just Nu integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
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
)
from .coordinator import ElprisetJustNuCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.SENSOR]


def _get_surcharges(entry: ConfigEntry) -> dict:
    """Merge surcharge values from options (takes priority) then data."""
    result = {}
    keys = (
        CONF_SURCHARGE_SPOT_MARKUP,
        CONF_SURCHARGE_VARIABLE_COSTS,
        CONF_SURCHARGE_ELCERT,
        CONF_SURCHARGE_OTHER,
        CONF_VAT_PERCENT,
    )
    defaults = {CONF_VAT_PERCENT: DEFAULT_VAT_PERCENT}
    for k in keys:
        result[k] = entry.options.get(k, entry.data.get(k, defaults.get(k, 0.0)))
    return result


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Elpriset Just Nu from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    zone = entry.data[CONF_PRICE_ZONE]
    update_interval = entry.options.get(
        CONF_UPDATE_INTERVAL,
        entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
    )

    coordinator = ElprisetJustNuCoordinator(
        hass,
        price_zone=zone,
        surcharges=_get_surcharges(entry),
        update_interval_minutes=update_interval,
    )

    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: ElprisetJustNuCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()
    return unload_ok
