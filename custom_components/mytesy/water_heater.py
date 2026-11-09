"""Read-only TESY B15/E32 boilers and HPWH4_11 heat pump water heaters.

Write support requires physical validation for each appliance family.
"""
from __future__ import annotations

from homeassistant.components.water_heater import WaterHeaterEntity
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .device_families import device_family

HP_MODES = ("hp", "eh", "au", "sm")
B15_MODES = ("man", "vac", "p1", "p2", "p3")
E32_MODES = ("man", "vac", "p1", "p2", "p3")


def _value(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    try:
        return float(value) if value is not None else None
    except (ValueError, TypeError):
        return None


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([TesyWaterHeater(coordinator, mac) for mac, row in (coordinator.data or {}).items()
                        if device_family(row.get("device") or {}) in {"heat_pump", "boiler_b15", "boiler_e32"}])


class TesyWaterHeater(CoordinatorEntity, WaterHeaterEntity):
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, mac):
        super().__init__(coordinator)
        self._mac = mac
        row = coordinator.data[mac]
        self._family = device_family(row.get("device") or {})
        self._attr_name = row.get("name") or "TESY Water Heater"
        self._attr_unique_id = f"{mac}_water_heater"
        self._attr_device_info = {"identifiers": {(DOMAIN, mac)}}
        if self._family == "heat_pump":
            self._attr_min_temp, self._attr_max_temp = 10, 75
            self._attr_operation_list = [*HP_MODES, "off"]
        elif self._family == "boiler_b15":
            self._attr_min_temp, self._attr_max_temp = 30, 75
            self._attr_operation_list = [*B15_MODES, "off"]
        else:
            # E32 exposes heat level (1..5), not degrees Celsius. Do not
            # impersonate its heat level as a physical temperature.
            self._attr_operation_list = [*E32_MODES, "off"]

    @property
    def _row(self):
        return (self.coordinator.data or {}).get(self._mac) or {}

    @property
    def _state(self):
        return self._row.get("state") or {}

    @property
    def available(self):
        return bool(self._row)

    @property
    def native_current_temperature(self):
        field = "current_temp" if self._family != "boiler_e32" else None
        return _value(self._state.get(field)) if field else None

    @property
    def native_target_temperature(self):
        return _value(self._state.get("set_temp" if self._family == "boiler_b15" else "temp"))

    @property
    def current_operation(self):
        st = self._state
        if self._family == "heat_pump":
            if str(st.get("power_status")).lower() == "off": return "off"
        elif str(st.get("stand_by")).lower() == "yes":
            return "off"
        mode = str(st.get("mode") or "").lower()
        return mode if mode in self.operation_list else None

    @property
    def extra_state_attributes(self):
        st = self._state
        keys = ("boost", "fan", "program_status", "heating", "shower", "alarmAnode", "alarmEvap", "error") if self._family == "heat_pump" else ("boost", "heat_level", "current_heat_level", "heater_state", "errorInd", "antifrost", "disinfection")
        return {k: st[k] for k in keys if k in st} | {"tesy_device_family": self._family}
