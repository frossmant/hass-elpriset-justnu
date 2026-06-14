# hass-elpriset-justnu

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Home Assistant integration for Swedish electricity spot prices via [Elpriset just nu.se](https://www.elprisetjustnu.se).

Data is free, open and sourced directly from [entsoe.eu](https://transparency.entsoe.eu/).  
Prices are **excluding VAT, surcharges and taxes** (spot price only).

> Elpriser tillhandahålls av [Elpriset just nu.se](https://www.elprisetjustnu.se)

---

## Features

- Add **multiple price zones** via the standard Home Assistant GUI — one entry per zone
- Live current-hour price sensor (updates on coordinator schedule)
- Sensors for next-hour price, daily min/max/average
- Full hourly price list for today (and tomorrow, once published after ~13:00) as sensor attributes
- Quarter-hour prices from 1 October 2025 (96 slots/day instead of 24)
- Options flow to adjust the update interval per zone

## Supported Zones

| Zone | Region |
|------|--------|
| SE1  | Luleå / Norra Sverige |
| SE2  | Sundsvall / Norra Mellansverige |
| SE3  | Stockholm / Södra Mellansverige |
| SE4  | Malmö / Södra Sverige |

## Installation

### Via HACS (recommended)

1. Go to **HACS → Integrations**
2. Click **⋮ → Custom repositories**
3. Add:
   ```
   Repository: https://github.com/frossmant/hass-elpriset-justnu
   Type: Integration
   ```
4. Click **Add**, then install **Elpriset Just Nu**
5. **Restart** Home Assistant

### Manual

Copy `custom_components/elpriset_justnu/` into your HA `custom_components/` folder and restart.

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Elpriset Just Nu**
3. Select a **price zone** from the dropdown
4. Optionally set a **friendly name**
5. Repeat for each zone you want to monitor

## Sensors Created

For each configured zone the following sensors are created:

| Sensor | Description |
|--------|-------------|
| `current_price` | Spot price for the current hour (SEK/kWh) |
| `next_hour_price` | Spot price for the next hour (SEK/kWh) |
| `average_price_today` | Mean spot price across today (SEK/kWh) |
| `min_price_today` | Cheapest slot today (SEK/kWh) |
| `max_price_today` | Most expensive slot today (SEK/kWh) |
| `prices_today` | Count of slots; full list in `attributes.prices` |
| `prices_tomorrow` | Count of slots; full list in `attributes.prices` |
| `tomorrow_prices_available` | Yes / No — whether tomorrow's data has been published |

## Example Dashboard

See [example.yaml](example.yaml) for Lovelace card examples including an apexcharts-card price graph and an automation that alerts when the price drops below a threshold.

## Changelog

See [CHANGELOG](CHANGELOG).

## License

GPL v3 — see [LICENSE](LICENSE).
