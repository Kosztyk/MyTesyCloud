"""Climate entities for MyTESY cloud convectors."""

from __future__ import annotations

import asyncio
from typing import Any

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature, HVACAction, HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import TesyCloudError
from .const import DOMAIN
from .coordinator import TesyCloudCoordinator

PRESET_COMFORT = "comfort"
PRESET_ECO = "eco"
PRESET_SLEEP = "sleep"
PRESET_MODES = [PRESET_COMFORT, PRESET_ECO, PRESET_SLEEP]


def _payload(coordinator: TesyCloudCoordinator, mac: str) -> dict[str, Any]:
    payload = (coordinator.data or {}).get(mac) or {}
    return payload if isinstance(payload, dict) else {}


def _state(coordinator: TesyCloudCoordinator, mac: str) -> dict[str, Any]:
    st = _payload(coordinator, mac).get("state") or {}
    return st if isinstance(st, dict) else {}


def _device(coordinator: TesyCloudCoordinator, mac: str) -> dict[str, Any]:
    payload = _payload(coordinator, mac)
    dev = payload.get("device")
    if isinstance(dev, dict):
        return dev
    return payload if isinstance(payload, dict) else {}


def _is_on(state: dict[str, Any]) -> bool:
    s = state.get("status")
    return isinstance(s, str) and s.lower() == "on"


def _hvac_action(state: dict[str, Any]) -> HVACAction:
    if not _is_on(state):
        return HVACAction.OFF
    h = state.get("heating")
    if isinstance(h, str) and h.lower() == "on":
        return HVACAction.HEATING
    return HVACAction.IDLE


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: TesyCloudCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities = [TesyCloudClimate(coordinator, mac) for mac in (coordinator.data or {}).keys()]
    async_add_entities(entities)


class TesyCloudClimate(CoordinatorEntity[TesyCloudCoordinator], ClimateEntity):
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    _attr_preset_modes = PRESET_MODES
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(self, coordinator: TesyCloudCoordinator, mac: str) -> None:
        super().__init__(coordinator)
        self._mac = mac
        base_name = _payload(coordinator, mac).get("name") or f"Tesy Convector {mac.replace(':', '')[-6:]}"
        self._attr_name = base_name
        self._attr_unique_id = mac

    @property
    def device_info(self):
        dev = _device(self.coordinator, self._mac)
        model = dev.get("model_type") or dev.get("model") or "Cloud Convector"
        sw = dev.get("firmware_version")
        return {
            "identifiers": {(DOMAIN, self._mac)},
            "manufacturer": "TESY",
            "name": self._attr_name,
            "model": model,
            "sw_version": sw,
        }

    @property
    def hvac_mode(self) -> HVACMode:
        return HVACMode.HEAT if _is_on(_state(self.coordinator, self._mac)) else HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction:
        return _hvac_action(_state(self.coordinator, self._mac))

    @property
    def current_temperature(self) -> float | None:
        v = _state(self.coordinator, self._mac).get("current_temp")
        try:
            return float(v)
        except Exception:
            return None

    @property
    def target_temperature(self) -> float | None:
        v = _state(self.coordinator, self._mac).get("temp")
        try:
            return float(v)
        except Exception:
            return None

    @property
    def preset_mode(self) -> str | None:
        mode = _state(self.coordinator, self._mac).get("mode")
        if isinstance(mode, str) and mode in PRESET_MODES:
            return mode
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        st = _state(self.coordinator, self._mac)
        keys = [
            "watt",
            "status",
            "heating",
            "openedWindow",
            "antiFrost",
            "lockedDevice",
            "uv",
            "adaptiveStart",
            "mode",
            "programStatus",
            "timeRemaining",
            "modeTime",
            "TCorrection",
        ]
        return {k: st.get(k) for k in keys if k in st}

    async def async_turn_on(self) -> None:
        device = _device(self.coordinator, self._mac)
        try:
            await self.coordinator.api.async_set_power(device, True)
            self._apply_optimistic_state(status="on")
            await self._async_refresh_after_command()
        except TesyCloudError as err:
            raise HomeAssistantError(f"Failed to turn on for {self._attr_name}: {err}") from err

    async def async_turn_off(self) -> None:
        device = _device(self.coordinator, self._mac)
        try:
            await self.coordinator.api.async_set_power(device, False)
            self._apply_optimistic_state(status="off", heating="off")
            await self._async_refresh_after_command()
        except TesyCloudError as err:
            raise HomeAssistantError(f"Failed to turn off for {self._attr_name}: {err}") from err

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.OFF:
            await self.async_turn_off()
            return
        if hvac_mode == HVACMode.HEAT:
            await self.async_turn_on()
            return
        raise HomeAssistantError(f"Unsupported HVAC mode for {self._attr_name}: {hvac_mode}")

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            raise HomeAssistantError(f"No target temperature provided for {self._attr_name}")
        device = _device(self.coordinator, self._mac)
        try:
            await self.coordinator.api.async_set_temperature(device, float(temperature))
            self._apply_optimistic_state(temp=float(temperature))
            await self._async_refresh_after_command()
        except TesyCloudError as err:
            raise HomeAssistantError(f"Failed to set temperature for {self._attr_name}: {err}") from err

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode not in PRESET_MODES:
            raise HomeAssistantError(f"Unsupported preset mode for {self._attr_name}: {preset_mode}")
        device = _device(self.coordinator, self._mac)
        try:
            await self.coordinator.api.async_set_mode(device, preset_mode)
            self._apply_optimistic_state(mode=preset_mode)
            await self._async_refresh_after_command()
        except TesyCloudError as err:
            raise HomeAssistantError(f"Failed to set preset for {self._attr_name}: {err}") from err

    def _apply_optimistic_state(self, **changes: Any) -> None:
        payload = _payload(self.coordinator, self._mac)
        state = payload.get("state")
        if isinstance(state, dict):
            state.update(changes)
        self.async_write_ha_state()

    async def _async_refresh_after_command(self) -> None:
        await asyncio.sleep(1.0)
        await self.coordinator.async_request_refresh()
