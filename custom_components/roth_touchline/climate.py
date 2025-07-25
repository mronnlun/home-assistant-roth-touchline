"""Climate platform for Roth Touchline integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    HVAC_MODES_ROTH,
    MANUFACTURER,
    MODEL,
    ROTH_HVAC_MODES,
)
from .coordinator import RothTouchlineDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Roth Touchline climate platform."""
    coordinator: RothTouchlineDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]["coordinator"]
    hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]

    entities = []
    for zone_id, zone_data in coordinator.data.items():
        entities.append(RothTouchlineClimate(coordinator, hub, zone_id, zone_data))

    async_add_entities(entities)


class RothTouchlineClimate(CoordinatorEntity[RothTouchlineDataUpdateCoordinator], ClimateEntity):
    """Representation of a Roth Touchline climate entity."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    # Note: Removed TARGET_TEMPERATURE feature as XML API may not support setting temperature
    # Only providing monitoring capabilities for now
    _attr_supported_features = ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.AUTO]

    def __init__(
        self,
        coordinator: RothTouchlineDataUpdateCoordinator,
        hub,
        zone_id: str,
        zone_data: dict[str, Any],
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._hub = hub
        self._zone_id = zone_id
        self._attr_unique_id = f"{DOMAIN}_{zone_id}_climate"
        self._attr_name = f"Roth Touchline {zone_data.get('name', zone_id)}"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._zone_id)},
            "name": self.name,
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "sw_version": "1.0.0",
        }

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        zone_data = self.coordinator.data.get(self._zone_id, {})
        return zone_data.get("current_temperature")

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        zone_data = self.coordinator.data.get(self._zone_id, {})
        return zone_data.get("target_temperature")

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return current HVAC mode."""
        zone_data = self.coordinator.data.get(self._zone_id, {})
        roth_mode = zone_data.get("hvac_mode")
        if roth_mode is not None:
            return ROTH_HVAC_MODES.get(roth_mode, HVACMode.OFF)
        return HVACMode.OFF

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        # Note: This may not work with Roth Touchline XML API
        # Temperature setting capability needs to be verified
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is not None:
            success = await self._hub.set_temperature(self._zone_id, temperature)
            if success:
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.warning("Failed to set temperature for zone %s", self._zone_id)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode."""
        # Note: This may not work with Roth Touchline XML API
        # HVAC mode setting capability needs to be verified
        roth_mode = HVAC_MODES_ROTH.get(hvac_mode)
        if roth_mode is not None:
            success = await self._hub.set_hvac_mode(self._zone_id, roth_mode)
            if success:
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.warning("Failed to set HVAC mode for zone %s", self._zone_id)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
