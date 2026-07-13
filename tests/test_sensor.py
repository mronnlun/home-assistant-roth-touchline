"""Tests for Roth Touchline sensors."""

from unittest.mock import MagicMock

from custom_components.roth_touchline.const import DOMAIN, SENSOR_TYPES
from custom_components.roth_touchline.sensor import RothTouchlineSensor


def test_controller_identity_prevents_collisions() -> None:
    """Equal zone numbers on different controllers have distinct identifiers."""
    coordinator = MagicMock()
    zone_data = {"name": "Living room", "current_temperature": 20.5}

    first = RothTouchlineSensor(
        coordinator=coordinator,
        controller_id="controller-a:80",
        zone_id="G0",
        zone_data=zone_data,
        sensor_type="current_temperature",
        sensor_config=SENSOR_TYPES["current_temperature"],
    )
    second = RothTouchlineSensor(
        coordinator=coordinator,
        controller_id="controller-b:80",
        zone_id="G0",
        zone_data=zone_data,
        sensor_type="current_temperature",
        sensor_config=SENSOR_TYPES["current_temperature"],
    )

    assert first.unique_id != second.unique_id
    assert first.device_info["identifiers"] == {(DOMAIN, "controller-a:80_G0")}
    assert first.device_info["identifiers"] != second.device_info["identifiers"]
