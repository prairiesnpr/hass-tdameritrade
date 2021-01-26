"""Support for the TDAmeritrade sensors."""
import logging

from homeassistant.helpers.entity import Entity
from datetime import timedelta
from aiohttp.client_exceptions import ClientConnectorError, ClientResponseError

from .const import CONF_ACCOUNTS, DOMAIN

SCAN_INTERVAL = timedelta(seconds=10)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the TDAmeritrade sensor platform."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    if config_entry.options:
        config.update(config_entry.options)
    if config_entry.options:
        accounts = config_entry.options[CONF_ACCOUNTS]
    else:
        accounts = config_entry.data[CONF_ACCOUNTS]
    sensors = []
    for account_id in accounts:
        sensors.append(AccountValueSensor(config["client"], account_id))
    sensors = [entity for entity in sensors if not hass.states.get(
        f"sensor.available_funds_{entity.account_id[-4:]}"
    )]
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
        return f"{DOMAIN}.{self._name}_{self.account_id[-4:]}"

    @property
    def available(self):
        """Return the availability of the sensor."""
        return self._available

    @property
    def unit_of_measurement(self):
        """Return the unit_of_measurement of the device."""
        return "Dollars"

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        return self._attributes

    @property
    def icon(self):
        """Return the class of this sensor."""
        return "mdi:cash"

    async def async_update(self):
        """Update the state from the sensor."""
        _LOGGER.debug("Updating sensor: %s, id: %s", self._name, self.entity_id)
        resp = None
        try:
            resp = await self._client.async_get_account(self._account_id)
        except (ClientConnectorError, ClientResponseError) as error:
            _LOGGER.warning("Client Exception: %s", error)
        if resp:
            self._available = True
            self._attributes = resp["securitiesAccount"]
            if resp["securitiesAccount"]["type"] == "MARGIN":
                self._current_value = resp["securitiesAccount"]["currentBalances"][
                    "availableFunds"
                ]
            elif resp["securitiesAccount"]["type"] == "CASH":
                self._current_value = resp["securitiesAccount"]["currentBalances"][
                    "cashAvailableForTrading"
                ]
            else:
                self._current_value = 0.00
        else:
            self._available = False
