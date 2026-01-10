"""Binary sensor entities for MyTESY cloud convectors (read-only)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TesyCloudCoordinator


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
        value_fn=lambda c, m: _state_on(_state(c, m).get("status")),
    ),
    _BinDesc(
        key="heating_active",
        name="Heating Active",
        icon="mdi:radiator",
        device_class=BinarySensorDeviceClass.HEAT,
        entity_category=None,
        value_fn=lambda c, m: _state_on(_state(c, m).get("heating")),
    ),
    _BinDesc(
        key="window_open_detected",
        name="Open Window Detected",
        icon="mdi:window-open-variant",
        device_class=BinarySensorDeviceClass.WINDOW,
        entity_category=None,
        value_fn=lambda c, m: _state_on(_state(c, m).get("openedWindow")),
    ),
    _BinDesc(
        key="anti_frost",
        name="Anti-frost Enabled",
        icon="mdi:snowflake",
        device_class=None,
        entity_category=None,
        value_fn=lambda c, m: _state_on(_state(c, m).get("antiFrost")),
    ),
    _BinDesc(
        key="device_locked",
        name="Device Locked",
        icon="mdi:lock",
        device_class=BinarySensorDeviceClass.LOCK,
        entity_category=None,
        value_fn=lambda c, m: _state_on(_state(c, m).get("lockedDevice")),
    ),
    _BinDesc(
        key="uv_enabled",
        name="UV Enabled",
        icon="mdi:weather-sunny-alert",
        device_class=None,
        entity_category=None,
        value_fn=lambda c, m: _state_on(_state(c, m).get("uv")),
    ),
    _BinDesc(
        key="adaptive_start",
        name="Adaptive Start",
        icon="mdi:rocket-launch-outline",
        device_class=None,
        entity_category=None,
        value_fn=lambda c, m: _state_on(_state(c, m).get("adaptiveStart")),
    ),
    # Diagnostics
    _BinDesc(
        key="has_internet",
        name="Has Internet",
        icon="mdi:earth",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c, m: bool(_device(c, m).get("hasInternet")),
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
    def device_info(self):
        return _device_info(self.coordinator, self._mac)
