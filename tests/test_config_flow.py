"""Test the Roth Touchline config flow."""

from unittest.mock import AsyncMock, patch, sentinel

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
import pytest

from custom_components.roth_touchline.config_flow import (
    CannotConnect,
    InvalidAuth,
    validate_input,
)
from custom_components.roth_touchline.const import (
    CONF_MAX_ZONES,
    CONF_UPDATE_INTERVAL,
    DEFAULT_MAX_ZONES,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


async def test_form(hass: HomeAssistant) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with (
        patch(
            "custom_components.roth_touchline.config_flow.validate_input",
            return_value={"title": "Test Roth Touchline"},
        ),
        patch(
            "custom_components.roth_touchline.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 80,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "Test Roth Touchline"
    assert result2["data"] == {
        CONF_HOST: "192.168.1.100",
        CONF_PORT: 80,
        CONF_MAX_ZONES: DEFAULT_MAX_ZONES,
        CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL,
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_cannot_connect(hass: HomeAssistant) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.roth_touchline.config_flow.validate_input",
        side_effect=CannotConnect,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 80,
            },
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_invalid_auth(hass: HomeAssistant) -> None:
    """Test we handle invalid auth error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.roth_touchline.config_flow.validate_input",
        side_effect=InvalidAuth,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 80,
            },
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_unknown_error(hass: HomeAssistant) -> None:
    """Test we handle unknown error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.roth_touchline.config_flow.validate_input",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 80,
            },
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "unknown"}


async def test_validate_input_uses_shared_session(hass: HomeAssistant) -> None:
    """Config validation reuses Home Assistant's managed HTTP session."""
    data = {
        CONF_HOST: "192.168.1.100",
        CONF_PORT: 80,
        CONF_MAX_ZONES: DEFAULT_MAX_ZONES,
        CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL,
    }

    with (
        patch(
            "custom_components.roth_touchline.config_flow.async_get_clientsession",
            return_value=sentinel.session,
        ),
        patch(
            "custom_components.roth_touchline.config_flow.RothTouchlineHub"
        ) as hub_class,
    ):
        hub_class.return_value.test_connection = AsyncMock(return_value=True)

        await validate_input(hass, data)

    hub_class.assert_called_once_with(
        sentinel.session,
        "192.168.1.100",
        80,
        DEFAULT_MAX_ZONES,
    )


async def test_form_validates_real_http_response(
    hass: HomeAssistant, aioclient_mock
) -> None:
    """The config flow validates a Roth Touchline response over HTTP."""
    aioclient_mock.post(
        "http://192.168.1.100:80/cgi-bin/ILRReadValues.cgi",
        text=(
            "<body><i><n>G0.RaumTemp</n><v>2050</v></i>"
            "<i><n>R0.SystemStatus</n><v>1</v></i></body>"
        ),
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("custom_components.roth_touchline.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 80,
                CONF_MAX_ZONES: DEFAULT_MAX_ZONES,
                CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL,
            },
        )

    assert result["type"] == "create_entry"
    assert aioclient_mock.call_count == 1
