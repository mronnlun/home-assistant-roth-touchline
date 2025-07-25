"""Test configuration for Roth Touchline integration."""
import pytest
from unittest.mock import patch
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.roth_touchline.const import DOMAIN


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": "192.168.1.100",
            "port": 80,
        },
        unique_id="192.168.1.100",
    )


@pytest.fixture
async def mock_roth_touchline_hub():
    """Mock RothTouchlineHub."""
    with patch("custom_components.roth_touchline.hub.RothTouchlineHub") as mock_hub:
        hub_instance = mock_hub.return_value
        hub_instance.test_connection.return_value = True
        hub_instance.get_zones.return_value = [
            {"id": "zone1", "name": "Living Room"},
            {"id": "zone2", "name": "Bedroom"},
        ]
        hub_instance.get_zone_data.return_value = {
            "id": "zone1",
            "name": "Living Room",
            "current_temperature": 20.5,
            "target_temperature": 21.0,
            "hvac_mode": 1,
            "humidity": 45,
            "battery_level": 85,
            "heating": True,
            "cooling": False,
            "online": True,
            "battery_low": False,
        }
        yield hub_instance
