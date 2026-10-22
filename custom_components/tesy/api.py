"""Unofficial MyTESY (TESY Cloud) API client (v4 portal compatible)."""

from __future__ import annotations

import asyncio
import json
import logging
import ssl
import threading
from typing import Any

import aiohttp
import paho.mqtt.client as mqtt

from .const import (
    TESY_API_BASE,
    TESY_LANG,
    TESY_MQTT_HOST,
    TESY_MQTT_PASSWORD,
    TESY_MQTT_PORT,
    TESY_MQTT_USERNAME,
    TESY_MQTT_VERSION,
    TESY_ORIGIN,
)

_LOGGER = logging.getLogger(__name__)


class TesyCloudError(Exception):
    """Base error for the MyTESY cloud client."""


class TesyCloudAuthError(TesyCloudError):
    """Authentication/authorization error."""


class _TesyMqttPublisher:
    """Minimal MQTT-over-WebSocket publisher for Tesy cloud commands."""

    def __init__(self, app_id: str) -> None:
        self._app_id = app_id

    def publish(self, *, mac: str, model: str, token: str, command: str, payload: dict[str, Any], request_type: str = "request") -> None:
        connect_event = threading.Event()
        publish_event = threading.Event()
        result: dict[str, Any] = {"connect_rc": None, "publish_rc": None, "error": None}

        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"ha_tesy_{self._app_id[:16]}",
            transport="websockets",
            protocol=mqtt.MQTTv311,
        )
        client.username_pw_set(TESY_MQTT_USERNAME, TESY_MQTT_PASSWORD)
        client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
        client.ws_set_options(path="/")

        topic = f"{TESY_MQTT_VERSION}/{mac}/{request_type}/{model}/{token}/{command}"
        body = json.dumps({"app_id": self._app_id, **payload})

        def on_connect(_client: mqtt.Client, _userdata: Any, _flags: Any, reason_code: Any, _properties: Any = None) -> None:
            rc = getattr(reason_code, "value", reason_code)
            result["connect_rc"] = int(rc)
            connect_event.set()
            if int(rc) == 0:
                info = _client.publish(topic, body)
                result["publish_rc"] = int(info.rc)
                if int(info.rc) != 0:
                    publish_event.set()
            else:
                publish_event.set()

        def on_publish(_client: mqtt.Client, _userdata: Any, _mid: int, _reason_code: Any = None, _properties: Any = None) -> None:
            publish_event.set()

        def on_disconnect(_client: mqtt.Client, _userdata: Any, _disconnect_flags: Any, reason_code: Any, _properties: Any = None) -> None:
            rc = getattr(reason_code, "value", reason_code)
            if rc not in (0, None) and result.get("error") is None:
                result["error"] = f"disconnect rc={rc}"
            connect_event.set()
            publish_event.set()

        client.on_connect = on_connect
        client.on_publish = on_publish
        client.on_disconnect = on_disconnect

        try:
            client.connect(TESY_MQTT_HOST, TESY_MQTT_PORT, keepalive=20)
            client.loop_start()

            if not connect_event.wait(10):
                raise TesyCloudError("Timed out connecting to Tesy MQTT broker")

            if result["connect_rc"] != 0:
                raise TesyCloudError(f"Tesy MQTT connect failed: rc={result['connect_rc']}")

            if not publish_event.wait(10):
                raise TesyCloudError("Timed out publishing command to Tesy MQTT broker")

            if result.get("publish_rc") not in (0, None):
                raise TesyCloudError(f"Tesy MQTT publish failed: rc={result['publish_rc']}")

            if result.get("error"):
                _LOGGER.debug("Tesy MQTT disconnect note after publish: %s", result["error"])
        except Exception as err:
            raise TesyCloudError(str(err)) from err
        finally:
            try:
                client.disconnect()
            except Exception:
                pass
            try:
                client.loop_stop()
            except Exception:
                pass


class TesyCloudApi:
    def __init__(self, session: aiohttp.ClientSession, username: str, password: str, user_id: str, app_id: str) -> None:
        self._session = session
        self._username = username
        self._password = password
        self._user_id = user_id
        self._mqtt = _TesyMqttPublisher(app_id=app_id)

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

        if isinstance(data, dict) and data.get("error") == "1":
            raise TesyCloudAuthError("MyTESY rejected credentials (error=1).")

        if not isinstance(data, dict):
            raise TesyCloudError(f"Unexpected response type: {type(data)}")

        return data

    async def async_send_command(
        self,
        device: dict[str, Any],
        command: str,
        payload: dict[str, Any],
        request_type: str = "request",
    ) -> None:
        mac = str(device.get("mac") or (device.get("state") or {}).get("mac") or "").strip()
        model = str(device.get("model") or "").strip()
        token = str(device.get("token") or "").strip()
        missing = [name for name, value in (("mac", mac), ("model", model), ("token", token)) if not value]
        if missing:
            raise TesyCloudError(
                f"Device is missing {','.join(missing)} and cannot be controlled. Available keys: {sorted(device.keys())}"
            )

        await asyncio.get_running_loop().run_in_executor(
            None,
            lambda: self._mqtt.publish(
                mac=mac,
                model=model,
                token=token,
                command=command,
                payload=payload,
                request_type=request_type,
            ),
        )

        await self._async_post_app_log(mac=mac, command=command, payload=payload)

    async def _async_post_app_log(self, *, mac: str, command: str, payload: dict[str, Any]) -> None:
        url = f"{TESY_API_BASE}/app-log"
        body = {
            "mac": mac,
            "command": command,
            "payload": payload,
            "userID": self._user_id,
            "userEmail": self._username,
            "userPass": self._password,
            "lang": TESY_LANG,
        }
        headers = {
            "Origin": TESY_ORIGIN,
            "Referer": f"{TESY_ORIGIN}/dashboard",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
        }
        try:
            async with self._session.post(url, json=body, headers=headers, timeout=aiohttp.ClientTimeout(total=15)):
                return
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Tesy app-log POST failed for %s/%s: %s", mac, command, err)

    async def async_set_power(self, device: dict[str, Any], on: bool) -> None:
        await self.async_send_command(device, "onOff", {"status": "on" if on else "off"})

    async def async_set_temperature(self, device: dict[str, Any], temperature: float) -> None:
        await self.async_send_command(device, "setTemp", {"temp": int(round(temperature))})

    async def async_set_mode(self, device: dict[str, Any], mode: str) -> None:
        await self.async_send_command(device, "setMode", {"name": mode})
