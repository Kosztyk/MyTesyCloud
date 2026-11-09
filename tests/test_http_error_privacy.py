"""Exercise credential-bearing HTTP failures without contacting MyTESY."""
import ast
import asyncio
import json
import logging
from pathlib import Path
import runpy
import traceback
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock

import aiohttp
from multidict import CIMultiDict, CIMultiDictProxy
from yarl import URL

COMP = Path(__file__).resolve().parents[1] / "custom_components" / "mytesy"
FAMILIES = runpy.run_path(str(COMP / "device_families.py"))


def load_api():
    """Load the real client; omit only the unused MQTT transport import."""
    tree = ast.parse((COMP / "api.py").read_text())
    tree.body = [node for node in tree.body
                 if not (isinstance(node, ast.ImportFrom) and node.level)
                 and not (isinstance(node, ast.Import)
                          and any(alias.name == "paho.mqtt.client" for alias in node.names))]
    namespace = {
        **runpy.run_path(str(COMP / "const.py")),
        "supports_water_heater": FAMILIES["supports_water_heater"],
        "mqtt": SimpleNamespace(),
        "__name__": "mytesy_http_error_test",
    }
    exec(compile(tree, str(COMP / "api.py"), "exec"), namespace)
    return SimpleNamespace(**namespace)


API = load_api()
PASSWORD = "private-password/&+secret"
REQUEST_URL = URL("https://ad.mytesy.com/rest/get-my-devices").with_query(
    userPass=PASSWORD, userEmail="private@example.com"
)


def response_error(status):
    headers = CIMultiDictProxy(CIMultiDict())
    info = aiohttp.RequestInfo(REQUEST_URL, "GET", headers, REQUEST_URL)
    return aiohttp.ClientResponseError(info, (), status=status, message="Server failure")


class Response:
    def __init__(self, status=200, data=None, json_error=None):
        self.status = status
        self.data = data if data is not None else {"userID": "123"}
        self.json_error = json_error

    def raise_for_status(self):
        if self.status >= 400:
            raise response_error(self.status)

    async def json(self, **kwargs):
        if self.json_error is not None:
            raise self.json_error
        return self.data


class Request:
    def __init__(self, response, error=None):
        self.response, self.error = response, error

    async def __aenter__(self):
        if self.error is not None:
            raise self.error
        return self.response

    async def __aexit__(self, *args):
        return False


class HttpPrivacy(unittest.IsolatedAsyncioTestCase):
    def make_api(self, response=None, error=None, resolve=False):
        request = Request(response or Response(), error)
        session = SimpleNamespace(get=Mock(return_value=request), post=Mock(return_value=request))
        return API.TesyCloudApi(session, "private@example.com", PASSWORD, "" if resolve else "123", "test")

    async def call(self, api, operation):
        if operation == "devices":
            return await api.async_get_my_devices()
        if operation == "statistics":
            return await api.async_get_device_statistics({"mac": "AA", "model_id": 1}, "power")
        if operation == "groups_get":
            return await api.async_group_request("get-my-groups")
        if operation == "groups_post":
            return await api.async_group_request("create-group", payload={"name": "Room"})
        return await api.async_resolve_user_id()

    async def assert_safe_failure(self, api, operation, expected=None):
        try:
            await self.call(api, operation)
        except API.TesyCloudError as err:
            formatted = "".join(traceback.format_exception(type(err), err, err.__traceback__))
            self.assertNotIn(PASSWORD, formatted)
            self.assertNotIn(str(REQUEST_URL), formatted)
            self.assertNotIn("userPass=", formatted)
            self.assertNotIn("private@example.com", formatted)
            self.assertIsNone(err.__cause__)
            self.assertTrue(err.__suppress_context__)
            if expected is not None:
                self.assertEqual(str(err), expected)
        else:
            self.fail("Expected a safe MyTESY error")

    async def test_http_status_errors_omit_credentials_and_original_traceback(self):
        for operation in ("devices", "statistics", "groups_get", "groups_post", "login"):
            for status in (429, 500, 502, 503):
                with self.subTest(operation=operation, status=status):
                    await self.assert_safe_failure(
                        self.make_api(Response(status), resolve=operation == "login"), operation,
                        f"MyTESY answered HTTP {status}",
                    )

    async def test_transport_timeouts_and_payload_errors_omit_exception_text(self):
        for operation in ("devices", "statistics", "groups_get", "groups_post", "login"):
            for error_type in (aiohttp.ClientConnectionError, aiohttp.ClientPayloadError, asyncio.TimeoutError):
                with self.subTest(operation=operation, error=error_type.__name__):
                    await self.assert_safe_failure(
                        self.make_api(error=error_type(str(REQUEST_URL)), resolve=operation == "login"), operation,
                    )

    async def test_json_errors_never_echo_response_body(self):
        for operation in ("devices", "statistics", "groups_get", "groups_post", "login"):
            with self.subTest(operation=operation):
                error = json.JSONDecodeError(str(REQUEST_URL), f"userPass={PASSWORD}", 0)
                await self.assert_safe_failure(
                    self.make_api(Response(json_error=error), resolve=operation == "login"), operation,
                )

    async def test_unauthorized_devices_and_login_still_trigger_reauthentication(self):
        for operation in ("devices", "login"):
            for status in (401, 403):
                with self.subTest(operation=operation, status=status):
                    with self.assertRaises(API.TesyCloudAuthError):
                        await self.call(self.make_api(Response(status), resolve=operation == "login"), operation)
        with self.assertRaises(API.TesyCloudAuthError):
            await self.call(self.make_api(Response(data={"error": 1})), "devices")

    async def test_successful_responses_are_preserved(self):
        data = {"AA": {"model": "B15", "state": {"set_temp": 50}}}
        self.assertEqual(await self.call(self.make_api(Response(data=data)), "devices"), data)
        self.assertEqual(await self.call(self.make_api(Response(data={"data": [1, 2]})), "statistics"), [1, 2])
        self.assertEqual(await self.call(self.make_api(Response(data={"groups": []})), "groups_get"), {"groups": []})
        self.assertEqual(await self.call(self.make_api(Response(), resolve=True), "login"), "123")

    async def test_app_log_failure_debug_message_omits_exception_text(self):
        api = self.make_api(error=aiohttp.ClientConnectionError(str(REQUEST_URL)))
        with self.assertLogs("mytesy_http_error_test", logging.DEBUG) as captured:
            await api._async_post_app_log(mac="AA", command="onOff", payload={"status": "on"})
        self.assertNotIn(PASSWORD, "".join(captured.output))
        self.assertNotIn("userPass", "".join(captured.output))

    async def test_water_heater_commands_cannot_reach_mqtt_or_app_log(self):
        for model in ("B15", "B15_1", "E32", "E32_1", "HPWH4_11", "HPWH4_11_1", "BOILER_UNKNOWN"):
            for command in ("powerOnOff", "setStandby", "setMode", "setTemp", "setProgram", "deleteProgram"):
                with self.subTest(model=model, command=command):
                    api = self.make_api()
                    api._mqtt.publish = Mock()
                    api._async_post_app_log = AsyncMock()
                    with self.assertRaisesRegex(API.TesyCloudError, "read-only"):
                        await api.async_send_command({"model": model, "mac": "AA", "token": "token"}, command, {})
                    api._mqtt.publish.assert_not_called()
                    api._async_post_app_log.assert_not_awaited()

    async def test_confirmed_convector_commands_still_publish(self):
        api = self.make_api()
        api._mqtt.publish = Mock()
        api._async_post_app_log = AsyncMock()
        await api.async_set_power({"model": "cn06as", "mac": "AA", "token": "token"}, True)
        api._mqtt.publish.assert_called_once_with(
            mac="AA", model="cn06as", token="token", command="onOff", payload={"status": "on"}, request_type="request"
        )
        api._async_post_app_log.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
