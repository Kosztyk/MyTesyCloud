"""The mytesy integration."""

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
from .statistics import TesyStatisticsCoordinator

PLATFORMS: list[str] = ["climate", "sensor", "binary_sensor", "switch", "number", "button", "calendar", "water_heater"]
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

    stats = TesyStatisticsCoordinator(hass, api, coordinator)
    # Statistics are optional and must not break setup or legacy energy entities.
    await stats.async_refresh()
    coordinator._tesy_statistics = stats

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "statistics": stats,
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

    if not hass.services.has_service(DOMAIN, "set_program_interval"):
        async def _set_program_interval(call: ServiceCall) -> None:
            mac = call.data["mac"]
            for record in hass.data.get(DOMAIN, {}).values():
                payload = (record["coordinator"].data or {}).get(mac)
                if payload is not None:
                    await record["api"].async_send_command(payload["device"], "setProgram", {
                        "day": call.data["day"], "from": call.data["from"],
                        "to": call.data["to"], "temp": call.data["temp"],
                        "program_number": call.data["program_number"],
                    })
                    await record["coordinator"].async_request_refresh()
                    return
            raise ValueError("Specified TESY MAC not found")
        hass.services.async_register(DOMAIN, "set_program_interval", _set_program_interval,
            schema=vol.Schema({vol.Required("mac"): cv.string,
                vol.Required("day"): vol.All(vol.Coerce(int), vol.Range(min=0, max=7)),
                vol.Required("from"): vol.Match(r"^([01]\d|2[0-3]):[0-5]\d$"),
                vol.Required("to"): vol.Match(r"^([01]\d|2[0-3]):[0-5]\d$"),
                vol.Required("temp"): vol.All(vol.Coerce(int), vol.Range(min=5, max=35)),
                vol.Required("program_number"): vol.All(vol.Coerce(int), vol.Range(min=1, max=255))}))

    if not hass.services.has_service(DOMAIN, "delete_program_interval"):
        async def _delete_program_interval(call: ServiceCall) -> None:
            for record in hass.data.get(DOMAIN, {}).values():
                payload = (record["coordinator"].data or {}).get(call.data["mac"])
                if payload is not None:
                    await record["api"].async_send_command(payload["device"], "deleteProgram", {
                        "program_number": call.data["program_number"]})
                    await record["coordinator"].async_request_refresh()
                    return
            raise ValueError("Specified TESY MAC not found")
        hass.services.async_register(DOMAIN, "delete_program_interval", _delete_program_interval,
            schema=vol.Schema({vol.Required("mac"): cv.string,
                vol.Required("program_number"): vol.All(vol.Coerce(int), vol.Range(min=1, max=255))}))

    # Group operations use TESY native group REST API, not local synthetic groups.
    async def _group_action(call: ServiceCall) -> None:
        action = call.data["operation"]
        endpoint = {"create": "create-group", "edit": "edit-group", "delete": "delete-group",
                    "add_device": "add-device-to-group"}[action]
        params = {k: v for k,v in call.data.items() if k not in {"operation", "entry_id"}}
        if action in {"edit", "delete"} and "id" not in params:
            raise ValueError("Group id required")
        if action == "add_device" and ("group_id" not in params or "mac" not in params):
            raise ValueError("Group id and device MAC required")
        if action == "create" and not str(params.get("name") or "").strip():
            raise ValueError("Group name required")
        record = hass.data[DOMAIN].get(call.data.get("entry_id") or entry.entry_id)
        if record is None: raise ValueError("TESY integration entry unavailable")
        await record["api"].async_group_request(endpoint, payload=params)
        await record["coordinator"].async_request_refresh()

    if not hass.services.has_service(DOMAIN, "manage_group"):
        hass.services.async_register(DOMAIN, "manage_group", _group_action, schema=vol.Schema({
            vol.Required("operation"): vol.In(["create", "edit", "delete", "add_device"]),
            vol.Optional("entry_id"): cv.string, vol.Optional("id"): vol.Coerce(int),
            vol.Optional("group_id"): vol.Coerce(int), vol.Optional("name"): cv.string,
            vol.Optional("mac"): cv.string, vol.Optional("devices"): [cv.string]}))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    try:
        from .schedule_frontend import async_setup_editor
        await async_setup_editor(hass)
    except Exception as exc:
        LOGGER.warning("TESY schedule editor UI unavailable: %s", exc)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        if not hass.data.get(DOMAIN) and hass.services.has_service(DOMAIN, SERVICE_RESET_HISTORY):
            hass.services.async_remove(DOMAIN, SERVICE_RESET_HISTORY)
    return unload_ok
