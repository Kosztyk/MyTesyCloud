"""The mytesy integration."""

from __future__ import annotations

from datetime import timedelta
import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
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


def _entry_records(hass: HomeAssistant) -> dict[str, dict]:
    """Return only currently loaded MyTESY accounts, excluding UI state."""
    state = hass.data.get(DOMAIN, {})
    records = {}
    for entry in hass.config_entries.async_entries(DOMAIN):
        record = state.get(entry.entry_id)
        if isinstance(record, dict) and "coordinator" in record and "api" in record:
            records[entry.entry_id] = record
    return records


def _resolve_record(hass: HomeAssistant, entry_id: str | None = None) -> dict:
    """Resolve a live account per invocation; never capture the first account."""
    records = _entry_records(hass)
    if entry_id:
        record = records.get(entry_id)
        if record is None:
            raise HomeAssistantError("The specified MyTESY account is not loaded")
        return record
    if not records:
        raise HomeAssistantError("No MyTESY account is loaded")
    if len(records) != 1:
        raise HomeAssistantError("Select entry_id when multiple MyTESY accounts are loaded")
    return next(iter(records.values()))


def _resolve_device(hass: HomeAssistant, mac: str, entry_id: str | None = None):
    """Resolve a heater in the correct account without indexing `_editor`."""
    records = _entry_records(hass)
    if entry_id:
        record = _resolve_record(hass, entry_id)
        payload = (record["coordinator"].data or {}).get(mac)
        if payload is None:
            raise HomeAssistantError("Device MAC not found in the specified MyTESY account")
        return record, payload
    matches = [
        (record, payload)
        for record in records.values()
        if (payload := (record["coordinator"].data or {}).get(mac)) is not None
    ]
    if not matches:
        raise HomeAssistantError("MyTESY device MAC not found in any loaded account")
    if len(matches) > 1:
        raise HomeAssistantError("Device MAC belongs to multiple accounts; specify entry_id")
    return matches[0]


def _register_services(hass: HomeAssistant) -> None:
    """Global services resolve loaded entries afresh for every service call."""
    if not hass.services.has_service(DOMAIN, SERVICE_RESET_HISTORY):
        async def _reset_history(call: ServiceCall) -> None:
            records = _entry_records(hass)
            selected = call.data.get("entry_id")
            if selected:
                records = {selected: _resolve_record(hass, selected)}
            if not records:
                raise HomeAssistantError("No MyTESY account is loaded")
            for record in records.values():
                history = record.get("history")
                if history is not None:
                    await history.async_reset(call.data.get("mac"))
                await record["coordinator"].async_request_refresh()

        hass.services.async_register(
            DOMAIN, SERVICE_RESET_HISTORY, _reset_history,
            schema=vol.Schema({vol.Optional("mac"): cv.string,
                               vol.Optional("entry_id"): cv.string}),
        )

    if not hass.services.has_service(DOMAIN, "set_program_interval"):
        async def _set_program_interval(call: ServiceCall) -> None:
            record, payload = _resolve_device(hass, call.data["mac"], call.data.get("entry_id"))
            await record["api"].async_send_command(payload["device"], "setProgram", {
                "day": call.data["day"], "from": call.data["from"],
                "to": call.data["to"], "temp": call.data["temp"],
                "program_number": call.data["program_number"],
            })
            await record["coordinator"].async_request_refresh()

        hass.services.async_register(
            DOMAIN, "set_program_interval", _set_program_interval,
            schema=vol.Schema({
                vol.Required("mac"): cv.string,
                vol.Optional("entry_id"): cv.string,
                vol.Required("day"): vol.All(vol.Coerce(int), vol.Range(min=0, max=7)),
                vol.Required("from"): vol.Match(r"^([01]\d|2[0-3]):[0-5]\d$"),
                vol.Required("to"): vol.Match(r"^([01]\d|2[0-3]):[0-5]\d$"),
                vol.Required("temp"): vol.All(vol.Coerce(int), vol.Range(min=5, max=35)),
                vol.Required("program_number"): vol.All(vol.Coerce(int), vol.Range(min=1, max=255)),
            }),
        )

    if not hass.services.has_service(DOMAIN, "delete_program_interval"):
        async def _delete_program_interval(call: ServiceCall) -> None:
            record, payload = _resolve_device(hass, call.data["mac"], call.data.get("entry_id"))
            await record["api"].async_send_command(payload["device"], "deleteProgram", {
                "program_number": call.data["program_number"],
            })
            await record["coordinator"].async_request_refresh()

        hass.services.async_register(
            DOMAIN, "delete_program_interval", _delete_program_interval,
            schema=vol.Schema({
                vol.Required("mac"): cv.string,
                vol.Optional("entry_id"): cv.string,
                vol.Required("program_number"): vol.All(vol.Coerce(int), vol.Range(min=1, max=255)),
            }),
        )

    if not hass.services.has_service(DOMAIN, "manage_group"):
        async def _group_action(call: ServiceCall) -> None:
            action = call.data["operation"]
            endpoint = {"create": "create-group", "edit": "edit-group",
                        "delete": "delete-group", "add_device": "add-device-to-group"}[action]
            params = {k: v for k, v in call.data.items() if k not in {"operation", "entry_id"}}
            if action in {"edit", "delete"} and "id" not in params:
                raise HomeAssistantError("Group id is required")
            if action == "add_device" and ("group_id" not in params or "mac" not in params):
                raise HomeAssistantError("Group id and device MAC are required")
            if action == "create" and not str(params.get("name") or "").strip():
                raise HomeAssistantError("Group name is required")
            record = _resolve_record(hass, call.data.get("entry_id"))
            await record["api"].async_group_request(endpoint, payload=params)
            await record["coordinator"].async_request_refresh()

        hass.services.async_register(
            DOMAIN, "manage_group", _group_action,
            schema=vol.Schema({
                vol.Required("operation"): vol.In(["create", "edit", "delete", "add_device"]),
                vol.Optional("entry_id"): cv.string,
                vol.Optional("id"): vol.Coerce(int),
                vol.Optional("group_id"): vol.Coerce(int),
                vol.Optional("name"): cv.string,
                vol.Optional("mac"): cv.string,
                vol.Optional("devices"): [cv.string],
            }),
        )


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register integration-wide services once, independent of accounts."""
    hass.data.setdefault(DOMAIN, {})
    _register_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Restore global services if HA reloads a fully unloaded integration.
    _register_services(hass)
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

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    try:
        from .schedule_frontend import async_setup_editor
        await async_setup_editor(hass)
    except Exception as exc:
        LOGGER.warning("TESY schedule editor UI unavailable: %s", exc)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload this account; on the last account clean up services and editor."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unloaded:
        return False

    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if not _entry_records(hass):
        from .schedule_frontend import async_unload_editor
        try:
            await async_unload_editor(hass)
        finally:
            for service in (SERVICE_RESET_HISTORY, "set_program_interval",
                            "delete_program_interval", "manage_group"):
                if hass.services.has_service(DOMAIN, service):
                    hass.services.async_remove(DOMAIN, service)
            # Retain static URL registration across entry reloads.
    return True
