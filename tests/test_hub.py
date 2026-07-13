"""Tests for Roth Touchline HTTP communication."""

from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from custom_components.roth_touchline.hub import (
    RothTouchlineCommunicationError,
    RothTouchlineHub,
)


def _session_with_response(body: str) -> tuple[MagicMock, MagicMock]:
    """Create an HTTP session returning one mocked response."""
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.text = AsyncMock(return_value=body)

    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=response)
    context.__aexit__ = AsyncMock(return_value=None)

    session = MagicMock(spec=aiohttp.ClientSession)
    session.post.return_value = context
    return session, response


async def test_bulk_refresh_uses_one_request() -> None:
    """A refresh retrieves all zones in one controller request."""
    session, _ = _session_with_response(
        "<body>"
        "<i><n>G0.RaumTemp</n><v>2050</v></i>"
        "<i><n>G0.SollTemp</n><v>2100</v></i>"
        "<i><n>G0.name</n><v>Living room</v></i>"
        "<i><n>R0.SystemStatus</n><v>1</v></i>"
        "</body>"
    )
    hub = RothTouchlineHub(session, "192.0.2.1", 80, max_zones=10)

    zones = await hub.get_zone_data()

    assert zones["G0"]["current_temperature"] == 20.5
    assert session.post.call_count == 1


async def test_http_failure_is_reported() -> None:
    """An HTTP failure cannot be mistaken for a valid empty controller."""
    session, response = _session_with_response("")
    response.raise_for_status.side_effect = aiohttp.ClientError("HTTP 500")
    hub = RothTouchlineHub(session, "192.0.2.1", 80)

    with pytest.raises(RothTouchlineCommunicationError):
        await hub.test_connection()


async def test_malformed_xml_is_reported() -> None:
    """Malformed XML is reported as a communication failure."""
    session, _ = _session_with_response("not XML")
    hub = RothTouchlineHub(session, "192.0.2.1", 80)

    with pytest.raises(RothTouchlineCommunicationError):
        await hub.test_connection()
