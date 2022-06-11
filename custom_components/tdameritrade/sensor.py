"""Support for the TDAmeritrade sensors."""
import logging

from homeassistant.helpers.entity import Entity
from datetime import timedelta
from homeassistant.core import callback
from aiohttp.client_exceptions import ClientConnectorError, ClientResponseError, ServerDisconnectedError
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    CONF_ACCOUNTS,
    DOMAIN,
    CLOSED_SCAN_INTERVAL,
    OPEN_SCAN_INTERVAL,
    AVAILABLE_FUNDS,
    CURRENT_BALANCES,
    SECURITIES_ACCOUNT,
    CASH_AVAILABLE_FOR_TRADEING,
    TYPE,
    MARGIN,
    CASH,
    CLIENT,
)
from homeassistant.const import STATE_OFF, STATE_ON

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the TDAmeritrade sensor platform."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    accounts = config_entry.data[CONF_ACCOUNTS]
    sensors = [
        AccountValueSensor(config[CLIENT], account_id) for account_id in accounts
    ]
    async_add_entities(sensors)
    return True


class AccountValueSensor(Entity):
    """Representation of Available Funds sensors."""

    def __init__(self, client, account_id):
        """Initialize of a account sensor."""
        self._name = "Available Funds"
        self._client = client
        self._account_id = account_id
        self._current_value = None
        self._attributes = {}
        self._available = False
        self._last_updated = None
        self._interval = timedelta(seconds=10)
        self._remove_update_interval = None
        self._should_poll = False

    @property
    def should_poll(self):
        """Return if this sensor should pull."""
        return self._should_poll

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._current_value

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._name} #--{self._account_id[-4:]}"

    @property
    def account_id(self):
        """Return the account_id of the sensor."""
        return self._account_id

    @property
    def unique_id(self):
        """Return the unique_id of the sensor."""
        return f"{DOMAIN}.{self._name}_{self.account_id}"

    @property
    def available(self):
        """Return the availability of the sensor."""
        return self._available

    @property
    def unit_of_measurement(self):
        """Return the unit_of_measurement of the device."""
        return "Dollars"

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes."""
        return self._attributes

    @property
    def icon(self):
        """Return the class of this sensor."""
        return "mdi:cash"

    @callback
    async def async_schedule_update(self, event_time=None):
        """Update the entity."""
        self.async_schedule_update_ha_state(True)

    async def async_added_to_hass(self):
        """Start custom polling."""
        self._remove_update_interval = async_track_time_interval(
            self.hass, self.async_schedule_update, self._interval
        )

    async def async_will_remove_from_hass(self):
        """Stop custom polling."""
        self._remove_update_interval()

    async def async_update(self):
        """Update the state from the sensor."""
        _LOGGER.debug("Updating sensor: %s, id: %s", self._name, self.entity_id)
        resp = None
        try:
            resp = await self._client.async_get_account(self._account_id)
        except (ClientConnectorError, ClientResponseError, ServerDisconnectedError) as error:
            _LOGGER.warning("Client Exception: %s", error)
        if resp:
            self._available = True
            self._attributes = resp[SECURITIES_ACCOUNT]
            if resp[SECURITIES_ACCOUNT][TYPE] == MARGIN:
                self._current_value = resp[SECURITIES_ACCOUNT][CURRENT_BALANCES][
                    AVAILABLE_FUNDS
                ]
            elif resp[SECURITIES_ACCOUNT][TYPE] == CASH:
                self._current_value = resp[SECURITIES_ACCOUNT][CURRENT_BALANCES][
                    CASH_AVAILABLE_FOR_TRADEING
                ]
            else:
                self._current_value = 0.00
        else:
            self._available = False

        if (
            self._interval != timedelta(seconds=CLOSED_SCAN_INTERVAL)
            and self.hass.states.get("binary_sensor.market").state == STATE_OFF
        ):
            _LOGGER.debug(
                "Market is closed, setting scan inteval to %s minutes.",
                CLOSED_SCAN_INTERVAL / 60,
            )
            self._interval = timedelta(seconds=CLOSED_SCAN_INTERVAL)
            self._remove_update_interval()
            self._remove_update_interval = async_track_time_interval(
                self.hass, self.async_schedule_update, self._interval
            )
        elif (
            self._interval != timedelta(seconds=OPEN_SCAN_INTERVAL)
            and self.hass.states.get("binary_sensor.market").state == STATE_ON
        ):
            _LOGGER.debug(
                "Market is open, setting scan inteval to %s seconds.",
                OPEN_SCAN_INTERVAL,
            )
            self._interval = timedelta(seconds=OPEN_SCAN_INTERVAL)
            self._remove_update_interval()
            self._remove_update_interval = async_track_time_interval(
                self.hass, self.async_schedule_update, self._interval
            )
