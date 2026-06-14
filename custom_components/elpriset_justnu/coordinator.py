"""Data update coordinator for Elpriset Just Nu."""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_BASE_URL,
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

_LOGGER = logging.getLogger(__name__)


def _total_ore(spot_sek: float, surcharges: dict[str, float]) -> float:
    """Calculate total consumer price in öre/kWh including all surcharges and VAT.

    spot_sek  — spot price in SEK/kWh (from API)
    surcharges — dict with the four markup fields + vat_percent

    Formula:
        total = (spot_öre + påslag_spot + rörliga + elcert + other) * (1 + VAT/100)
    """
    spot_ore = spot_sek * 100.0
    fixed_ore = (
        surcharges.get(CONF_SURCHARGE_SPOT_MARKUP, 0.0)
        + surcharges.get(CONF_SURCHARGE_VARIABLE_COSTS, 0.0)
        + surcharges.get(CONF_SURCHARGE_ELCERT, 0.0)
        + surcharges.get(CONF_SURCHARGE_OTHER, 0.0)
    )
    vat_factor = 1.0 + surcharges.get(CONF_VAT_PERCENT, DEFAULT_VAT_PERCENT) / 100.0
    return round((spot_ore + fixed_ore) * vat_factor, 2)


class ElprisetJustNuCoordinator(DataUpdateCoordinator):
    """Fetch and cache electricity price data from elprisetjustnu.se."""

    def __init__(
        self,
        hass: HomeAssistant,
        price_zone: str,
        surcharges: dict[str, float],
        update_interval_minutes: int = DEFAULT_UPDATE_INTERVAL,
    ) -> None:
        self.price_zone = price_zone
        self.surcharges = surcharges
        self._session: aiohttp.ClientSession | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{price_zone}",
            update_interval=timedelta(minutes=update_interval_minutes),
        )

    def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _fetch_prices(self, target_date: date) -> list[dict]:
        url = (
            f"{API_BASE_URL}/{target_date.year}/"
            f"{target_date.month:02d}-{target_date.day:02d}_{self.price_zone}.json"
        )
        session = self._get_session()
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 404:
                    return []
                if resp.status != 200:
                    raise UpdateFailed(f"API returned HTTP {resp.status} for {url}")
                return await resp.json()
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Network error fetching {url}: {err}") from err

    async def _async_update_data(self) -> dict[str, Any]:
        now = datetime.now().astimezone()
        today = now.date()
        tomorrow = today + timedelta(days=1)

        today_prices = await self._fetch_prices(today)
        if not today_prices:
            raise UpdateFailed(f"No price data for {self.price_zone} on {today}")

        tomorrow_prices = await self._fetch_prices(tomorrow)

        current_entry = None
        next_entry = None
        for i, entry in enumerate(today_prices):
            start = datetime.fromisoformat(entry["time_start"])
            end = datetime.fromisoformat(entry["time_end"])
            if start <= now < end:
                current_entry = entry
                if i + 1 < len(today_prices):
                    next_entry = today_prices[i + 1]
                elif tomorrow_prices:
                    next_entry = tomorrow_prices[0]
                break

        sek_today = [e["SEK_per_kWh"] for e in today_prices]
        has_surcharges = any(
            self.surcharges.get(k, 0.0) != 0.0
            for k in (
                CONF_SURCHARGE_SPOT_MARKUP,
                CONF_SURCHARGE_VARIABLE_COSTS,
                CONF_SURCHARGE_ELCERT,
                CONF_SURCHARGE_OTHER,
            )
        )

        ore_today = [_total_ore(s, self.surcharges) for s in sek_today] if has_surcharges else []

        return {
            "zone": self.price_zone,
            "today": today_prices,
            "tomorrow": tomorrow_prices,
            "tomorrow_available": len(tomorrow_prices) > 0,
            "current": current_entry,
            "next_hour": next_entry,
            # Spot stats (SEK/kWh)
            "average_today": round(sum(sek_today) / len(sek_today), 5) if sek_today else None,
            "min_today": round(min(sek_today), 5) if sek_today else None,
            "max_today": round(max(sek_today), 5) if sek_today else None,
            # Total stats (öre/kWh, only set when surcharges configured)
            "has_surcharges": has_surcharges,
            "surcharges": self.surcharges,
            "total_current": (
                _total_ore(current_entry["SEK_per_kWh"], self.surcharges)
                if has_surcharges and current_entry
                else None
            ),
            "total_next_hour": (
                _total_ore(next_entry["SEK_per_kWh"], self.surcharges)
                if has_surcharges and next_entry
                else None
            ),
            "total_average_today": (
                round(sum(ore_today) / len(ore_today), 2) if ore_today else None
            ),
            "total_min_today": round(min(ore_today), 2) if ore_today else None,
            "total_max_today": round(max(ore_today), 2) if ore_today else None,
            "last_updated": now.isoformat(),
        }

    async def async_shutdown(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
        await super().async_shutdown()
