"""The tesy integration."""

from __future__ import annotations

from datetime import timedelta
import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TesyCloudApi
from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD, CONF_USER_ID, DEFAULT_SCAN_INTERVAL
from .coordinator import TesyCloudCoordinator
from .history import TesyHistoryManager

PLATFORMS: list[str] = ["climate", "sensor", "binary_sensor"]
SERVICE_RESET_HISTORY = "reset_history"
LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    user_id = entry.data[CONF_USER_ID]

    api = TesyCloudApi(session, username, password, user_id, app_id=entry.entry_id.replace("-", "")[:16])

    history = TesyHistoryManager(hass, entry.entry_id, keep_days=30)
    try:
        await history.async_load()
    except Exception as err:
        LOGGER.warning("Failed to load TESY history store; starting with empty history: %s", err)

    update_interval = timedelta(seconds=DEFAULT_SCAN_INTERVAL)
    coordinator = TesyCloudCoordinator(hass, api, update_interval, history=history)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
        "history": history,
    }

    if not hass.services.has_service(DOMAIN, SERVICE_RESET_HISTORY):
        async def _async_handle_reset_history(call: ServiceCall) -> None:
            mac = call.data.get("mac")
            for item in hass.data.get(DOMAIN, {}).values():
                hist = item.get("history")
                coord = item.get("coordinator")
                if hist is None:
                    continue
                await hist.async_reset(mac)
                if coord is not None:
                    await coord.async_request_refresh()

        hass.services.async_register(
            DOMAIN,
            SERVICE_RESET_HISTORY,
            _async_handle_reset_history,
            schema=vol.Schema({vol.Optional("mac"): cv.string}),
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        if not hass.data.get(DOMAIN) and hass.services.has_service(DOMAIN, SERVICE_RESET_HISTORY):
            hass.services.async_remove(DOMAIN, SERVICE_RESET_HISTORY)
    return unload_ok
