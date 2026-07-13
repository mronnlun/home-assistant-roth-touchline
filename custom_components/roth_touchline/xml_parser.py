"""XML parsing utilities for Roth Touchline responses."""

from __future__ import annotations

from datetime import UTC, datetime
import logging
from typing import Any
import xml.etree.ElementTree as ET

_LOGGER = logging.getLogger(__name__)


class RothTouchlineParseError(Exception):
    """Raised when a Roth Touchline response cannot be parsed."""


class RothTouchlineXMLParser:
    """Parser for Roth Touchline XML responses."""

    @staticmethod
    def parse_values_response(response_text: str) -> dict[str, str]:
        """Parse the XML response from ILRReadValues.cgi."""
        values: dict[str, str] = {}

        try:
            response_text = response_text.strip()
            if not response_text:
                raise RothTouchlineParseError("Device returned an empty response")

            _LOGGER.debug("Parsing XML response: %s", response_text[:500])
            root = ET.fromstring(response_text)

            items = root.findall(".//item")
            if not items:
                items = root.findall(".//i")

            for item in items:
                name_elem = item.find("name")
                if name_elem is None:
                    name_elem = item.find("n")

                value_elem = item.find("value")
                if value_elem is None:
                    value_elem = item.find("v")

                if name_elem is not None and value_elem is not None:
                    name = name_elem.text
                    value = value_elem.text
                    if name is not None and value is not None:
                        values[name] = value

        except ET.ParseError as err:
            raise RothTouchlineParseError("Device returned malformed XML") from err

        if not values:
            raise RothTouchlineParseError(
                "Device response did not contain Roth Touchline values"
            )

        return values

    @staticmethod
    def extract_zone_data(values: dict[str, str], zone_id: str) -> dict[str, Any]:
        """Extract zone data from parsed values."""
        zone_num = zone_id.removeprefix("G")

        zone_data: dict[str, Any] = {
            "id": zone_id,
            "name": f"Zone {zone_id}",
            "current_temperature": None,
            "target_temperature": None,
        }
        current_temp_key = f"G{zone_num}.RaumTemp"
        if current_temp_key in values:
            zone_data["current_temperature"] = (
                RothTouchlineXMLParser._parse_temperature(
                    values[current_temp_key], zone_id, "current"
                )
            )

        target_temp_key = f"G{zone_num}.SollTemp"
        if target_temp_key in values:
            zone_data["target_temperature"] = RothTouchlineXMLParser._parse_temperature(
                values[target_temp_key], zone_id, "target"
            )

        name = values.get(f"G{zone_num}.name")
        if name:
            zone_data["name"] = name

        now = datetime.now(UTC)
        zone_data["timestamp"] = now
        zone_data["last_seen"] = now

        return zone_data

    @staticmethod
    def _parse_temperature(value: str, zone_id: str, kind: str) -> float | None:
        """Convert a controller temperature value from hundredths of a degree."""
        try:
            return float(value) / 100.0
        except TypeError, ValueError:
            _LOGGER.warning("Invalid %s temperature for %s: %s", kind, zone_id, value)
            return None

    @staticmethod
    def extract_all_zone_data(
        values: dict[str, str], max_zones: int
    ) -> dict[str, dict[str, Any]]:
        """Extract all available zones from one bulk response."""
        return {
            zone["id"]: RothTouchlineXMLParser.extract_zone_data(values, zone["id"])
            for zone in RothTouchlineXMLParser.get_available_zones(values, max_zones)
        }

    @staticmethod
    def get_available_zones(
        values: dict[str, str], max_zones: int = 7
    ) -> list[dict[str, Any]]:
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
                zones.append({"id": zone_id, "name": zone_name, "number": zone_num})

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
            items.extend(
                [f"G{zone_num}.RaumTemp", f"G{zone_num}.SollTemp", f"G{zone_num}.name"]
            )

        # Add system status
        items.append("R0.SystemStatus")

        return items
