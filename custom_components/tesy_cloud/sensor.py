"""Sensor entities for MyTESY cloud convectors (read-only).

Adds rich telemetry based on the get-my-devices payload, including an estimated
energy total derived from heating state + selected wattage.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import TesyCloudCoordinator


def _safe_float(v: Any) -> float | None:
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        return None


def _safe_int(v: Any) -> int | None:
    try:
        if v is None:
            return None
        return int(float(v))
    except Exception:
        return None


def _state_on(v: Any) -> bool:
    if isinstance(v, str):
        return v.lower() == "on"
    if isinstance(v, bool):
        return v
    return False


def _payload(coordinator: TesyCloudCoordinator, mac: str) -> dict[str, Any]:
    return (coordinator.data or {}).get(mac) or {}


def _device(coordinator: TesyCloudCoordinator, mac: str) -> dict[str, Any]:
    dev = _payload(coordinator, mac).get("device") or {}
    return dev if isinstance(dev, dict) else {}


def _state(coordinator: TesyCloudCoordinator, mac: str) -> dict[str, Any]:
    st = _payload(coordinator, mac).get("state") or {}
    return st if isinstance(st, dict) else {}


def _device_info(coordinator: TesyCloudCoordinator, mac: str) -> dict[str, Any]:
    dev = _device(coordinator, mac)
    model = dev.get("model_type") or dev.get("model") or "Cloud Convector"
    sw = dev.get("firmware_version")
    name = _payload(coordinator, mac).get("name") or f"Tesy Convector {mac.replace(':','')[-6:]}"
    return {
        "identifiers": {(DOMAIN, mac)},
        "manufacturer": "TESY",
        "name": name,
        "model": model,
        "sw_version": sw,
    }


@dataclass(frozen=True)
class _SensorDesc:
    key: str
    name: str
    icon: str | None
    device_class: SensorDeviceClass | None
    state_class: SensorStateClass | None
    unit: str | None
    entity_category: EntityCategory | None
    value_fn: Callable[[TesyCloudCoordinator, str], Any]


SENSORS: tuple[_SensorDesc, ...] = (
    _SensorDesc(
        key="power_setting",
        name="Heater Power",
        icon="mdi:flash",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        unit=UnitOfPower.WATT,
        entity_category=None,
        value_fn=lambda c, m: _safe_float(_state(c, m).get("watt")),
    ),
    _SensorDesc(
        key="mode",
        name="Mode",
        icon="mdi:heat-wave",
        device_class=None,
        state_class=None,
        unit=None,
        entity_category=None,
        value_fn=lambda c, m: _state(c, m).get("mode"),
    ),
    _SensorDesc(
        key="program_status",
        name="Program Status",
        icon="mdi:calendar-clock",
        device_class=None,
        state_class=None,
        unit=None,
        entity_category=None,
        value_fn=lambda c, m: _state(c, m).get("programStatus"),
    ),
    _SensorDesc(
        key="time_remaining",
        name="Time Remaining",
        icon="mdi:timer-sand",
        device_class=None,
        state_class=None,
        unit=UnitOfTime.MINUTES,
        entity_category=None,
        value_fn=lambda c, m: _safe_int(_state(c, m).get("timeRemaining")),
    ),
    _SensorDesc(
        key="mode_time",
        name="Mode Time",
        icon="mdi:timer-outline",
        device_class=None,
        state_class=None,
        unit=UnitOfTime.MINUTES,
        entity_category=None,
        value_fn=lambda c, m: _safe_int(_state(c, m).get("modeTime")),
    ),
    _SensorDesc(
        key="temperature_correction",
        name="Temperature Correction",
        icon="mdi:thermometer-chevron-up",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=None,
        unit=UnitOfTemperature.CELSIUS,
        entity_category=None,
        value_fn=lambda c, m: _safe_float(_state(c, m).get("TCorrection")),
    ),
    # Preset temps / timers
    _SensorDesc(
        key="comfort_temp",
        name="Comfort Temperature",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=None,
        unit=UnitOfTemperature.CELSIUS,
        entity_category=None,
        value_fn=lambda c, m: _safe_float((_state(c, m).get("comfortTemp") or {}).get("temp")),
    ),
    _SensorDesc(
        key="eco_temp",
        name="Eco Temperature",
        icon="mdi:leaf",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=None,
        unit=UnitOfTemperature.CELSIUS,
        entity_category=None,
        value_fn=lambda c, m: _safe_float((_state(c, m).get("ecoTemp") or {}).get("temp")),
    ),
    _SensorDesc(
        key="eco_time",
        name="Eco Time",
        icon="mdi:leaf-circle",
        device_class=None,
        state_class=None,
        unit=UnitOfTime.MINUTES,
        entity_category=None,
        value_fn=lambda c, m: _safe_int((_state(c, m).get("ecoTemp") or {}).get("time")),
    ),
    _SensorDesc(
        key="sleep_time",
        name="Sleep Time",
        icon="mdi:sleep",
        device_class=None,
        state_class=None,
        unit=UnitOfTime.MINUTES,
        entity_category=None,
        value_fn=lambda c, m: _safe_int((_state(c, m).get("sleepMode") or {}).get("time")),
    ),
    _SensorDesc(
        key="delayed_start_time",
        name="Delayed Start Time",
        icon="mdi:clock-plus",
        device_class=None,
        state_class=None,
        unit=UnitOfTime.MINUTES,
        entity_category=None,
        value_fn=lambda c, m: _safe_int((_state(c, m).get("delayedStart") or {}).get("time")),
    ),
    _SensorDesc(
        key="delayed_start_temp",
        name="Delayed Start Temperature",
        icon="mdi:clock-plus-outline",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=None,
        unit=UnitOfTemperature.CELSIUS,
        entity_category=None,
        value_fn=lambda c, m: _safe_float((_state(c, m).get("delayedStart") or {}).get("temp")),
    ),
    # Diagnostics
    _SensorDesc(
        key="firmware_version",
        name="Firmware Version",
        icon="mdi:chip",
        device_class=None,
        state_class=None,
        unit=None,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c, m: _device(c, m).get("firmware_version"),
    ),
    _SensorDesc(
        key="wifi_ssid",
        name="Wi-Fi SSID",
        icon="mdi:wifi",
        device_class=None,
        state_class=None,
        unit=None,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c, m: _device(c, m).get("wifi_ssid"),
    ),
    _SensorDesc(
        key="reported_ip",
        name="Reported WAN IP",
        icon="mdi:ip-network",
        device_class=None,
        state_class=None,
        unit=None,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c, m: _device(c, m).get("ip"),
    ),
    _SensorDesc(
        key="timezone",
        name="Device Timezone",
        icon="mdi:map-clock",
        device_class=None,
        state_class=None,
        unit=None,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c, m: _device(c, m).get("timezone"),
    ),
    _SensorDesc(
        key="device_time",
        name="Device Time (reported)",
        icon="mdi:clock-outline",
        device_class=None,
        state_class=None,
        unit=None,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c, m: _device(c, m).get("time"),
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: TesyCloudCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    macs = list((coordinator.data or {}).keys())

    entities: list[SensorEntity] = []
    for mac in macs:
        for desc in SENSORS:
            entities.append(TesyCloudBasicSensor(coordinator, mac, desc))
        entities.append(TesyCloudEstimatedEnergySensor(coordinator, mac))

    async_add_entities(entities)


class TesyCloudBasicSensor(CoordinatorEntity[TesyCloudCoordinator], SensorEntity):
    def __init__(self, coordinator: TesyCloudCoordinator, mac: str, desc: _SensorDesc) -> None:
        super().__init__(coordinator)
        self._mac = mac
        self.entity_description = None  # to keep HA from trying to auto-map
        self._desc = desc

        base_name = _payload(coordinator, mac).get("name") or f"Tesy Convector {mac.replace(':','')[-6:]}"
        self._attr_name = f"{base_name} {desc.name}"
        self._attr_unique_id = f"{mac}_{desc.key}"
        self._attr_icon = desc.icon
        self._attr_device_class = desc.device_class
        self._attr_state_class = desc.state_class
        self._attr_native_unit_of_measurement = desc.unit
        self._attr_entity_category = desc.entity_category

    @property
    def native_value(self):
        return self._desc.value_fn(self.coordinator, self._mac)

    @property
    def device_info(self):
        return _device_info(self.coordinator, self._mac)


class TesyCloudEstimatedEnergySensor(CoordinatorEntity[TesyCloudCoordinator], SensorEntity, RestoreEntity):
    """Estimated energy (kWh) based on heating on/off and selected wattage.

    Important: `state.watt` appears to represent selected heater power (W), not a live meter.
    We only accumulate while `state.heating == "on"`.
    """

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_icon = "mdi:counter"

    def __init__(self, coordinator: TesyCloudCoordinator, mac: str) -> None:
        super().__init__(coordinator)
        self._mac = mac
        base_name = _payload(coordinator, mac).get("name") or f"Tesy Convector {mac.replace(':','')[-6:]}"
        self._attr_name = f"{base_name} Energy (estimated)"
        self._attr_unique_id = f"{mac}_energy_estimated"

        self._energy_kwh: float = 0.0
        self._last_ts = dt_util.utcnow()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state not in (None, "unknown", "unavailable"):
            try:
                self._energy_kwh = float(last.state)
            except Exception:
                self._energy_kwh = 0.0
        self._last_ts = dt_util.utcnow()

    def _effective_power_w(self) -> float:
        st = _state(self.coordinator, self._mac)
        heating = _state_on(st.get("heating"))
        if not heating:
            return 0.0
        w = _safe_float(st.get("watt"))
        return float(w) if w is not None else 0.0

    @property
    def native_value(self) -> float:
        # Update accumulation on every state read (coordinator refreshes periodically).
        now = dt_util.utcnow()
        dt_seconds = (now - self._last_ts).total_seconds()
        if dt_seconds < 0:
            dt_seconds = 0
        # Cap to avoid huge jumps if system time changed or long downtime.
        dt_seconds = min(dt_seconds, 6 * 3600)

        p_w = self._effective_power_w()
        self._energy_kwh += (p_w / 1000.0) * (dt_seconds / 3600.0)
        self._last_ts = now
        return round(self._energy_kwh, 4)

    @property
    def device_info(self):
        return _device_info(self.coordinator, self._mac)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "effective_power_w": self._effective_power_w(),
            "note": "Estimated from heating state + selected power; not a calibrated meter.",
        }
