"""App-discovered writable TESY convector settings."""
from __future__ import annotations
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.exceptions import HomeAssistantError
from .const import DOMAIN
from .device_families import supports_water_heater
from .schedule_frontend import async_sidebar_state, async_set_sidebar_visible

FLAGS = {
    "adaptiveStart": ("Adaptive Start", "setAdaptiveStart"),
    "antiFrost": ("Anti-Frost", "setAntiFrost"),
    "openedWindow": ("Open Window Detection", "setOpenedWindow"),
    "lockedDevice": ("Child Lock", "setLockDevice"),
    "uv": ("UV", "setUV"),
    "programStatus": ("Weekly Program", "setProgramStatus"),
}

def _on(value):
    if isinstance(value, bool): return value
    if isinstance(value, str): return value.lower() in ("on", "enabled", "true", "1")
    return value == 1

async def async_setup_entry(hass, entry, async_add_entities):
    c = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities=[]
    await async_sidebar_state(hass)
    for mac, payload in (c.data or {}).items():
        if supports_water_heater(payload.get("device") or {}): continue
        entities.append(TesySidebarVisibilitySwitch(c, mac))
        state = payload.get("state") or {}
        for field in FLAGS:
            if field == "programStatus" or (state.get(field) is not None and isinstance(state[field], (str, bool, int))):
                entities.append(TesySettingSwitch(c, mac, field))
    async_add_entities(entities)

class TesySettingSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, mac, field):
        super().__init__(coordinator)
        self.mac, self.field = mac, field
        self._attr_unique_id = f"{mac}_setting_{field}"
        self._attr_name = f"{(coordinator.data or {}).get(mac, {}).get('name', 'TESY')} {FLAGS[field][0]}"
        self._attr_device_info = {"identifiers": {(DOMAIN, mac)}}
    @property
    def available(self):
        state = (self.coordinator.data or {}).get(self.mac, {}).get("state") or {}
        return super().available and (self.field != "programStatus" or state.get("programStatus") is not None)

    @property
    def is_on(self):
        state = (self.coordinator.data or {}).get(self.mac, {}).get("state") or {}
        return None if state.get(self.field) is None else _on(state.get(self.field))
    async def _write(self, enabled):
        payload = (self.coordinator.data or {}).get(self.mac, {})
        device = payload.get("device") or {}
        try:
            await self.coordinator.api.async_send_command(device, FLAGS[self.field][1], {"status": "on" if enabled else "off"})
            await self.coordinator.async_request_refresh()
        except Exception as exc:
            raise HomeAssistantError(f"TESY {FLAGS[self.field][0]} command failed") from exc
    async def async_turn_on(self): await self._write(True)
    async def async_turn_off(self): await self._write(False)


class TesySidebarVisibilitySwitch(CoordinatorEntity, SwitchEntity):
    """Show/hide the TESY schedules navigation item, not device schedules."""
    _attr_icon = "mdi:menu-open"
    _attr_should_poll = False

    def __init__(self, coordinator, mac):
        super().__init__(coordinator)
        self._mac = mac
        self._attr_unique_id = f"{mac}_sidebar_schedule_visibility"
        self._attr_name = f"{(coordinator.data or {}).get(mac, {}).get('name', 'TESY')} Show TESY schedules in sidebar"
        self._attr_device_info = {"identifiers": {(DOMAIN, mac)}}

    @property
    def is_on(self):
        return self.hass.data.get(DOMAIN, {}).get("_editor", {}).get("visible", True)

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.hass.data[DOMAIN]["_editor"].setdefault("switch_entities", set()).add(self)

    async def async_will_remove_from_hass(self):
        self.hass.data.get(DOMAIN, {}).get("_editor", {}).get("switch_entities", set()).discard(self)
        await super().async_will_remove_from_hass()

    async def async_turn_on(self):
        await async_set_sidebar_visible(self.hass, True)

    async def async_turn_off(self):
        await async_set_sidebar_visible(self.hass, False)
