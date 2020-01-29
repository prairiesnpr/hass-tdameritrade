"""Platform for Market open sensor."""

import logging

from homeassistant.components.binary_sensor import BinarySensorDevice
from .const import DOMAIN as TDA_DOMAIN
from homeassistant.util import dt

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config, add_entities, discovery_info=None):
    """Set up the TDAmeritrade binary sensor platform."""
    sensors = []
    for client in hass.data[TDA_DOMAIN].items():
        sensors.append(MarketOpenSensor(client))
    add_entities(sensors)
    return True


class MarketOpenSensor(BinarySensorDevice):
    """Representation of a Sensor."""

    def __init__(self, client):
        """Initialize of a market binary sensor."""
        self._state = None
        self._name = "Market"
        self._client = client[1]
        self._attributes = {}

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

    async def async_update(self):
        """Update the state of this sensor (Market Open)."""

        resp = await self._client.async_get_market_hours("EQUITY")

        market_open = dt.parse_datetime(
            resp["equity"]["EQ"]["sessionHours"]["regularMarket"][0]["start"]
        )
        market_close = dt.parse_datetime(
            resp["equity"]["EQ"]["sessionHours"]["regularMarket"][0]["end"]
        )

        if (dt.as_utc(market_open) < dt.utcnow()) and (
            dt.utcnow() < dt.as_utc(market_close)
        ):
            self._state = True
        else:
            self._state = False
        self._attributes = resp
