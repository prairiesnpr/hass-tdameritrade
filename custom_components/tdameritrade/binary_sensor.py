"""Platform for Market open sensor."""

import logging

from homeassistant.components.binary_sensor import BinarySensorDevice
from .const import DOMAIN as TDA_DOMAIN

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

    async def async_update(self):
        """Update the state of this sensor (Market Open)."""

        resp = await self._client.async_get_market_hours("EQUITY")
        self._state = resp["equity"]["EQ"]["isOpen"]
