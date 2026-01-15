"""Climate entities for MyTESY cloud convectors (read-only)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import HVACAction, HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TesyCloudCoordinator


def _payload(coordinator: TesyCloudCoordinator, mac: str) -> dict[str, Any]:
    return (coordinator.data or {}).get(mac) or {}


def _state(coordinator: TesyCloudCoordinator, mac: str) -> dict[str, Any]:
    st = _payload(coordinator, mac).get("state") or {}
    return st if isinstance(st, dict) else {}


def _device(coordinator: TesyCloudCoordinator, mac: str) -> dict[str, Any]:
    dev = _payload(coordinator, mac).get("device") or {}
    return dev if isinstance(dev, dict) else {}


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
    entities: list[ClimateEntity] = []
    for mac in (coordinator.data or {}).keys():
        entities.append(TesyCloudClimate(coordinator, mac))
    async_add_entities(entities)


class TesyCloudClimate(CoordinatorEntity[TesyCloudCoordinator], ClimateEntity):
    _attr_temperature_unit = "°C"
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]

    def __init__(self, coordinator: TesyCloudCoordinator, mac: str) -> None:
        super().__init__(coordinator)
        self._mac = mac
        base_name = _payload(coordinator, mac).get("name") or f"Tesy Convector {mac.replace(':','')[-6:]}"
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
    def hvac_modes(self):
        return [HVACMode.OFF, HVACMode.HEAT]

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
        except Exception:  # noqa: BLE001
            return None

    @property
    def target_temperature(self) -> float | None:
        v = _state(self.coordinator, self._mac).get("temp")
        try:
            return float(v)
        except Exception:  # noqa: BLE001
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        st = _state(self.coordinator, self._mac)
        # expose useful raw fields as attributes
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