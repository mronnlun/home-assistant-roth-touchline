"""Hub for Roth Touchline integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DEFAULT_TIMEOUT
from .xml_parser import RothTouchlineXMLParser

_LOGGER = logging.getLogger(__name__)


class RothTouchlineHub:
    """Hub for communicating with Roth Touchline system."""

    def __init__(self, hass: HomeAssistant, host: str, port: int, max_zones: int = 7) -> None:
        """Initialize the hub."""
        self._hass = hass
        self._host = host
        self._port = port
        self._max_zones = max_zones
        self._session = aiohttp.ClientSession()
        self._base_url = f"http://{host}:{port}"

    async def test_connection(self) -> bool:
        """Test connectivity to the Roth Touchline system."""
        try:
            # Create a simple test request with G0 data
            xml_body = RothTouchlineXMLParser.create_request_xml([
                "G0.RaumTemp",
                "G0.SollTemp", 
                "G0.name"
            ])
            
            async with async_timeout.timeout(DEFAULT_TIMEOUT):
                async with self._session.post(
                    f"{self._base_url}/cgi-bin/ILRReadValues.cgi",
                    data=xml_body,
                    headers=self._get_headers()
                ) as response:
                    if response.status == 200:
                        data = await response.text()
                        _LOGGER.debug("Connection test successful: %s", data[:200])
                        return True
                    else:
                        _LOGGER.error("Connection test failed with status: %s", response.status)
                        return False
        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout connecting to Roth Touchline: %s", err)
            raise HomeAssistantError("Timeout connecting to device") from err
        except aiohttp.ClientError as err:
            _LOGGER.error("Error connecting to Roth Touchline: %s", err)
            raise HomeAssistantError("Cannot connect to device") from err

    def _get_headers(self) -> dict[str, str]:
        """Get the required headers for Roth Touchline requests."""
        return {
            "Accept-Language": "*",
            "Content-Type": "text/xml",
            "User-Agent": "SpiderControl/1.0 (iniNet-Solutions GmbH)",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Accept": "text/html, image/gif, image/jpeg, *; q = .2, */*; q=.2",
        }

    async def get_zones(self) -> list[dict[str, Any]]:
        """Get all zones from the Roth Touchline system."""
        try:
            # Request data for configured number of zones plus system status
            request_items = RothTouchlineXMLParser.get_zone_request_items(self._max_zones)
            xml_body = RothTouchlineXMLParser.create_request_xml(request_items)
            
            async with async_timeout.timeout(DEFAULT_TIMEOUT):
                async with self._session.post(
                    f"{self._base_url}/cgi-bin/ILRReadValues.cgi",
                    data=xml_body,
                    headers=self._get_headers()
                ) as response:
                    if response.status == 200:
                        response_text = await response.text()
                        values = RothTouchlineXMLParser.parse_values_response(response_text)
                        zones = RothTouchlineXMLParser.get_available_zones(values, self._max_zones)
                        return zones
                    else:
                        _LOGGER.error("Failed to get zones, status: %s", response.status)
                        return []
        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout getting zones: %s", err)
            raise HomeAssistantError("Timeout getting zones") from err
        except aiohttp.ClientError as err:
            _LOGGER.error("Error getting zones: %s", err)
            raise HomeAssistantError("Cannot get zones") from err

    async def get_zone_data(self, zone_id: str) -> dict[str, Any] | None:
        """Get data for a specific zone."""
        try:
            # Extract zone number from zone_id (e.g., "G0" -> 0)
            zone_num = zone_id.replace("G", "")
            
            # Request current temperature, setpoint, and name for this zone
            request_items = [
                f"G{zone_num}.RaumTemp",
                f"G{zone_num}.SollTemp",
                f"G{zone_num}.name"
            ]
            
            xml_body = RothTouchlineXMLParser.create_request_xml(request_items)
            
            async with async_timeout.timeout(DEFAULT_TIMEOUT):
                async with self._session.post(
                    f"{self._base_url}/cgi-bin/ILRReadValues.cgi",
                    data=xml_body,
                    headers=self._get_headers()
                ) as response:
                    if response.status == 200:
                        response_text = await response.text()
                        values = RothTouchlineXMLParser.parse_values_response(response_text)
                        zone_data = RothTouchlineXMLParser.extract_zone_data(values, zone_id)
                        return zone_data
                    else:
                        _LOGGER.error("Failed to get zone %s data, status: %s", zone_id, response.status)
                        return None
        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout getting zone %s data: %s", zone_id, err)
            return None
        except aiohttp.ClientError as err:
            _LOGGER.error("Error getting zone %s data: %s", zone_id, err)
            return None

    async def get_temperature_history(self, zone_id: str, hours: int = 24) -> list[dict[str, Any]]:
        """Get temperature history for a zone."""
        # Note: The Roth Touchline system may not support historical data via XML API
        # This method may need to be implemented differently or removed
        _LOGGER.warning("Temperature history not supported by Roth Touchline XML API")
        return []

    async def get_daily_temperature_stats(self, zone_id: str) -> dict[str, Any] | None:
        """Get daily temperature statistics for a zone."""
        # Note: The Roth Touchline system may not support daily stats via XML API
        # This method may need to be implemented differently or removed
        _LOGGER.warning("Daily temperature stats not supported by Roth Touchline XML API")
        return None

    async def set_temperature(self, zone_id: str, temperature: float) -> bool:
        """Set target temperature for a zone."""
        try:
            # Extract zone number from zone_id (e.g., "G0" -> 0)
            zone_num = zone_id.replace("G", "")
            
            # Create XML request to set temperature
            # TODO: Implement actual temperature setting XML format for Roth Touchline
            # This will likely require a different endpoint or XML format
            
            _LOGGER.warning("Temperature setting via XML API not yet implemented for zone %s", zone_id)
            return False
            
        except Exception as err:
            _LOGGER.error("Error setting temperature for zone %s: %s", zone_id, err)
            return False

    async def set_hvac_mode(self, zone_id: str, mode: int) -> bool:
        """Set HVAC mode for a zone."""
        try:
            # Extract zone number from zone_id (e.g., "G0" -> 0)
            zone_num = zone_id.replace("G", "")
            
            # Create XML request to set HVAC mode
            # TODO: Implement actual HVAC mode setting XML format for Roth Touchline
            # This will likely require a different endpoint or XML format
            
            _LOGGER.warning("HVAC mode setting via XML API not yet implemented for zone %s", zone_id)
            return False
            
        except Exception as err:
            _LOGGER.error("Error setting HVAC mode for zone %s: %s", zone_id, err)
            return False

    async def close(self) -> None:
        """Close the session."""
        if self._session:
            await self._session.close()
