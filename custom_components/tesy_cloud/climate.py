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


def _safe_float(v: Any) -> float | None:
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        return None


def _is_on(state: dict[str, Any]) -> bool:
    # state.status: "on"/"off"
    s = state.get("status")
    if isinstance(s, str):
        return s.lower() == "on"
    return False


def _hvac_action(state: dict[str, Any]) -> HVACAction:
    if not _is_on(state):
        return HVACAction.OFF
    h = state.get("heating")
    if isinstance(h, str) and h.lower() == "on":
        return HVACAction.HEATING
    return HVACAction.IDLE


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: TesyCloudCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    macs = list((coordinator.data or {}).keys())
    async_add_entities([TesyCloudConvector(coordinator, mac) for mac in macs])


class TesyCloudConvector(CoordinatorEntity[TesyCloudCoordinator], ClimateEntity):
    """A read-only climate entity."""

    _attr_temperature_unit = "°C"
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]

    def __init__(self, coordinator: TesyCloudCoordinator, mac: str) -> None:
        super().__init__(coordinator)
        self._mac = mac
        self._attr_unique_id = mac

    def _payload(self) -> dict[str, Any]:
        return (self.coordinator.data or {}).get(self._mac) or {}

    def _device(self) -> dict[str, Any]:
        dev = self._payload().get("device") or {}
        return dev if isinstance(dev, dict) else {}

    def _state(self) -> dict[str, Any]:
        st = self._payload().get("state") or {}
        return st if isinstance(st, dict) else {}

    @property
    def name(self) -> str:
        return self._payload().get("name") or f"Tesy Convector {self._mac.replace(':','')[-6:]}"

    @property
    def current_temperature(self) -> float | None:
        # In your response: state.current_temp
        return _safe_float(self._state().get("current_temp"))

    @property
    def target_temperature(self) -> float | None:
        # In your response: state.temp (setpoint)
        return _safe_float(self._state().get("temp"))

    @property
    def hvac_mode(self) -> HVACMode:
        return HVACMode.HEAT if _is_on(self._state()) else HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction:
        return _hvac_action(self._state())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        st = self._state()
        return {
            "opened_window": st.get("openedWindow"),
            "anti_frost": st.get("antiFrost"),
            "locked": st.get("lockedDevice"),
            "mode": st.get("mode"),
            "heating": st.get("heating"),
            "watt": st.get("watt"),
        }

    @property
    def device_info(self):
        dev = self._device()
        model = dev.get("model_type") or dev.get("model") or "Cloud Convector"
        sw = dev.get("firmware_version")
        return {
            "identifiers": {(DOMAIN, self._mac)},
            "manufacturer": "TESY",
            "name": self.name,
            "model": model,
            "sw_version": sw,
        }
