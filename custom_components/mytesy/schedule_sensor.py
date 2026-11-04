"""Schedule editor link and live program data for each TESY device."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

class TesyScheduleEditor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Schedule editor"
    _attr_icon = "mdi:calendar-edit"
    _attr_native_value = "Open"
    _unrecorded_attributes = frozenset({"mytesy_schedule_editor", "editor_url", "program_intervals"})

    def __init__(self, coordinator, mac):
        super().__init__(coordinator)
        self._mac = mac
        self._attr_unique_id = f"{mac}_schedule_editor"
        self._attr_device_info = {"identifiers": {(DOMAIN, mac)}}

    @property
    def extra_state_attributes(self):
        state = ((self.coordinator.data or {}).get(self._mac) or {}).get("state") or {}
        raw = state.get("program")
        from .calendar import _program_items
        items = _program_items(raw)
        clean = [{k: v for k, v in item.items() if k in {"day", "from", "to", "temp", "program_number"}}
                 for item in items[:150]]
        from homeassistant.helpers import entity_registry as er
        program_switch = er.async_get(self.hass).async_get_entity_id("switch", DOMAIN, f"{self._mac}_setting_programStatus")
        return {"mytesy_schedule_editor": True,
                "editor_url": f"/mytesy-schedules?mac={self._mac}",
                "program_intervals": clean,
                "program_data_available": isinstance(raw, (list, dict)),
                "device_name": ((self.coordinator.data or {}).get(self._mac) or {}).get("name", "TESY"),
                "program_status_display": ("Enabled" if str(state.get("programStatus")).lower() in ("on", "true", "1", "enabled") else "Disabled" if str(state.get("programStatus")).lower() in ("off", "false", "0", "disabled") else "Status unavailable"),
                "program_status": state.get("programStatus"),
                "program_switch_entity_id": program_switch}
