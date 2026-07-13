"""Hub for the Roth Touchline integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
from homeassistant.exceptions import HomeAssistantError

from .const import DEFAULT_MAX_ZONES, DEFAULT_TIMEOUT
from .xml_parser import RothTouchlineParseError, RothTouchlineXMLParser

_LOGGER = logging.getLogger(__name__)


class RothTouchlineCommunicationError(HomeAssistantError):
    """Raised when communication with a Roth Touchline controller fails."""


class RothTouchlineHub:
    """Communicate with a Roth Touchline controller."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        max_zones: int = DEFAULT_MAX_ZONES,
    ) -> None:
        """Initialize the hub using Home Assistant's shared HTTP session."""
        self._session = session
        self._max_zones = max_zones
        self._url = f"http://{host}:{port}/cgi-bin/ILRReadValues.cgi"

    async def test_connection(self) -> bool:
        """Test connectivity and validate that the response uses the expected API."""
        values = await self._read_values(
            ["G0.RaumTemp", "G0.SollTemp", "G0.name", "R0.SystemStatus"]
        )
        if not any(key.startswith(("G0.", "R0.")) for key in values):
            raise RothTouchlineCommunicationError(
                "Device response did not contain expected Roth Touchline values"
            )
        return True

    async def get_zone_data(self) -> dict[str, dict[str, Any]]:
        """Get all available zone data in one request."""
        values = await self._read_values(
            RothTouchlineXMLParser.get_zone_request_items(self._max_zones)
        )
        return RothTouchlineXMLParser.extract_all_zone_data(values, self._max_zones)

    async def _read_values(self, items: list[str]) -> dict[str, str]:
        """Read and parse a set of values from the controller."""
        xml_body = RothTouchlineXMLParser.create_request_xml(items)

        try:
            async with asyncio.timeout(DEFAULT_TIMEOUT):
                async with self._session.post(
                    self._url,
                    data=xml_body,
                    headers=self._get_headers(),
                ) as response:
                    response.raise_for_status()
                    response_text = await response.text()
        except TimeoutError as err:
            raise RothTouchlineCommunicationError(
                "Timed out communicating with the controller"
            ) from err
        except aiohttp.ClientError as err:
            raise RothTouchlineCommunicationError(
                "Unable to communicate with the controller"
            ) from err

        try:
            return RothTouchlineXMLParser.parse_values_response(response_text)
        except RothTouchlineParseError as err:
            raise RothTouchlineCommunicationError(str(err)) from err

    @staticmethod
    def _get_headers() -> dict[str, str]:
        """Get the headers required by the Roth Touchline controller."""
        return {
            "Accept-Language": "*",
            "Content-Type": "text/xml",
            "User-Agent": "SpiderControl/1.0 (iniNet-Solutions GmbH)",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Accept": "text/html, image/gif, image/jpeg, *; q=.2, */*; q=.2",
        }
