"""DataUpdateCoordinator for Roth Touchline integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, UPDATE_INTERVAL
from .hub import RothTouchlineHub

_LOGGER = logging.getLogger(__name__)


class RothTouchlineDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from the Roth Touchline system."""

    def __init__(self, hass: HomeAssistant, hub: RothTouchlineHub) -> None:
        """Initialize."""
        self.hub = hub
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            zones = await self.hub.get_zones()
            data = {}
            
            for zone in zones:
                zone_id = zone.get("id")
                if zone_id:
                    # Get current zone data via XML API
                    zone_data = await self.hub.get_zone_data(zone_id)
                    if zone_data:
                        # Note: Daily statistics may not be available via XML API
                        # Commenting out daily stats for now
                        # daily_stats = await self.hub.get_daily_temperature_stats(zone_id)
                        # if daily_stats:
                        #     zone_data.update({
                        #         "daily_avg_temperature": daily_stats.get("avg_temperature"),
                        #         "daily_min_temperature": daily_stats.get("min_temperature"),
                        #         "daily_max_temperature": daily_stats.get("max_temperature"),
                        #     })
                        
                        # Add last seen timestamp
                        zone_data["last_seen"] = zone_data.get("timestamp") or "Unknown"
                        
                        data[zone_id] = zone_data

            _LOGGER.debug("Updated temperature data for %d zones via XML API", len(data))
            return data
            
        except Exception as err:
            _LOGGER.error("Error communicating with Roth Touchline XML API: %s", err)
            raise UpdateFailed(f"Error communicating with XML API: {err}") from err
