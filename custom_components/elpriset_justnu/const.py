"""Constants for the Elpriset Just Nu integration."""

DOMAIN = "elpriset_justnu"

# API
API_BASE_URL = "https://www.elprisetjustnu.se/api/v1/prices"

# Price zones
PRICE_ZONES = {
    "SE1": "Luleå / SE1 (Norra Sverige)",
    "SE2": "Sundsvall / SE2 (Norra Mellansverige)",
    "SE3": "Stockholm / SE3 (Södra Mellansverige)",
    "SE4": "Malmö / SE4 (Södra Sverige)",
}

# Config keys
CONF_PRICE_ZONE = "price_zone"
CONF_NAME = "name"
CONF_UPDATE_INTERVAL = "update_interval"

# Surcharge config keys (all in öre/kWh)
CONF_SURCHARGE_SPOT_MARKUP = "surcharge_spot_markup"       # Fast påslag spot
CONF_SURCHARGE_VARIABLE_COSTS = "surcharge_variable_costs"  # Rörliga kostnader
CONF_SURCHARGE_ELCERT = "surcharge_elcert"                  # Fast påslag elcertifikat
CONF_SURCHARGE_OTHER = "surcharge_other"                    # Any other fixed markup
CONF_VAT_PERCENT = "vat_percent"                            # VAT %, typically 25

# Defaults
DEFAULT_UPDATE_INTERVAL = 60  # minutes
MIN_UPDATE_INTERVAL = 15
MAX_UPDATE_INTERVAL = 240
DEFAULT_VAT_PERCENT = 25.0

# Sensor names — spot (raw)
SENSOR_CURRENT_PRICE = "current_price"
SENSOR_AVERAGE_PRICE = "average_price_today"
SENSOR_MIN_PRICE = "min_price_today"
SENSOR_MAX_PRICE = "max_price_today"
SENSOR_NEXT_HOUR_PRICE = "next_hour_price"
SENSOR_PRICES_TODAY = "prices_today"
SENSOR_PRICES_TOMORROW = "prices_tomorrow"
SENSOR_TOMORROW_AVAILABLE = "tomorrow_prices_available"

# Sensor names — total (spot + surcharges + VAT), in öre/kWh
SENSOR_TOTAL_CURRENT = "total_price_current"
SENSOR_TOTAL_NEXT_HOUR = "total_price_next_hour"
SENSOR_TOTAL_AVERAGE = "total_price_average_today"
SENSOR_TOTAL_MIN = "total_price_min_today"
SENSOR_TOTAL_MAX = "total_price_max_today"

# Units
UNIT_SEK_PER_KWH = "SEK/kWh"
UNIT_EUR_PER_KWH = "EUR/kWh"
UNIT_ORE_PER_KWH = "öre/kWh"

# Attribution
ATTRIBUTION = "Data provided by Elpriset just nu.se"
ATTR_ATTRIBUTION = "attribution"
