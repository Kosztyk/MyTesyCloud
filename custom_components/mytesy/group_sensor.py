"""Read native TESY cloud device groups."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    stats = hass.data[DOMAIN][entry.entry_id]["statistics"]
    async_add_entities([TesyGroupsSensor(stats, entry.entry_id)])

class TesyGroupsSensor(CoordinatorEntity, SensorEntity):
    _attr_name = "TESY Cloud Device Groups"
    _attr_icon = "mdi:folder-multiple"
    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_cloud_groups"
    @property
    def _groups(self):
        raw = (self.coordinator.data or {}).get("__groups__")
        if isinstance(raw, list): return raw
        if isinstance(raw, dict):
            for key in ("groups", "data"):
                if isinstance(raw.get(key), list): return raw[key]
            if all(isinstance(v, dict) for v in raw.values()): return list(raw.values())
        return []
    @property
    def native_value(self): return len(self._groups)
    @property
    def extra_state_attributes(self):
        return {"groups": [{"id": x.get("id"), "name": x.get("name"), "devices": x.get("devices", [])} for x in self._groups[:32]]}
