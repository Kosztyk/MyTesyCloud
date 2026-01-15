"""Unofficial MyTESY (TESY Cloud) API client (v4 portal compatible).

Observed working endpoint:
  GET /rest/get-my-devices?userID=<id>&userEmail=<email>&userPass=<pass>&lang=en

This client is intentionally minimal and read-only.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import TESY_API_BASE, TESY_LANG, TESY_ORIGIN

_LOGGER = logging.getLogger(__name__)


class TesyCloudError(Exception):
    """Base error for the MyTESY cloud client."""


class TesyCloudAuthError(TesyCloudError):
    """Authentication/authorization error."""


class TesyCloudApi:
    def __init__(self, session: aiohttp.ClientSession, username: str, password: str, user_id: str) -> None:
        self._session = session
        self._username = username
        self._password = password
        self._user_id = user_id

    async def async_get_my_devices(self) -> dict[str, Any]:
        url = f"{TESY_API_BASE}/get-my-devices"
        params = {
            "userID": self._user_id,
            "userEmail": self._username,
            "userPass": self._password,
            "lang": TESY_LANG,
        }
        headers = {
            "Origin": TESY_ORIGIN,
            "Referer": f"{TESY_ORIGIN}/",
            "Accept": "application/json, text/plain, */*",
        }

        try:
            async with self._session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                text = await resp.text()
                try:
                    data = await resp.json(content_type=None)
                except Exception as e:  # noqa: BLE001
                    raise TesyCloudError(f"JSON parse failed: {e}; body[:200]={text[:200]!r}") from e

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise TesyCloudError(f"Connection error: {e}") from e

        # Observed invalid creds response: {"error":"1"}
        if isinstance(data, dict) and data.get("error") == "1":
            raise TesyCloudAuthError("MyTESY rejected credentials (error=1).")

        if not isinstance(data, dict):
            raise TesyCloudError(f"Unexpected response type: {type(data)}")

        return data
