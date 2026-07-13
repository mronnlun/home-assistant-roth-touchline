"""Tests for Roth Touchline config-entry lifecycle behavior."""

from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.roth_touchline import async_migrate_entry
from custom_components.roth_touchline.const import (
    CONF_MAX_ZONES,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
)
from custom_components.roth_touchline.hub import RothTouchlineCommunicationError

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")

ZONE_DATA = {
    "G0": {
        "id": "G0",
        "name": "Living room",
        "current_temperature": 20.5,
        "target_temperature": 21.0,
        "timestamp": None,
        "last_seen": None,
    }
}


def _config_entry(host: str, *, port: int = 80, version: int = 2) -> MockConfigEntry:
    """Create a configured Roth Touchline entry."""
    unique_id = host if version == 1 else f"{host}:{port}"
    return MockConfigEntry(
        domain=DOMAIN,
        title=f"Roth Touchline ({host})",
        data={
            CONF_HOST: host,
            CONF_PORT: port,
            CONF_MAX_ZONES: 10,
            CONF_UPDATE_INTERVAL: 300,
        },
        unique_id=unique_id,
        version=version,
    )


async def _setup_entry(hass: HomeAssistant, entry: MockConfigEntry) -> AsyncMock:
    """Set up an entry with a mocked controller."""
    entry.add_to_hass(hass)
    with patch("custom_components.roth_touchline.RothTouchlineHub") as hub_class:
        hub = hub_class.return_value
        hub.get_zone_data = AsyncMock(return_value=ZONE_DATA)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return hub


async def test_setup_creates_read_only_sensors(hass: HomeAssistant) -> None:
    """A successful first refresh creates the three supported sensors."""
    entry = _config_entry("192.0.2.1")

    await _setup_entry(hass, entry)

    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    assert entry.state is ConfigEntryState.LOADED
    assert {entity.unique_id for entity in entries} == {
        "192.0.2.1:80_G0_current_temperature",
        "192.0.2.1:80_G0_target_temperature",
        "192.0.2.1:80_G0_last_seen",
    }
    assert all(
        (state := hass.states.get(entity.entity_id)) is not None
        and state.state != "unavailable"
        for entity in entries
    )


async def test_first_refresh_failure_retries_setup(hass: HomeAssistant) -> None:
    """A controller failure during initial refresh asks Home Assistant to retry."""
    entry = _config_entry("192.0.2.1")
    entry.add_to_hass(hass)

    with patch("custom_components.roth_touchline.RothTouchlineHub") as hub_class:
        hub_class.return_value.get_zone_data = AsyncMock(
            side_effect=RothTouchlineCommunicationError("offline")
        )
        assert not await hass.config_entries.async_setup(entry.entry_id)

    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_entities_become_unavailable_and_recover(hass: HomeAssistant) -> None:
    """Coordinator failures make sensors unavailable until communication recovers."""
    entry = _config_entry("192.0.2.1")
    hub = await _setup_entry(hass, entry)
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entity_registry = er.async_get(hass)
    entity = er.async_entries_for_config_entry(entity_registry, entry.entry_id)[0]

    hub.get_zone_data.side_effect = RothTouchlineCommunicationError("offline")
    await coordinator.async_refresh()
    state = hass.states.get(entity.entity_id)
    assert state is not None
    assert state.state == "unavailable"

    hub.get_zone_data.side_effect = None
    hub.get_zone_data.return_value = ZONE_DATA
    await coordinator.async_refresh()
    state = hass.states.get(entity.entity_id)
    assert state is not None
    assert state.state != "unavailable"


async def test_unload_removes_runtime_data(hass: HomeAssistant) -> None:
    """Unloading an entry removes its entities and runtime data."""
    entry = _config_entry("192.0.2.1")
    await _setup_entry(hass, entry)

    assert await hass.config_entries.async_unload(entry.entry_id)

    assert entry.state is ConfigEntryState.NOT_LOADED
    assert entry.entry_id not in hass.data[DOMAIN]


async def test_reload_recreates_runtime_data(hass: HomeAssistant) -> None:
    """Reloading an entry unloads and sets up the integration again."""
    entry = _config_entry("192.0.2.1")
    await _setup_entry(hass, entry)
    original_coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    with patch("custom_components.roth_touchline.RothTouchlineHub") as hub_class:
        hub_class.return_value.get_zone_data = AsyncMock(return_value=ZONE_DATA)
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert hass.data[DOMAIN][entry.entry_id]["coordinator"] is not original_coordinator


async def test_two_controllers_can_use_the_same_zone_id(hass: HomeAssistant) -> None:
    """Controller identity keeps equal zone identifiers distinct."""
    first = _config_entry("192.0.2.1")
    second = _config_entry("192.0.2.2")
    await _setup_entry(hass, first)
    await _setup_entry(hass, second)

    entity_registry = er.async_get(hass)
    first_ids = {
        entity.unique_id
        for entity in er.async_entries_for_config_entry(entity_registry, first.entry_id)
    }
    second_ids = {
        entity.unique_id
        for entity in er.async_entries_for_config_entry(
            entity_registry, second.entry_id
        )
    }

    assert first_ids
    assert second_ids
    assert first_ids.isdisjoint(second_ids)


async def test_version_one_identifiers_are_migrated(hass: HomeAssistant) -> None:
    """Existing entity history is retained when controller identity is introduced."""
    entry = _config_entry("192.0.2.1", version=1)
    entry.add_to_hass(hass)
    entity_registry = er.async_get(hass)
    legacy_entity = entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        f"{DOMAIN}_G0_current_temperature",
        config_entry=entry,
        suggested_object_id="roth_touchline_living_room_current_temperature",
    )
    device_registry = dr.async_get(hass)
    legacy_device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "G0")},
    )

    assert await async_migrate_entry(hass, entry)

    assert entry.version == 2
    assert entry.unique_id == "192.0.2.1:80"
    assert entity_registry.async_get(legacy_entity.entity_id).unique_id == (
        "192.0.2.1:80_G0_current_temperature"
    )
    assert device_registry.async_get(legacy_device.id).identifiers == {
        (DOMAIN, "192.0.2.1:80_G0")
    }
