"""Config flow for tesy."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TesyCloudApi, TesyCloudAuthError, TesyCloudError
from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD, CONF_USER_ID


class TesyCloudConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            hass: HomeAssistant = self.hass
            session = async_get_clientsession(hass)
            api = TesyCloudApi(
                session=session,
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                user_id=user_input[CONF_USER_ID],
            )

            try:
                await api.async_get_my_devices()
            except TesyCloudAuthError:
                errors["base"] = "auth"
            except TesyCloudError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                # Use email + user_id as unique ID to prevent duplicates
                unique = f'{user_input[CONF_USERNAME]}::{user_input[CONF_USER_ID]}'
                await self.async_set_unique_id(unique)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input[CONF_USERNAME],
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_USER_ID): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
