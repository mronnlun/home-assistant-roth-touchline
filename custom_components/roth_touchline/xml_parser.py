"""XML parsing utilities for Roth Touchline responses."""
from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from typing import Any

_LOGGER = logging.getLogger(__name__)


class RothTouchlineXMLParser:
    """Parser for Roth Touchline XML responses."""

    @staticmethod
    def parse_values_response(response_text: str) -> dict[str, str]:
        """Parse the XML response from ILRReadValues.cgi."""
        values = {}
        
        try:
            # Remove any BOM or whitespace
            response_text = response_text.strip()
            
            # TODO: Implement actual XML parsing based on Roth Touchline response format
            # The actual response format from the Roth Touchline system needs to be analyzed
            # This is a placeholder implementation
            
            _LOGGER.debug("Parsing XML response: %s", response_text[:500])
            
            # Try to parse as XML
            root = ET.fromstring(response_text)
            
            # Extract values based on the expected response structure
            # This will need to be updated based on actual response format
            for item in root.findall(".//item") or root.findall(".//i"):
                name_elem = item.find("name") or item.find("n")
                value_elem = item.find("value") or item.find("v")
                
                if name_elem is not None and value_elem is not None:
                    name = name_elem.text
                    value = value_elem.text
                    if name and value:
                        values[name] = value
            
        except ET.ParseError as err:
            _LOGGER.error("Failed to parse XML response: %s", err)
            _LOGGER.debug("Raw response that failed to parse: %s", response_text)
        except Exception as err:
            _LOGGER.error("Unexpected error parsing XML response: %s", err)
        
        return values

    @staticmethod
    def extract_zone_data(values: dict[str, str], zone_id: str) -> dict[str, Any]:
        """Extract zone data from parsed values."""
        zone_num = zone_id.replace("G", "")
        
        zone_data = {
            "id": zone_id,
            "name": f"Zone {zone_id}",
            "current_temperature": None,
            "target_temperature": None,
        }
        
        try:
            # Extract current temperature (RaumTemp) - divide by 100 since values are in hundredths
            current_temp_key = f"G{zone_num}.RaumTemp"
            if current_temp_key in values:
                try:
                    raw_temp = float(values[current_temp_key])
                    zone_data["current_temperature"] = raw_temp / 100.0
                except (ValueError, TypeError):
                    _LOGGER.warning("Invalid current temperature value for %s: %s", 
                                   zone_id, values[current_temp_key])
            
            # Extract target temperature (SollTemp) - divide by 100 since values are in hundredths
            target_temp_key = f"G{zone_num}.SollTemp"
            if target_temp_key in values:
                try:
                    raw_temp = float(values[target_temp_key])
                    zone_data["target_temperature"] = raw_temp / 100.0
                except (ValueError, TypeError):
                    _LOGGER.warning("Invalid target temperature value for %s: %s", 
                                   zone_id, values[target_temp_key])
            
            # Extract room name
            name_key = f"G{zone_num}.name"
            if name_key in values and values[name_key]:
                zone_data["name"] = values[name_key]
            
            # Add timestamp with timezone information
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            zone_data["timestamp"] = now
            
            # Also add last_seen timestamp for sensor
            zone_data["last_seen"] = now
            
        except Exception as err:
            _LOGGER.error("Error extracting zone data for %s: %s", zone_id, err)
        
        return zone_data

    @staticmethod
    def get_available_zones(values: dict[str, str], max_zones: int = 7) -> list[dict[str, Any]]:
        """Get list of available zones from parsed values."""
        zones = []
        
        # Check for zones G0 through G(max_zones-1)
        for zone_num in range(max_zones):
            zone_id = f"G{zone_num}"
            
            # Check if this zone has data
            has_temp = f"G{zone_num}.RaumTemp" in values
            has_setpoint = f"G{zone_num}.SollTemp" in values
            has_name = f"G{zone_num}.name" in values
            
            if has_temp or has_setpoint or has_name:
                zone_name = values.get(f"G{zone_num}.name", f"Zone {zone_num}")
                zones.append({
                    "id": zone_id,
                    "name": zone_name,
                    "number": zone_num
                })
        
        return zones

    @staticmethod
    def create_request_xml(items: list[str]) -> str:
        """Create XML request body for the specified items."""
        root = ET.Element("body")
        item_list = ET.SubElement(root, "item_list")
        
        for item in items:
            i_element = ET.SubElement(item_list, "i")
            n_element = ET.SubElement(i_element, "n")
            n_element.text = item
        
        # Return XML string without XML declaration
        xml_str = ET.tostring(root, encoding="unicode")
        return xml_str

    @staticmethod
    def get_zone_request_items(max_zones: int = 7) -> list[str]:
        """Get the list of items to request for all zones."""
        items = []
        
        # Add items for each zone
        for zone_num in range(max_zones):
            items.extend([
                f"G{zone_num}.RaumTemp",
                f"G{zone_num}.SollTemp",
                f"G{zone_num}.name"
            ])
        
        # Add system status
        items.append("R0.SystemStatus")
        
        return items
