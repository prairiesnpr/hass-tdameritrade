"""The TDAmeritrade integration."""
import asyncio
import logging
import voluptuous as vol

from tdameritrade_api import AmeritradeAPI

from homeassistant.const import (
    ATTR_CREDENTIALS,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
)

from homeassistant.config_entries import ConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    aiohttp_client,
    config_entry_oauth2_flow,
    config_validation as cv,
)

from . import config_flow
from .const import (
    DOMAIN,
    TDA_URL,
    CONF_CONSUMER_KEY,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
    CONF_ACCOUNTS,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Inclusive(CONF_CONSUMER_KEY, ATTR_CREDENTIALS): cv.string,
                vol.Inclusive(CONF_ACCOUNTS, ATTR_CREDENTIALS): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = ["binary_sensor", "sensor"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the TDAmeritrade component."""

    if DOMAIN not in config:
        _LOGGER.warning(f"{DOMAIN} not in config. {config}")
        return True

    if CONF_CLIENT_ID in config[DOMAIN]:
        config_flow.TDAmeritradeFlowHandler.async_register_implementation(
            hass,
            config_flow.TDAmeritradeLocalOAuth2Implementation(
                hass,
                DOMAIN,
                config[DOMAIN][CONF_CONSUMER_KEY],
                None,
                OAUTH2_AUTHORIZE,
                OAUTH2_TOKEN,
            ),
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up TDAmeritrade from a config entry."""

    websession = aiohttp_client.async_get_clientsession(hass)

    implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(
        hass, entry
    )

    oauth_session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)

    auth = config_flow.TDAmeritradeOAuth(TDA_URL, websession, oauth_session)

    tda_api = AmeritradeAPI(auth)

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

        return await tda_api.async_place_order(
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
        res = await tda_api.async_get_quote(ticker=symbol)

        hass.states.async_set(
            f"get_quote_service.{symbol}",
            res[symbol]["lastPrice"],
            attributes=res[symbol],
        )

        return True

    hass.services.async_register(DOMAIN, "place_order", place_order_service)
    hass.services.async_register(DOMAIN, "get_quote", get_quote_service)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"TEST": "Test Entry"}

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
