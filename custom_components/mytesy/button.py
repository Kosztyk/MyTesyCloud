"""TESY manual refresh (REST state + optional native statistics)."""
from homeassistant.components.button import ButtonEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([TesyRefreshButton(data["coordinator"], data["statistics"], mac)
                        for mac in (data["coordinator"].data or {})])

class TesyRefreshButton(ButtonEntity):
    _attr_icon = "mdi:refresh"
    def __init__(self, coordinator, stats, mac):
        self.coordinator, self.stats, self.mac=coordinator,stats,mac
        self._attr_name=f"{(coordinator.data or {}).get(mac, {}).get('name', 'TESY')} Refresh Cloud Data"
        self._attr_unique_id=f"{mac}_refresh_cloud_data"
        self._attr_device_info={"identifiers": {(DOMAIN,mac)}}
    async def async_press(self):
        await self.coordinator.async_request_refresh()
        await self.stats.async_request_refresh()
