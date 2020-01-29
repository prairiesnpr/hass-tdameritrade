"""The TDAmeritrade integration."""
import asyncio

import voluptuous as vol

from typing import Any

from tdameritrade_api import AbstractAuth, AmeritradeAPI
from aiohttp import ClientSession

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
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
    TDA_URL,
    CONF_CONSUMER_KEY,
)


CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Required(CONF_CONSUMER_KEY): cv.string})},
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = ["binary_sensor", "sensor"]


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


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the TDAmeritrade component."""
    hass.data[DOMAIN] = {}

    if DOMAIN not in config:
        return

    config_flow.OAuth2FlowHandler.async_register_implementation(
        hass,
        TDAmeritradeLocalOAuth2Implementation(
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

    auth = TDAmeritradeOAuth(TDA_URL, websession, oauth_session)

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

    hass.data[DOMAIN][entry.entry_id] = tda_api

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
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
