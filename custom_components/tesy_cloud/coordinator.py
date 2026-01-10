"""Coordinator for MyTESY cloud polling."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import TesyCloudApi, TesyCloudError

_LOGGER = logging.getLogger(__name__)


def _guess_device_name(dev_obj: dict[str, Any], mac: str) -> str:
    # Prefer the explicit deviceName at the top level.
    name = dev_obj.get("deviceName")
    if isinstance(name, str) and name.strip():
        return name.strip()

    state = dev_obj.get("state")
    if isinstance(state, dict):
        n2 = state.get("deviceName")
        if isinstance(n2, str) and n2.strip():
            return n2.strip()

    return f"Tesy Convector {mac.replace(':', '')[-6:]}"


class TesyCloudCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, api: TesyCloudApi, update_interval) -> None:
        super().__init__(hass, _LOGGER, name="tesy_cloud", update_interval=update_interval)
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            raw = await self.api.async_get_my_devices()

            out: dict[str, Any] = {}
            for mac, dev_obj in raw.items():
                if not isinstance(dev_obj, dict):
                    continue
                state = dev_obj.get("state") or {}
                if not isinstance(state, dict):
                    state = {}

                mac_str = str(mac)
                out[mac_str] = {
                    "device": dev_obj,
                    "state": state,
                    "name": _guess_device_name(dev_obj, mac_str),
                }

            return out
        except TesyCloudError as err:
            raise UpdateFailed(str(err)) from err
