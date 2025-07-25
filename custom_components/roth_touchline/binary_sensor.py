"""Binary sensor platform for Roth Touchline integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import RothTouchlineDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

BINARY_SENSOR_TYPES = {
    "heating": {
        "name": "Heating",
        "device_class": BinarySensorDeviceClass.HEAT,
    },
    "cooling": {
        "name": "Cooling", 
        "device_class": BinarySensorDeviceClass.COLD,
    },
    "online": {
        "name": "Online",
        "device_class": BinarySensorDeviceClass.CONNECTIVITY,
    },
    "battery_low": {
        "name": "Battery Low",
        "device_class": BinarySensorDeviceClass.BATTERY,
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Roth Touchline binary sensor platform."""
    coordinator: RothTouchlineDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]["coordinator"]

    entities = []
    for zone_id, zone_data in coordinator.data.items():
        for sensor_type, sensor_config in BINARY_SENSOR_TYPES.items():
            if sensor_type in zone_data:
                entities.append(
                    RothTouchlineBinarySensor(
                        coordinator, zone_id, zone_data, sensor_type, sensor_config
                    )
                )

    async_add_entities(entities)


class RothTouchlineBinarySensor(CoordinatorEntity[RothTouchlineDataUpdateCoordinator], BinarySensorEntity):
    """Representation of a Roth Touchline binary sensor."""

    def __init__(
        self,
        coordinator: RothTouchlineDataUpdateCoordinator,
        zone_id: str,
        zone_data: dict[str, Any],
        sensor_type: str,
        sensor_config: dict[str, Any],
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._zone_id = zone_id
        self._sensor_type = sensor_type
        self._sensor_config = sensor_config
        
        zone_name = zone_data.get("name", zone_id)
        self._attr_unique_id = f"{DOMAIN}_{zone_id}_{sensor_type}"
        self._attr_name = f"Roth Touchline {zone_name} {sensor_config['name']}"
        self._attr_device_class = sensor_config.get("device_class")

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._zone_id)},
            "name": f"Roth Touchline Zone {self._zone_id}",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "sw_version": "1.0.0",
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        zone_data = self.coordinator.data.get(self._zone_id, {})
        return zone_data.get(self._sensor_type, False)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
