"""Unofficial MyTESY (TESY Cloud) API client.

Your account works with:
  GET /rest/get-my-devices?userID=...&userEmail=...&userPass=...&lang=en

This client intentionally does NOT use legacy /rest/old-app-login (returns error=1).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import TESY_API_BASE, TESY_LANG, TESY_ORIGIN

_LOGGER = logging.getLogger(__name__)


class TesyCloudError(Exception):
    """Base error for TESY cloud."""


class TesyCloudAuthError(TesyCloudError):
    """Auth/credentials error."""


def _headers() -> dict[str, str]:
    # Keep these fairly close to the browser headers.
    return {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "dnt": "1",
        "origin": TESY_ORIGIN,
        "referer": f"{TESY_ORIGIN}/",
        "cache-control": "no-cache",
        "pragma": "no-cache",
    }


class TesyCloudApi:
    def __init__(self, session: aiohttp.ClientSession, user_id: str, username: str, password: str) -> None:
        self._session = session
        self._user_id = str(user_id).strip()
        self._username = username
        self._password = password
        self._lock = asyncio.Lock()

    async def async_get_my_devices(self) -> dict[str, Any]:
        """Return the raw JSON object from get-my-devices."""
        params = {
            "userID": self._user_id,
            "userEmail": self._username,
            "userPass": self._password,
            "lang": TESY_LANG,
        }
        url = f"{TESY_API_BASE}/get-my-devices"

        async with self._lock:
            async with self._session.get(
                url,
                params=params,
                headers=_headers(),
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                text = await resp.text()
                if resp.status >= 400:
                    raise TesyCloudError(f"get-my-devices failed (HTTP {resp.status}): {text[:200]}")

                try:
                    data = await resp.json(content_type=None)
                except Exception as e:  # noqa: BLE001
                    raise TesyCloudError(f"get-my-devices JSON parse failed: {e}; body[:200]={text[:200]!r}") from e

        # Observed invalid creds response: {"error":"1"}
        if isinstance(data, dict) and data.get("error") == "1":
            raise TesyCloudAuthError("MyTESY rejected credentials (error=1). Check userID/userEmail/userPass.")

        if not isinstance(data, dict):
            raise TesyCloudError(f"Unexpected response type: {type(data)}")

        return data
