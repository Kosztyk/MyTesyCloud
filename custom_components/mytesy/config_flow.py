"""Config flow for mytesy."""

from __future__ import annotations

import uuid
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
                user_id=user_input.get(CONF_USER_ID, ""),
                app_id=uuid.uuid4().hex[:16],
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
                unique = f'{user_input[CONF_USERNAME]}::{api._user_id}'
                await self.async_set_unique_id(unique)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input[CONF_USERNAME],
                    data={**user_input, CONF_USER_ID: api._user_id},
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(CONF_USER_ID): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reauth(self, entry_data):
        """Start reauthentication for an existing configuration entry."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Validate fresh credentials and reload the existing entry in place."""
        entry = self._get_reauth_entry()
        errors = {}
        if user_input is not None:
            api = TesyCloudApi(
                session=async_get_clientsession(self.hass),
                username=entry.data[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                # Force the login endpoint to validate the new password.
                user_id="",
                app_id=uuid.uuid4().hex[:16],
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
                if (entry.data.get(CONF_USER_ID) and
                        str(api._user_id) != str(entry.data[CONF_USER_ID])):
                    errors["base"] = "auth"
                else:
                    return self.async_update_reload_and_abort(
                        entry,
                        data_updates={CONF_PASSWORD: user_input[CONF_PASSWORD],
                                      CONF_USER_ID: api._user_id},
                    )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            errors=errors,
        )
