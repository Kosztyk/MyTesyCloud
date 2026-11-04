"""TESY B15/E32 boilers and HPWH4_11 heat pump water heater controls.

Command names and payloads extracted from MyTESY 3.0 Android source map.
"""
from __future__ import annotations

from homeassistant.components.water_heater import WaterHeaterEntity, WaterHeaterEntityFeature
from homeassistant.const import UnitOfTemperature, ATTR_TEMPERATURE
from homeassistant.exceptions import HomeAssistantError
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


def _enabled(value):
    return str(value).lower() in ("on", "yes", "1", "true")


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([TesyWaterHeater(coordinator, mac) for mac, row in (coordinator.data or {}).items()
                        if device_family(row.get("device") or {}) in {"heat_pump", "boiler_b15", "boiler_e32"}])


class TesyWaterHeater(CoordinatorEntity, WaterHeaterEntity):
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (WaterHeaterEntityFeature.TARGET_TEMPERATURE |
                                WaterHeaterEntityFeature.OPERATION_MODE |
                                WaterHeaterEntityFeature.ON_OFF)

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
            self._attr_supported_features = (WaterHeaterEntityFeature.OPERATION_MODE | WaterHeaterEntityFeature.ON_OFF)
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

    async def _send(self, command, data):
        try:
            await self.coordinator.api.async_send_command(self._row["device"], command, data)
            await self.coordinator.async_request_refresh()
        except Exception as exc:
            raise HomeAssistantError(f"TESY {self._family} {command} failed") from exc

    async def async_turn_on(self, **kwargs):
        if self._family == "heat_pump":
            await self._send("powerOnOff", {"state": "on"})
        else:
            await self._send("setStandby", {"setState": "no"})

    async def async_turn_off(self, **kwargs):
        if self._family == "heat_pump":
            await self._send("powerOnOff", {"state": "off"})
        else:
            await self._send("setStandby", {"setState": "yes"})

    async def async_set_temperature(self, **kwargs):
        value = kwargs.get(ATTR_TEMPERATURE)
        if value is None or not self.min_temp <= float(value) <= self.max_temp:
            raise HomeAssistantError("Invalid TESY water temperature")
        if self._family == "boiler_e32":
            raise HomeAssistantError("E32 uses heat levels; temperature control is not supported")
        if self._family == "heat_pump":
            mode = str(self._state.get("mode") or "hp")
            max_temp = 65 if mode == "hp" else 75
            if float(value) > max_temp:
                raise HomeAssistantError("Setpoint exceeds selected heat pump mode maximum")
            await self._send("setMode", {"mode": mode, "setTemp": int(value)})
        else:
            await self._send("setMode", {"mode": str(self._state.get("mode") or "man"), "temp": int(value)})

    async def async_set_operation_mode(self, operation_mode):
        if operation_mode == "off":
            await self.async_turn_off()
            return
        if operation_mode == "vac":
            raise HomeAssistantError("Vacation requires dates; configure it using the TESY mobile app")
        if operation_mode not in self.operation_list:
            raise HomeAssistantError("Unsupported TESY mode")
        st = self._state
        if self._family == "heat_pump":
            if operation_mode == "va":
                raise HomeAssistantError("Vacation needs dates; use TESY mobile app")
            temp = _value(st.get("temp")) or 50
            await self._send("setMode", {"mode": operation_mode, "setTemp": int(temp)})
        elif self._family == "boiler_b15":
            await self._send("setMode", {"mode": operation_mode, "temp": int(_value(st.get("set_temp")) or 45)})
        else:
            await self._send("setMode", {"mode": operation_mode, "heatLevel": int(_value(st.get("heat_level")) or 1)})
