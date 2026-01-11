"""Config flow for MyTESY Cloud Convector."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TesyCloudApi, TesyCloudAuthError, TesyCloudError
from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD, CONF_USER_ID

_LOGGER = logging.getLogger(__name__)


async def _validate(hass: HomeAssistant, data: dict) -> None:
    api = TesyCloudApi(
        session=async_get_clientsession(hass),
        user_id=data[CONF_USER_ID],
        username=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
    )
    devices = await api.async_get_my_devices()
    if not isinstance(devices, dict) or len(devices) == 0:
        raise TesyCloudError("No devices returned from get-my-devices.")


class TesyCloudConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await _validate(self.hass, user_input)
            except TesyCloudAuthError:
                errors["base"] = "auth"
            except TesyCloudError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected MyTESY error")
                errors["base"] = "unknown"
            else:
                unique = f"{user_input[CONF_USERNAME]}:{user_input[CONF_USER_ID]}"
                await self.async_set_unique_id(unique)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input[CONF_USERNAME],
                    data={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_USER_ID: str(user_input[CONF_USER_ID]),
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_USER_ID): vol.Coerce(str),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
