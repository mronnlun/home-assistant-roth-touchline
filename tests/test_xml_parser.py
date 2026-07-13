"""Tests for Roth Touchline XML parsing."""

import pytest

from custom_components.roth_touchline.xml_parser import (
    RothTouchlineParseError,
    RothTouchlineXMLParser,
)


@pytest.mark.parametrize(
    ("xml", "expected"),
    [
        (
            "<body><i><n>G0.RaumTemp</n><v>2150</v></i></body>",
            {"G0.RaumTemp": "2150"},
        ),
        (
            "<body><item><name>G0.RaumTemp</name><value>2150</value></item></body>",
            {"G0.RaumTemp": "2150"},
        ),
    ],
)
def test_parse_supported_xml_formats(xml: str, expected: dict[str, str]) -> None:
    """Both known tag formats are parsed."""
    assert RothTouchlineXMLParser.parse_values_response(xml) == expected


@pytest.mark.parametrize("xml", ["", "not XML", "<html><body>Error</body></html>"])
def test_reject_invalid_responses(xml: str) -> None:
    """Invalid or unrelated responses cannot become empty successful updates."""
    with pytest.raises(RothTouchlineParseError):
        RothTouchlineXMLParser.parse_values_response(xml)


def test_extract_all_zones_from_bulk_response() -> None:
    """All zones are extracted from one parsed response."""
    values = {
        "G0.RaumTemp": "2050",
        "G0.SollTemp": "2100",
        "G0.name": "Living room",
        "G1.RaumTemp": "1875",
        "G1.SollTemp": "1900",
        "G1.name": "Bedroom",
    }

    zones = RothTouchlineXMLParser.extract_all_zone_data(values, max_zones=2)

    assert zones["G0"]["current_temperature"] == 20.5
    assert zones["G0"]["target_temperature"] == 21.0
    assert zones["G0"]["name"] == "Living room"
    assert zones["G1"]["current_temperature"] == 18.75
