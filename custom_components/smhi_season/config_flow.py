"""Config flow for SMHI Season integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import CONF_TEMP_SENSOR, DOMAIN


class SMHISeasonConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SMHI Season."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(
                title=f"SMHI Season ({user_input[CONF_TEMP_SENSOR]})",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_TEMP_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="temperature"
                    )
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors={})
