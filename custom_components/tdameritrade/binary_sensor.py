"""Platform for Market open sensor."""
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.util import dt

from datetime import timedelta

from aiohttp.client_exceptions import ClientConnectorError

from .const import DOMAIN


SCAN_INTERVAL = timedelta(seconds=120)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config, add_entities, discovery_info=None):
    """Set up the TDAmeritrade binary sensor platform."""
    sensors = []
    sensors.append(
        MarketOpenSensor(
            hass.data[DOMAIN][config.entry_id]["client"]
        )
    )
    add_entities(sensors)
    return True


class MarketOpenSensor(BinarySensorEntity):
    """Representation of a Sensor."""

    def __init__(self, client):
        """Initialize of a market binary sensor."""
        self._state = None
        self._name = "Market"
        self._client = client
        self._attributes = {"preMarket": False, "postMarket": False}

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
        _LOGGER.debug("Updating sensor: %s", self._name)
        resp = None
        try:
            resp = await self._client.async_get_market_hours("EQUITY")
        except ClientConnectorError as error:
            _LOGGER.warning("Client Exception: %s", error)
        if resp:
            try:
                if (
                    dt.as_utc(
                        dt.parse_datetime(
                            resp["equity"]["EQ"]["sessionHours"]["regularMarket"][0][
                                "start"
                            ]
                        )
                    )
                    < dt.utcnow()
                ) and (
                    dt.utcnow()
                    < dt.as_utc(
                        dt.parse_datetime(
                            resp["equity"]["EQ"]["sessionHours"]["regularMarket"][0]["end"]
                        )
                    )
                ):
                    self._state = True
                else:
                    self._state = False
            except KeyError:
                self._state = False
            try:
                if (
                    dt.as_utc(
                        dt.parse_datetime(
                            resp["equity"]["EQ"]["sessionHours"]["preMarket"][0]["start"]
                        )
                    )
                    < dt.utcnow()
                ) and (
                    dt.utcnow()
                    < dt.as_utc(
                        dt.parse_datetime(
                            resp["equity"]["EQ"]["sessionHours"]["preMarket"][0]["end"]
                        )
                    )
                ):
                    self._attributes["preMarket"] = True
                else:
                    self._attributes["preMarket"] = False
            except KeyError:
                self._attributes["preMarket"] = False

            try:

                if (
                    dt.as_utc(
                        dt.parse_datetime(
                            resp["equity"]["EQ"]["sessionHours"]["postMarket"][0]["start"]
                        )
                    )
                    < dt.utcnow()
                ) and (
                    dt.utcnow()
                    < dt.as_utc(
                        dt.parse_datetime(
                            resp["equity"]["EQ"]["sessionHours"]["postMarket"][0]["end"]
                        )
                    )
                ):
                    self._attributes["postMarket"] = True
                else:
                    self._attributes["postMarket"] = False
            except KeyError:
                self._attributes["postMarket"] = False
