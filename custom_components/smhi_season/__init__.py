"""The SMHI Season integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SMHI Season from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if not hass.services.has_service(DOMAIN, "recompute"):

        async def _recompute(call) -> None:
            """Recompute season state for every registered sensor entity."""
            for entity in list(hass.data[DOMAIN].get("entities", {}).values()):
                try:
                    await entity.async_recompute()
                except Exception:  # noqa: BLE001
                    _LOGGER.exception("Failed to recompute %s", entity.entity_id)

        hass.services.async_register(DOMAIN, "recompute", _recompute)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
