"""Test the SMHI Season config flow."""

from unittest.mock import patch

from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.smhi_season.const import CONF_TEMP_SENSOR, DOMAIN


async def test_form(hass: HomeAssistant) -> None:
    """Test we get the form and create entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "custom_components.smhi_season.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_TEMP_SENSOR: "sensor.outdoor_temperature"},
        )
        await hass.async_block_till_done()

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == "SMHI Season (sensor.outdoor_temperature)"
    assert result2["data"] == {
        CONF_TEMP_SENSOR: "sensor.outdoor_temperature",
    }
    assert len(mock_setup_entry.mock_calls) == 1
