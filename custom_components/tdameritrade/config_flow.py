"""Config flow for TDAmeritrade."""
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.core import callback

from .const import DOMAIN, CONF_ACCOUNTS, TITLE


_LOGGER = logging.getLogger(__name__)


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

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        # Accounts are persisted as a list, but handled as comma separated string in UI

        if user_input is not None:
            # Preserve existing options, for example *_from_yaml markers
            data = {**self.config_entry.options, **user_input}
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
        return self.async_show_form(step_id="init", data_schema=data_schema)
