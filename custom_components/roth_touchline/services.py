"""Service handlers for Roth Touchline integration."""
from __future__ import annotations

import csv
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_GET_TEMPERATURE_HISTORY = "get_temperature_history"
SERVICE_EXPORT_TEMPERATURE_DATA = "export_temperature_data"

GET_TEMPERATURE_HISTORY_SCHEMA = vol.Schema(
    {
        vol.Required("zone_id"): cv.string,
        vol.Optional("hours", default=24): cv.positive_int,
    }
)

EXPORT_TEMPERATURE_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional("days", default=7): cv.positive_int,
        vol.Optional("file_path"): cv.string,
    }
)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for the Roth Touchline integration."""

    async def handle_get_temperature_history(call: ServiceCall) -> None:
        """Handle get temperature history service call."""
        zone_id = call.data["zone_id"]
        hours = call.data["hours"]
        
        # Find the integration entry for this zone
        entry_data = None
        for entry_id, data in hass.data.get(DOMAIN, {}).items():
            if "hub" in data:
                hub = data["hub"]
                history = await hub.get_temperature_history(zone_id, hours)
                
                # Fire an event with the temperature history
                hass.bus.async_fire(
                    f"{DOMAIN}_temperature_history",
                    {
                        "zone_id": zone_id,
                        "hours": hours,
                        "history": history,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                
                _LOGGER.info(
                    "Retrieved %d temperature readings for zone %s (%d hours)",
                    len(history),
                    zone_id,
                    hours
                )
                break

    async def handle_export_temperature_data(call: ServiceCall) -> None:
        """Handle export temperature data service call."""
        days = call.data["days"]
        file_path = call.data.get("file_path")
        
        if not file_path:
            # Generate default file path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"/config/roth_touchline_export_{timestamp}.csv"
        
        try:
            # Collect data from all zones
            all_data = []
            
            for entry_id, data in hass.data.get(DOMAIN, {}).items():
                if "hub" in data and "coordinator" in data:
                    coordinator = data["coordinator"]
                    hub = data["hub"]
                    
                    for zone_id in coordinator.data.keys():
                        # Get temperature history for each zone
                        hours = days * 24
                        history = await hub.get_temperature_history(zone_id, hours)
                        
                        for reading in history:
                            all_data.append({
                                "zone_id": zone_id,
                                "zone_name": coordinator.data[zone_id].get("name", zone_id),
                                "timestamp": reading.get("timestamp"),
                                "current_temperature": reading.get("current_temperature"),
                                "target_temperature": reading.get("target_temperature"),
                                "humidity": reading.get("humidity"),
                                "hvac_mode": reading.get("hvac_mode"),
                                "heating": reading.get("heating", False),
                                "cooling": reading.get("cooling", False),
                            })
            
            # Write to CSV file
            if all_data:
                file_path_obj = Path(file_path)
                file_path_obj.parent.mkdir(parents=True, exist_ok=True)
                
                with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
                    fieldnames = [
                        "zone_id",
                        "zone_name", 
                        "timestamp",
                        "current_temperature",
                        "target_temperature",
                        "humidity",
                        "hvac_mode",
                        "heating",
                        "cooling",
                    ]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(all_data)
                
                # Fire an event with export results
                hass.bus.async_fire(
                    f"{DOMAIN}_data_exported",
                    {
                        "file_path": file_path,
                        "days": days,
                        "records_exported": len(all_data),
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                
                _LOGGER.info(
                    "Exported %d temperature records to %s",
                    len(all_data),
                    file_path
                )
            else:
                _LOGGER.warning("No temperature data found to export")
                
        except Exception as err:
            _LOGGER.error("Error exporting temperature data: %s", err)

    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_TEMPERATURE_HISTORY,
        handle_get_temperature_history,
        schema=GET_TEMPERATURE_HISTORY_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_TEMPERATURE_DATA,
        handle_export_temperature_data,
        schema=EXPORT_TEMPERATURE_DATA_SCHEMA,
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload services for the Roth Touchline integration."""
    hass.services.async_remove(DOMAIN, SERVICE_GET_TEMPERATURE_HISTORY)
    hass.services.async_remove(DOMAIN, SERVICE_EXPORT_TEMPERATURE_DATA)
