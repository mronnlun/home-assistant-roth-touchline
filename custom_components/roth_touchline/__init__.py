"""The Roth Touchline integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_MAX_ZONES,
    CONF_UPDATE_INTERVAL,
    DEFAULT_MAX_ZONES,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)
from .coordinator import RothTouchlineDataUpdateCoordinator
from .hub import RothTouchlineHub

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Roth Touchline from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, 80)
    max_zones = entry.data.get(CONF_MAX_ZONES, DEFAULT_MAX_ZONES)
    update_interval = entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)

    hub = RothTouchlineHub(async_get_clientsession(hass), host, port, max_zones)

    coordinator = RothTouchlineDataUpdateCoordinator(hass, hub, update_interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "hub": hub,
        "coordinator": coordinator,
        "controller_id": entry.unique_id or entry.entry_id,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def async_migrate_entry(  # pylint: disable=too-many-locals
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Migrate legacy identifiers to include the controller identity."""
    if entry.version != 1:
        return True

    host = entry.data[CONF_HOST].strip().lower()
    port = entry.data.get(CONF_PORT, 80)
    controller_id = f"{host}:{port}"

    entity_registry = er.async_get(hass)
    legacy_prefix = f"{DOMAIN}_"
    for entity in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
        if entity.platform != DOMAIN or not entity.unique_id.startswith(legacy_prefix):
            continue

        zone_and_type = entity.unique_id.removeprefix(legacy_prefix)
        zone_id, separator, sensor_type = zone_and_type.partition("_")
        if separator and zone_id.startswith("G"):
            entity_registry.async_update_entity(
                entity.entity_id,
                new_unique_id=f"{controller_id}_{zone_id}_{sensor_type}",
            )

    device_registry = dr.async_get(hass)
    for device in dr.async_entries_for_config_entry(device_registry, entry.entry_id):
        legacy_identifiers = {
            identifier
            for identifier in device.identifiers
            if identifier[0] == DOMAIN and identifier[1].startswith("G")
        }
        if not legacy_identifiers:
            continue

        new_identifiers = set(device.identifiers) - legacy_identifiers
        new_identifiers.update(
            (DOMAIN, f"{controller_id}_{zone_id}") for _, zone_id in legacy_identifiers
        )
        device_registry.async_update_device(device.id, new_identifiers=new_identifiers)

    hass.config_entries.async_update_entry(entry, unique_id=controller_id, version=2)
    return True
