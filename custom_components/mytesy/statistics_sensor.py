"""Non-invasive native TESY history sensors."""
from __future__ import annotations
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

class TesyNativeStatSensor(CoordinatorEntity, SensorEntity):
    _attr_icon = "mdi:chart-line"
    def __init__(self, coordinator, device_coordinator, mac, kind):
        super().__init__(coordinator)
        self._mac, self._kind = mac, kind
        dev = (device_coordinator.data or {}).get(mac, {})
        self._attr_name = f"{dev.get('name', 'TESY')} Cloud {kind.title()} Statistics"
        self._attr_unique_id = f"{mac}_cloud_{kind}_statistics"
        self._attr_device_info = {"identifiers": {(DOMAIN, mac)}}

    @property
    def native_value(self):
        data = (self.coordinator.data or {}).get(self._mac, {}).get(self._kind)
        if data is None:
            return None
        if isinstance(data, list):
            return len(data)
        if isinstance(data, dict):
            return len(data)
        return None

    @property
    def extra_state_attributes(self):
        data = (self.coordinator.data or {}).get(self._mac, {}).get(self._kind)
        # Limit attributes to avoid recorder state/attribute size failures.
        if isinstance(data, list):
            return {"points": data[-8:], "total_points": len(data), "period": "daily"}
        if isinstance(data, dict):
            return {"series": {str(k): v[-8:] if isinstance(v, list) else v for k,v in data.items()}, "period": "daily"}
        return {"availability": "cloud endpoint did not return data"}
