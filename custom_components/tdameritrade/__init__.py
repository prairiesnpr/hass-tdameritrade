"""The TDAmeritrade integration."""
import asyncio
import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    aiohttp_client,
    config_entry_oauth2_flow,
    config_validation as cv,
)

from tdameritrade_api import AmeritradeAPI

from . import api, config_flow

from .const import (
    DOMAIN,
    CONF_CONSUMER_KEY,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
    CONF_ACCOUNTS,
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_CONSUMER_KEY): cv.string,
                vol.Required(CONF_ACCOUNTS): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = ["binary_sensor", "sensor"]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the TDAmeritrade component."""
    hass.data[DOMAIN] = {}

    if DOMAIN not in config:
        return True

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up TDAmeritrade from a config entry."""

    config_flow.OAuth2FlowHandler.async_register_implementation(
        hass,
        config_entry_oauth2_flow.LocalOAuth2Implementation(
            hass,
            entry.domain,
            entry.data["consumer_key"],
            None,
            OAUTH2_AUTHORIZE,
            OAUTH2_TOKEN,
        ),
    )

    implementation = (
        await config_entry_oauth2_flow.async_get_config_entry_implementation(
            hass, entry
        )
    )

    session = config_entry_oauth2_flow.OAuth2Session(
        hass, entry, implementation
    )

    auth = api.AsyncConfigEntryAuth(
        aiohttp_client.async_get_clientsession(hass), session
    )

    client = AmeritradeAPI(auth)

    async def place_order_service(call):
        """Handle a place trade service call."""

        price = call.data["price"]
        instruction = call.data["instruction"]
        quantity = call.data["quantity"]
        symbol = call.data["symbol"]
        account_id = call.data["account_id"]
        order_type = call.data["order_type"]
        session = call.data["session"]
        duration = call.data["duration"]
        order_strategy_type = call.data["orderStrategyType"]
        asset_type = call.data["assetType"]

        return await client.async_place_order(
            price,
            instruction,
            quantity,
            symbol,
            account_id,
            order_type=order_type,
            session=session,
            duration=duration,
            orderStrategyType=order_strategy_type,
            assetType=asset_type,
        )

    async def get_quote_service(call):
        """Handle a place trade service call."""
        symbol = call.data["symbol"]
        res = await client.async_get_quote(ticker=symbol)

        hass.states.async_set(
            f"get_quote_service.{symbol}",
            res[symbol]["lastPrice"],
            attributes=res[symbol],
        )

        return True

    hass.services.async_register(DOMAIN, "place_order", place_order_service)
    hass.services.async_register(DOMAIN, "get_quote", get_quote_service)

    hass.data.setdefault(DOMAIN, {})
    hass_data = dict(entry.data)
    unsub_options_update_listener = entry.add_update_listener(
        options_update_listener
    )
    hass_data["unsub_options_update_listener"] = unsub_options_update_listener
    hass_data["client"] = AmeritradeAPI(auth)
    hass.data[DOMAIN][entry.entry_id] = hass_data

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def options_update_listener(hass, config_entry):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Unload a config entry."""
    _LOGGER.debug("Unload Requested")
    if config_entry.state == "loaded":
        try:
            unload_res = await asyncio.gather(
                *[
                    hass.config_entries.async_forward_entry_unload(
                        config_entry,
                        component
                    )
                    for component in PLATFORMS
                ],
                return_exceptions=True
            )
            unload_ok = all(unload_res)
            if unload_ok:
                hass.data[DOMAIN].pop(config_entry.entry_id)
                _LOGGER.debug("Unload Completed")
                return True
            _LOGGER.debug("Failed to Unload: %s", unload_res)
        except ValueError:
            _LOGGER.debug("Unload Failed with ValueError")
        return False
    _LOGGER.debug("Config entry not loaded")
    return True
