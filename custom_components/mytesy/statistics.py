"""Optional, read-only TESY cloud statistics; isolated from core device refresh."""
from __future__ import annotations
from datetime import timedelta
import logging
from typing import Any
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
_LOGGER = logging.getLogger(__name__)

class TesyStatisticsCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    def __init__(self, hass, api, device_coordinator):
        super().__init__(hass, _LOGGER, name="mytesy_statistics", update_interval=timedelta(minutes=60))
        self.api = api
        self.devices = device_coordinator

    async def _async_update_data(self):
        result = {}
        for mac, payload in (self.devices.data or {}).items():
            device = payload.get("device") or {}
            result[mac] = {}
            for kind in ("power", "temperature", "state"):
                try:
                    result[mac][kind] = await self.api.async_get_device_statistics(device, kind)
                except Exception as exc:
                    _LOGGER.debug("TESY statistics %s/%s unavailable: %s", mac, kind, exc)
                    result[mac][kind] = (self.data or {}).get(mac, {}).get(kind)
        try:
            groups = await self.api.async_group_request("get-my-groups")
            result["__groups__"] = groups
        except Exception as exc:
            _LOGGER.debug("TESY group retrieval unavailable: %s", exc)
            result["__groups__"] = (self.data or {}).get("__groups__")
        return result
