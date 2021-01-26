"""Platform for Market open sensor."""
import asyncio
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.util import dt

from datetime import timedelta

from aiohttp.client_exceptions import ClientConnectorError

from .const import DOMAIN, PRE_MARKET, POST_MARKET, REG_MARKET

SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config, add_entities, discovery_info=None):
    """Set up the TDAmeritrade binary sensor platform."""
    sensors = []
    sensors.append(MarketOpenSensor(hass.data[DOMAIN][config.entry_id]["client"]))
    add_entities(sensors)
    return True


class MarketOpenSensor(BinarySensorEntity):
    """Representation of a Sensor."""

    def __init__(self, client):
        """Initialize of a market binary sensor."""
        self._state = False
        self._name = "Market"
        self._client = client
        self._attributes = {PRE_MARKET: None, POST_MARKET: None}
        self._available = False

    @property
    def device_class(self):
        """Return the class of this binary sensor."""
        return "Market"

    @property
    def name(self):
        """Return the name of the binary sensor."""
        return self._name

    @property
    def is_on(self):
        """Return the state of the binary sensor."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        return self._attributes

    @property
    def icon(self):
        """Return the class of this binary sensor."""
        return "mdi:finance"

    async def _is_market_open(self, market, resp):
        if resp:
            try:
                market_open = dt.parse_datetime(resp["equity"]["EQ"]["sessionHours"][market][0]["start"])
                market_close = dt.parse_datetime(resp["equity"]["EQ"]["sessionHours"][market][0]["end"])
                market_state = market_open < dt.now() < market_close
                _LOGGER.debug(
                    "%s Market Open: %s, Close: %s, Current Time: %s, Market Open: %s",
                    market,
                    market_open,
                    market_close,
                    dt.now(),
                    market_state
                )
                return market_state
            except KeyError:
                _LOGGER.warning("Failed to update '%s' sensor", market)
                return None
        return None

    async def async_update(self):
        """Update the state of this sensor (Market Open)."""
        _LOGGER.debug("Updating sensor: %s", self._name)
        resp = None
        try:
            resp = await self._client.async_get_market_hours("EQUITY")
            _LOGGER.debug("Market Open Resp: %s", resp)
        except ClientConnectorError as error:
            _LOGGER.warning("Client Exception: %s", error)

        if resp:
            self._available = True
            market_state = await asyncio.gather(
                self._is_market_open(REG_MARKET, resp),
                self._is_market_open(PRE_MARKET, resp),
                self._is_market_open(POST_MARKET, resp)
            )

            self._state, self._attributes[PRE_MARKET], self._attributes[POST_MARKET] = market_state
        else:
            self._available = False
