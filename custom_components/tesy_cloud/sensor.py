"""Sensor entities for MyTESY cloud convectors (read-only)."""

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


def _robust_power_on_hours(hist: Any, mac: str) -> float:
    """Power-on time cannot be lower than heating time for the same window."""
    status_hours = hist.get_hours_last_days(mac, "status", days=30)
    heating_hours = hist.get_hours_last_days(mac, "heating", days=30)
    return round(max(status_hours, heating_hours), 3)


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
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: TesyCloudCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    macs = list((coordinator.data or {}).keys())

    entities: list[SensorEntity] = []
    for mac in macs:
        for desc in SENSORS:
            entities.append(TesyCloudBasicSensor(coordinator, mac, desc))
        entities.append(TesyCloudEstimatedEnergySensor(coordinator, mac))
        entities.append(TesyCloudHistoryHoursSensor(coordinator, mac, kind="status"))
        entities.append(TesyCloudHistoryHoursSensor(coordinator, mac, kind="heating"))

    async_add_entities(entities)


class TesyCloudBasicSensor(CoordinatorEntity[TesyCloudCoordinator], SensorEntity):
    def __init__(self, coordinator: TesyCloudCoordinator, mac: str, desc: _SensorDesc) -> None:
        super().__init__(coordinator)
        self._mac = mac
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



class TesyCloudEstimatedEnergySensor(CoordinatorEntity[TesyCloudCoordinator], SensorEntity):
    """Rolling 30-day estimated energy (kWh) from heating history and selected wattage."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_icon = "mdi:counter"

    def __init__(self, coordinator: TesyCloudCoordinator, mac: str) -> None:
        super().__init__(coordinator)
        self._mac = mac
        base_name = _payload(coordinator, mac).get("name") or f"Tesy Convector {mac.replace(':','')[-6:]}"
        self._attr_name = f"{base_name} Energy (estimated, last 30 days)"
        self._attr_unique_id = f"{mac}_energy_estimated"

    def _configured_power_w(self) -> float:
        st = _state(self.coordinator, self._mac)
        w = _safe_float(st.get("watt"))
        return float(w) if w is not None else 0.0

    @property
    def native_value(self) -> float:
        hist = getattr(self.coordinator, "_history", None)
        if hist is None:
            return 0.0
        heating_hours = hist.get_hours_last_days(self._mac, "heating", days=30)
        power_kw = self._configured_power_w() / 1000.0
        return round(heating_hours * power_kw, 2)

    @property
    def device_info(self):
        return _device_info(self.coordinator, self._mac)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        hist = getattr(self.coordinator, "_history", None)
        heating_hours = hist.get_hours_last_days(self._mac, "heating", days=30) if hist is not None else 0.0
        power_hours = _robust_power_on_hours(hist, self._mac) if hist is not None else 0.0
        return {
            "window_days": 30,
            "estimated_from_heating_hours": heating_hours,
            "power_on_hours_last_30d": power_hours,
            "configured_power_w": self._configured_power_w(),
            "note": "Estimated from locally tracked 30-day heating hours and the currently reported wattage; not a calibrated meter.",
        }


class TesyCloudHistoryHoursSensor(CoordinatorEntity[TesyCloudCoordinator], SensorEntity):
    """Rolling 30-day time-on sensor, persisted by integration history storage."""
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTime.HOURS

    def __init__(self, coordinator: TesyCloudCoordinator, mac: str, kind: str) -> None:
        super().__init__(coordinator)
        self._mac = mac
        self._kind = kind  # "status" or "heating"
        base_name = _payload(coordinator, mac).get("name") or f"Tesy Convector {mac.replace(':','')[-6:]}"
        if kind == "status":
            self._attr_name = f"{base_name} Power On Time (last 30 days)"
            self._attr_unique_id = f"{mac}_power_on_time_30d"
            self._attr_icon = "mdi:power-plug"
        else:
            self._attr_name = f"{base_name} Heating Time (last 30 days)"
            self._attr_unique_id = f"{mac}_heating_time_30d"
            self._attr_icon = "mdi:radiator"

    @property
    def native_value(self) -> float:
        hist = getattr(self.coordinator, "_history", None)
        if hist is None:
            return 0.0
        if self._kind == "status":
            return _robust_power_on_hours(hist, self._mac)
        return hist.get_hours_last_days(self._mac, "heating", days=30)

    @property
    def device_info(self):
        return _device_info(self.coordinator, self._mac)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        tracked = "power_on" if self._kind == "status" else "heating"
        attrs = {
            "tracked_metric": tracked,
            "window_days": 30,
            "display_unit": "h",
            "note": "Rolling 30-day time tracked locally by the integration, not authoritative TESY cloud history.",
        }
        if self._kind == "status":
            hist = getattr(self.coordinator, "_history", None)
            if hist is not None:
                attrs["raw_status_hours_last_30d"] = hist.get_hours_last_days(self._mac, "status", days=30)
                attrs["heating_hours_last_30d"] = hist.get_hours_last_days(self._mac, "heating", days=30)
                attrs["calculated_as"] = "max(raw_status_hours, heating_hours)"
        return attrs
