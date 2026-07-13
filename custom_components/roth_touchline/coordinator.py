"""DataUpdateCoordinator for Roth Touchline integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .hub import RothTouchlineCommunicationError, RothTouchlineHub

_LOGGER = logging.getLogger(__name__)


class RothTouchlineDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from the Roth Touchline system."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        hub: RothTouchlineHub,
        update_interval_seconds: int = 300,
    ) -> None:
        """Initialize."""
        self.hub = hub
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval_seconds),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            data = await self.hub.get_zone_data()
        except RothTouchlineCommunicationError as err:
            raise UpdateFailed(f"Error communicating with controller: {err}") from err

        _LOGGER.debug("Updated temperature data for %d zones", len(data))
        return data
