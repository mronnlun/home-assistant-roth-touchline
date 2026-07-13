"""Sensor platform for Roth Touchline integration."""

from __future__ import annotations

from datetime import UTC, datetime
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL, SENSOR_TYPES
from .coordinator import RothTouchlineDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Roth Touchline sensor platform."""
    coordinator: RothTouchlineDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]["coordinator"]
    controller_id: str = hass.data[DOMAIN][config_entry.entry_id]["controller_id"]

    entities = []
    for zone_id, zone_data in coordinator.data.items():
        for sensor_type, sensor_config in SENSOR_TYPES.items():
            # Always create last_seen sensor, and create others only if data exists
            if sensor_type == "last_seen" or sensor_type in zone_data:
                entities.append(
                    RothTouchlineSensor(
                        coordinator=coordinator,
                        controller_id=controller_id,
                        zone_id=zone_id,
                        zone_data=zone_data,
                        sensor_type=sensor_type,
                        sensor_config=sensor_config,
                    )
                )

    async_add_entities(entities)


class RothTouchlineSensor(
    CoordinatorEntity[RothTouchlineDataUpdateCoordinator], SensorEntity
):
    """Representation of a Roth Touchline sensor."""

    def __init__(
        self,
        *,
        coordinator: RothTouchlineDataUpdateCoordinator,
        controller_id: str,
        zone_id: str,
        zone_data: dict[str, Any],
        sensor_type: str,
        sensor_config: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._controller_id = controller_id
        self._zone_id = zone_id
        self._sensor_type = sensor_type
        self._sensor_config = sensor_config

        zone_name = zone_data.get("name", zone_id)
        self._attr_unique_id = f"{controller_id}_{zone_id}_{sensor_type}"
        self._attr_name = f"Roth Touchline {zone_name} {sensor_config['name']}"

        # Set sensor attributes
        self._attr_native_unit_of_measurement = sensor_config.get("unit")
        self._attr_icon = sensor_config.get("icon")

        device_class = sensor_config.get("device_class")
        if device_class == "temperature":
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
        elif device_class == "timestamp":
            self._attr_device_class = SensorDeviceClass.TIMESTAMP

        state_class = sensor_config.get("state_class")
        if state_class == "measurement":
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._controller_id}_{self._zone_id}")},
            name=f"Roth Touchline Zone {self._zone_id}",
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    @property
    def native_value(self) -> float | int | str | datetime | None:
        """Return the state of the sensor."""
        zone_data = self.coordinator.data.get(self._zone_id, {})
        value = zone_data.get(self._sensor_type)

        # For timestamp sensors, ensure we return a timezone-aware datetime object
        if self._sensor_type == "last_seen":
            if isinstance(value, datetime):
                # If datetime is naive, assume it's UTC
                if value.tzinfo is None:
                    return value.replace(tzinfo=UTC)
                return value
            if isinstance(value, str):
                try:
                    # Handle different string formats
                    if value.endswith("Z"):
                        # ISO format with Z suffix
                        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    elif "+" in value or value.endswith("+00:00"):
                        # ISO format with timezone offset
                        dt = datetime.fromisoformat(value)
                    else:
                        # Naive datetime string - assume UTC
                        dt = datetime.fromisoformat(value)
                        dt = dt.replace(tzinfo=UTC)

                    # Ensure result has timezone info
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=UTC)
                    return dt
                except (ValueError, AttributeError) as e:
                    _LOGGER.warning("Failed to parse timestamp '%s': %s", value, e)
                    return None
            return None

        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes for temperature logging."""
        zone_data = self.coordinator.data.get(self._zone_id, {})

        return {
            "zone_id": self._zone_id,
            "zone_name": zone_data.get("name", self._zone_id),
            "last_updated": zone_data.get("timestamp"),
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
