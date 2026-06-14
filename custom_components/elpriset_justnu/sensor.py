"""Sensor platform for Elpriset Just Nu."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ATTRIBUTION,
    ATTRIBUTION,
    CONF_NAME,
    CONF_PRICE_ZONE,
    CONF_SURCHARGE_ELCERT,
    CONF_SURCHARGE_OTHER,
    CONF_SURCHARGE_SPOT_MARKUP,
    CONF_SURCHARGE_VARIABLE_COSTS,
    CONF_VAT_PERCENT,
    DOMAIN,
    PRICE_ZONES,
    SENSOR_AVERAGE_PRICE,
    SENSOR_CURRENT_PRICE,
    SENSOR_MAX_PRICE,
    SENSOR_MIN_PRICE,
    SENSOR_NEXT_HOUR_PRICE,
    SENSOR_PRICES_TODAY,
    SENSOR_PRICES_TOMORROW,
    SENSOR_TOMORROW_AVAILABLE,
    SENSOR_TOTAL_AVERAGE,
    SENSOR_TOTAL_CURRENT,
    SENSOR_TOTAL_MAX,
    SENSOR_TOTAL_MIN,
    SENSOR_TOTAL_NEXT_HOUR,
    UNIT_ORE_PER_KWH,
    UNIT_SEK_PER_KWH,
)
from .coordinator import ElprisetJustNuCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class ElprisetSensorEntityDescription(SensorEntityDescription):
    """Describe an Elpriset sensor."""
    requires_surcharges: bool = False


# ── Spot price sensors (SEK/kWh, always shown) ───────────────────────────────
_SPOT_SENSORS: tuple[ElprisetSensorEntityDescription, ...] = (
    ElprisetSensorEntityDescription(
        key=SENSOR_CURRENT_PRICE,
        name="Current Spot Price",
        native_unit_of_measurement=UNIT_SEK_PER_KWH,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:lightning-bolt",
    ),
    ElprisetSensorEntityDescription(
        key=SENSOR_NEXT_HOUR_PRICE,
        name="Next Hour Spot Price",
        native_unit_of_measurement=UNIT_SEK_PER_KWH,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:lightning-bolt-outline",
    ),
    ElprisetSensorEntityDescription(
        key=SENSOR_AVERAGE_PRICE,
        name="Average Spot Price Today",
        native_unit_of_measurement=UNIT_SEK_PER_KWH,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:approximately-equal",
    ),
    ElprisetSensorEntityDescription(
        key=SENSOR_MIN_PRICE,
        name="Min Spot Price Today",
        native_unit_of_measurement=UNIT_SEK_PER_KWH,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:arrow-down-bold",
    ),
    ElprisetSensorEntityDescription(
        key=SENSOR_MAX_PRICE,
        name="Max Spot Price Today",
        native_unit_of_measurement=UNIT_SEK_PER_KWH,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:arrow-up-bold",
    ),
    ElprisetSensorEntityDescription(
        key=SENSOR_PRICES_TODAY,
        name="Prices Today",
        native_unit_of_measurement=None,
        device_class=None,
        state_class=None,
        icon="mdi:chart-line",
    ),
    ElprisetSensorEntityDescription(
        key=SENSOR_PRICES_TOMORROW,
        name="Prices Tomorrow",
        native_unit_of_measurement=None,
        device_class=None,
        state_class=None,
        icon="mdi:chart-line-variant",
    ),
    ElprisetSensorEntityDescription(
        key=SENSOR_TOMORROW_AVAILABLE,
        name="Tomorrow Prices Available",
        native_unit_of_measurement=None,
        device_class=SensorDeviceClass.ENUM,
        state_class=None,
        icon="mdi:calendar-check",
    ),
)

# ── Total price sensors (öre/kWh, only created when surcharges configured) ───
_TOTAL_SENSORS: tuple[ElprisetSensorEntityDescription, ...] = (
    ElprisetSensorEntityDescription(
        key=SENSOR_TOTAL_CURRENT,
        name="Current Total Price",
        native_unit_of_measurement=UNIT_ORE_PER_KWH,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:cash-clock",
        requires_surcharges=True,
    ),
    ElprisetSensorEntityDescription(
        key=SENSOR_TOTAL_NEXT_HOUR,
        name="Next Hour Total Price",
        native_unit_of_measurement=UNIT_ORE_PER_KWH,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:cash-fast",
        requires_surcharges=True,
    ),
    ElprisetSensorEntityDescription(
        key=SENSOR_TOTAL_AVERAGE,
        name="Average Total Price Today",
        native_unit_of_measurement=UNIT_ORE_PER_KWH,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:cash-multiple",
        requires_surcharges=True,
    ),
    ElprisetSensorEntityDescription(
        key=SENSOR_TOTAL_MIN,
        name="Min Total Price Today",
        native_unit_of_measurement=UNIT_ORE_PER_KWH,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:cash-minus",
        requires_surcharges=True,
    ),
    ElprisetSensorEntityDescription(
        key=SENSOR_TOTAL_MAX,
        name="Max Total Price Today",
        native_unit_of_measurement=UNIT_ORE_PER_KWH,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:cash-plus",
        requires_surcharges=True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Elpriset Just Nu sensors from a config entry."""
    coordinator: ElprisetJustNuCoordinator = hass.data[DOMAIN][entry.entry_id]
    has_surcharges = coordinator.data.get("has_surcharges", False)

    entities = [
        ElprisetSensor(coordinator, entry, desc)
        for desc in _SPOT_SENSORS
    ]
    if has_surcharges:
        entities += [
            ElprisetSensor(coordinator, entry, desc)
            for desc in _TOTAL_SENSORS
        ]

    async_add_entities(entities)


class ElprisetSensor(CoordinatorEntity[ElprisetJustNuCoordinator], SensorEntity):
    """A sensor entity for an Elpriset Just Nu data point."""

    entity_description: ElprisetSensorEntityDescription

    def __init__(
        self,
        coordinator: ElprisetJustNuCoordinator,
        entry: ConfigEntry,
        description: ElprisetSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        zone = entry.data[CONF_PRICE_ZONE]
        friendly_name = entry.data.get(CONF_NAME, PRICE_ZONES[zone])

        self._attr_unique_id = f"{DOMAIN}_{zone}_{description.key}"
        self._attr_name = f"{friendly_name} {description.name}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, zone)},
            name=friendly_name,
            manufacturer="Elpriset just nu.se",
            model=PRICE_ZONES.get(zone, zone),
            entry_type="service",
        )

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data
        if data is None:
            return None
        key = self.entity_description.key

        # ── Spot sensors ──────────────────────────────────────────────────────
        if key == SENSOR_CURRENT_PRICE:
            e = data.get("current")
            return round(e["SEK_per_kWh"], 5) if e else None

        if key == SENSOR_NEXT_HOUR_PRICE:
            e = data.get("next_hour")
            return round(e["SEK_per_kWh"], 5) if e else None

        if key == SENSOR_AVERAGE_PRICE:
            return data.get("average_today")

        if key == SENSOR_MIN_PRICE:
            return data.get("min_today")

        if key == SENSOR_MAX_PRICE:
            return data.get("max_today")

        if key == SENSOR_PRICES_TODAY:
            return len(data.get("today", []))

        if key == SENSOR_PRICES_TOMORROW:
            return len(data.get("tomorrow", []))

        if key == SENSOR_TOMORROW_AVAILABLE:
            return "Yes" if data.get("tomorrow_available") else "No"

        # ── Total price sensors (öre/kWh incl. surcharges + VAT) ─────────────
        if key == SENSOR_TOTAL_CURRENT:
            return data.get("total_current")

        if key == SENSOR_TOTAL_NEXT_HOUR:
            return data.get("total_next_hour")

        if key == SENSOR_TOTAL_AVERAGE:
            return data.get("total_average_today")

        if key == SENSOR_TOTAL_MIN:
            return data.get("total_min_today")

        if key == SENSOR_TOTAL_MAX:
            return data.get("total_max_today")

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data
        attrs: dict[str, Any] = {ATTR_ATTRIBUTION: ATTRIBUTION}
        if data is None:
            return attrs

        key = self.entity_description.key

        if key == SENSOR_CURRENT_PRICE:
            e = data.get("current")
            if e:
                attrs.update({
                    "EUR_per_kWh": e.get("EUR_per_kWh"),
                    "exchange_rate_EUR_SEK": e.get("EXR"),
                    "time_start": e.get("time_start"),
                    "time_end": e.get("time_end"),
                })

        elif key == SENSOR_NEXT_HOUR_PRICE:
            e = data.get("next_hour")
            if e:
                attrs.update({
                    "EUR_per_kWh": e.get("EUR_per_kWh"),
                    "time_start": e.get("time_start"),
                    "time_end": e.get("time_end"),
                })

        elif key == SENSOR_PRICES_TODAY:
            attrs["prices"] = [
                {
                    "SEK_per_kWh": e["SEK_per_kWh"],
                    "EUR_per_kWh": e["EUR_per_kWh"],
                    "time_start": e["time_start"],
                    "time_end": e["time_end"],
                }
                for e in data.get("today", [])
            ]

        elif key == SENSOR_PRICES_TOMORROW:
            attrs["prices"] = [
                {
                    "SEK_per_kWh": e["SEK_per_kWh"],
                    "EUR_per_kWh": e["EUR_per_kWh"],
                    "time_start": e["time_start"],
                    "time_end": e["time_end"],
                }
                for e in data.get("tomorrow", [])
            ]

        elif key == SENSOR_TOTAL_CURRENT:
            surcharges = data.get("surcharges", {})
            e = data.get("current")
            attrs.update({
                "spot_ore_per_kWh": round(e["SEK_per_kWh"] * 100, 2) if e else None,
                "fast_påslag_spot_ore": surcharges.get(CONF_SURCHARGE_SPOT_MARKUP, 0.0),
                "rörliga_kostnader_ore": surcharges.get(CONF_SURCHARGE_VARIABLE_COSTS, 0.0),
                "fast_påslag_elcert_ore": surcharges.get(CONF_SURCHARGE_ELCERT, 0.0),
                "övrigt_påslag_ore": surcharges.get(CONF_SURCHARGE_OTHER, 0.0),
                "moms_percent": surcharges.get(CONF_VAT_PERCENT, 25.0),
                "time_start": e.get("time_start") if e else None,
                "time_end": e.get("time_end") if e else None,
            })

        elif key in (SENSOR_TOTAL_AVERAGE, SENSOR_TOTAL_MIN, SENSOR_TOTAL_MAX):
            surcharges = data.get("surcharges", {})
            attrs.update({
                "fast_påslag_spot_ore": surcharges.get(CONF_SURCHARGE_SPOT_MARKUP, 0.0),
                "rörliga_kostnader_ore": surcharges.get(CONF_SURCHARGE_VARIABLE_COSTS, 0.0),
                "fast_påslag_elcert_ore": surcharges.get(CONF_SURCHARGE_ELCERT, 0.0),
                "övrigt_påslag_ore": surcharges.get(CONF_SURCHARGE_OTHER, 0.0),
                "moms_percent": surcharges.get(CONF_VAT_PERCENT, 25.0),
            })

        attrs["last_updated"] = data.get("last_updated")
        attrs["price_zone"] = data.get("zone")
        return attrs
