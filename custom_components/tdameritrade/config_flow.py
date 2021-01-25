"""Config flow for TDAmeritrade."""

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.core import callback

from tdameritrade_api import AbstractAuth
from copy import deepcopy


from typing import Any

from .const import (
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
    CONF_CONSUMER_KEY,
    CONF_ACCOUNTS,
    TITLE,
)


class LocalOAuth2Implementation(config_entry_oauth2_flow.LocalOAuth2Implementation):
    """Local OAuth2 implementation."""

    async def async_resolve_external_data(self, external_data: Any) -> dict:
        """Resolve the authorization code to tokens."""
        return await self._token_request(
            {
                "grant_type": "authorization_code",
                "code": external_data["code"],
                "redirect_uri": self.redirect_uri,
                "access_type": "offline",
            }
        )


class OAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Config flow to handle TDAmeritrade OAuth2 authentication."""

    DOMAIN = DOMAIN
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

    def __init__(self):
        """Initialize the Hass config flow."""
        super().__init__()
        self.consumer_key = None
        self.accounts = None

    async def async_step_user(self, user_input=None):
        """Handle a flow started by a user."""
        await self.async_set_unique_id(DOMAIN)

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input:
            self.consumer_key = user_input[CONF_CONSUMER_KEY]
            self.accounts = user_input[CONF_ACCOUNTS]
            if self.accounts and not isinstance(self.accounts, list):
                self.accounts = [x.strip() for x in self.accounts.split(",") if x]
            OAuth2FlowHandler.async_register_implementation(
                self.hass,
                LocalOAuth2Implementation(
                    self.hass,
                    DOMAIN,
                    self.consumer_key,
                    None,
                    OAUTH2_AUTHORIZE,
                    OAUTH2_TOKEN,
                ),
            )
            implementations = await config_entry_oauth2_flow.async_get_implementations(
                self.hass, self.DOMAIN
            )
            self.flow_impl = implementations[DOMAIN]
            return await self.async_step_auth()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CONSUMER_KEY): str,
                    vol.Optional(CONF_ACCOUNTS): str,
                },
            ),
        )

    async def async_oauth_create_entry(self, data):
        """Create an entry for the flow.

        Ok to override if you want to provide extra info.
        """
        data[CONF_CONSUMER_KEY] = self.consumer_key
        data[CONF_ACCOUNTS] = self.accounts
        return self.async_create_entry(title=TITLE, data=data)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a option flow for TDAmeritrade."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry
        if self.config_entry.options:
            self.accounts = deepcopy(self.config_entry.options[CONF_ACCOUNTS])
        else:
            self.accounts = deepcopy(self.config_entry.data[CONF_ACCOUNTS])

    async def async_step_init(self, user_input=None):
        """Update the accounts."""
        if user_input:
            if user_input.get(CONF_ACCOUNTS):
                old_accounts = self.accounts
                self.accounts = [
                    x.strip() for x in user_input[CONF_ACCOUNTS].split(",") if x
                ]
            return await self._update_accounts()

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_ACCOUNTS,
                    default=",".join(self.accounts),
                ): str,
            }
        )
        return self.async_show_form(step_id="init", data_schema=data_schema)

    async def _update_accounts(self):
        """Update config entry options."""
        return self.async_create_entry(title="", data={CONF_ACCOUNTS: self.accounts})
