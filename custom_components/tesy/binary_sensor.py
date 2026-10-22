"""Binary sensor entities for MyTESY cloud convectors (read-only)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import TesyCloudCoordinator
from .status import cloud_connected, derived_power_on, heating_active, parse_updated_at, stale_active_state, state_on


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
class _BinDesc:
    key: str
    name: str
    icon: str | None
    device_class: BinarySensorDeviceClass | None
    entity_category: EntityCategory | None
    value_fn: Callable[[TesyCloudCoordinator, str], bool]


BINARY_SENSORS: tuple[_BinDesc, ...] = (
    _BinDesc(
        key="device_on",
        name="Device On",
        icon="mdi:power",
        device_class=BinarySensorDeviceClass.POWER,
        entity_category=None,
        value_fn=lambda c, m: derived_power_on(_state(c, m)),
    ),
    _BinDesc(
        key="heating_active",
        name="Heating Active",
        icon="mdi:radiator",
        device_class=BinarySensorDeviceClass.HEAT,
        entity_category=None,
        value_fn=lambda c, m: heating_active(_state(c, m)),
    ),
    _BinDesc(
        key="window_open_detected",
        name="Open Window Detected",
        icon="mdi:window-open-variant",
        device_class=BinarySensorDeviceClass.WINDOW,
        entity_category=None,
        value_fn=lambda c, m: state_on(_state(c, m).get("openedWindow")),
    ),
    _BinDesc(
        key="anti_frost",
        name="Anti-frost Enabled",
        icon="mdi:snowflake",
        device_class=None,
        entity_category=None,
        value_fn=lambda c, m: state_on(_state(c, m).get("antiFrost")),
    ),
    _BinDesc(
        key="device_locked",
        name="Device Locked",
        icon="mdi:lock",
        device_class=BinarySensorDeviceClass.LOCK,
        entity_category=None,
        value_fn=lambda c, m: state_on(_state(c, m).get("lockedDevice")),
    ),
    _BinDesc(
        key="uv_enabled",
        name="UV Enabled",
        icon="mdi:weather-sunny-alert",
        device_class=None,
        entity_category=None,
        value_fn=lambda c, m: state_on(_state(c, m).get("uv")),
    ),
    _BinDesc(
        key="adaptive_start",
        name="Adaptive Start",
        icon="mdi:rocket-launch-outline",
        device_class=None,
        entity_category=None,
        value_fn=lambda c, m: state_on(_state(c, m).get("adaptiveStart")),
    ),
    # Diagnostics
    _BinDesc(
        key="has_internet",
        name="Has Internet",
        icon="mdi:earth",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c, m: cloud_connected(_device(c, m), _state(c, m)),
    ),
    _BinDesc(
        key="waiting_for_connection",
        name="Waiting For Connection",
        icon="mdi:lan-disconnect",
        device_class=None,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c, m: bool(_device(c, m).get("waitingForConnection")),
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: TesyCloudCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    macs = list((coordinator.data or {}).keys())

    entities: list[BinarySensorEntity] = []
    for mac in macs:
        for desc in BINARY_SENSORS:
            entities.append(TesyCloudBinarySensor(coordinator, mac, desc))

    async_add_entities(entities)


class TesyCloudBinarySensor(CoordinatorEntity[TesyCloudCoordinator], BinarySensorEntity):
    def __init__(self, coordinator: TesyCloudCoordinator, mac: str, desc: _BinDesc) -> None:
        super().__init__(coordinator)
        self._mac = mac
        self._desc = desc

        base_name = _payload(coordinator, mac).get("name") or f"Tesy Convector {mac.replace(':','')[-6:]}"
        self._attr_name = f"{base_name} {desc.name}"
        self._attr_unique_id = f"{mac}_{desc.key}"
        self._attr_icon = desc.icon
        self._attr_device_class = desc.device_class
        self._attr_entity_category = desc.entity_category

    @property
    def is_on(self) -> bool:
        return self._desc.value_fn(self.coordinator, self._mac)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self._desc.key != "has_internet":
            return None
        dev = _device(self.coordinator, self._mac)
        st = _state(self.coordinator, self._mac)
        return {
            "raw_hasInternet": dev.get("hasInternet"),
            "waitingForConnection": dev.get("waitingForConnection"),
            "reported_ip": dev.get("ip"),
            "last_cloud_update": st.get("updated_at"),
            "last_cloud_update_parsed": parse_updated_at(st.get("updated_at")).isoformat() if parse_updated_at(st.get("updated_at")) else None,
            "state_fresh": parse_updated_at(st.get("updated_at")) is not None,
            "stale_active_state": stale_active_state(st),
            "connectivity_source": "fresh_state_or_idle_presence__only_stale_heating_forces_disconnected",
        }

    @property
    def device_info(self):
        return _device_info(self.coordinator, self._mac)
