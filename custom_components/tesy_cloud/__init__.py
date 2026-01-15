"""The tesy integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TesyCloudApi
from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD, CONF_USER_ID, DEFAULT_SCAN_INTERVAL
from .coordinator import TesyCloudCoordinator
from .history import TesyHistoryManager

PLATFORMS: list[str] = ["climate", "sensor", "binary_sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    user_id = entry.data[CONF_USER_ID]

    api = TesyCloudApi(session, username, password, user_id)

    history = TesyHistoryManager(hass, entry.entry_id, keep_days=30)
    await history.async_load()

    update_interval = timedelta(seconds=DEFAULT_SCAN_INTERVAL)
    coordinator = TesyCloudCoordinator(hass, api, update_interval, history=history)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
        "history": history,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok
