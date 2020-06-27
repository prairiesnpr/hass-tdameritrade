"""Config flow for TDAmeritrade."""
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.core import callback
from tdameritrade_api import AbstractAuth
from aiohttp import ClientSession
from typing import Any

from .const import (
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
    CONF_CONSUMER_KEY,
    CONF_ACCOUNTS,
    TITLE,
)


_LOGGER = logging.getLogger(__name__)


class TDAmeritradeLocalOAuth2Implementation(
    config_entry_oauth2_flow.LocalOAuth2Implementation
):
    """Local OAuth2 implementation."""

    async def async_resolve_external_data(self, external_data: Any) -> dict:
        """Resolve the authorization code to tokens."""
        return await self._token_request(
            {
                "grant_type": "authorization_code",
                "code": external_data,
                "redirect_uri": self.redirect_uri,
                "access_type": "offline",
            }
        )


class TDAmeritradeOAuth(AbstractAuth):
    """TDAmeritrade Authentication using OAuth2."""

    def __init__(
        self,
        host: str,
        websession: ClientSession,
        oauth_session: config_entry_oauth2_flow.OAuth2Session,
    ):
        """Initialize TDA auth."""
        super().__init__(websession, host)
        self._oauth_session = oauth_session

    async def async_get_access_token(self):
        """Return a valid access token."""
        if not self._oauth_session.valid_token:
            await self._oauth_session.async_ensure_token_valid()

        return self._oauth_session.token["access_token"]


class TDAmeritradeFlowHandler(
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
        if user_input:
            self.consumer_key = user_input[CONF_CONSUMER_KEY]
            self.accounts = user_input[CONF_ACCOUNTS]
            if not isinstance(self.accounts, list):
                self.accounts = [x.strip() for x in self.accounts.split(",")]

            TDAmeritradeFlowHandler.async_register_implementation(
                self.hass,
                TDAmeritradeLocalOAuth2Implementation(
                    self.hass,
                    DOMAIN,
                    self.consumer_key,
                    None,
                    OAUTH2_AUTHORIZE,
                    OAUTH2_TOKEN,
                ),
            )

            return await self.async_step_pick_implementation()

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
        _LOGGER.warning(data)
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

    async def async_step_tda_settings(self, user_input=None):
        """Handle options flow."""
        # Accounts are persisted as a list, but handled as comma separated string in UI

        if user_input is not None:
            # Preserve existing options, for example *_from_yaml markers
            _LOGGER.warning(self.config_entry)
            data = {**self.config_entry[CONF_ACCOUNTS], **user_input}
            if not isinstance(data[CONF_ACCOUNTS], list):
                data[CONF_ACCOUNTS] = [
                    x.strip() for x in data[CONF_ACCOUNTS].split(",")
                ]
            return self.async_create_entry(title=TITLE, data=data)

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_ACCOUNTS,
                    default=", ".join(self.config_entry.options.get(CONF_ACCOUNTS, [])),
                ): str,
            }
        )
        return self.async_show_form(step_id="tda_settings", data_schema=data_schema)
