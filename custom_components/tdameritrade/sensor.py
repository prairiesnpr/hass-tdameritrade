"""Support for the TDAmeritrade sensors."""
import logging

from homeassistant.helpers.entity import Entity

from .const import CONF_ACCOUNTS, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config, add_entities, discovery_info=None):
    """Set up the TDAmeritrade binary sensor platform."""
    sensors = []
    for account_id in config.data[CONF_ACCOUNTS]:
        sensors.append(
            AccountValueSensor(hass.data[DOMAIN][config.entry_id], account_id)
        )
    add_entities(sensors)
    return True


class AccountValueSensor(Entity):
    """Representation of Available Funds sensors."""

    def __init__(self, client, account_id):
        """Initialize of a account sensor."""
        self._name = "Available Funds"
        self._client = client["td_api"]
        self.account_id = account_id
        self.current_value = None
        self.units = None
        self.last_changed_time = None
        self._attributes = {}

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.current_value

    @property
    def name(self):
        """Return the name of the binary sensor."""
        return f"{self._name} #--{self.account_id[-4:]}"

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
        """Return the class of this binary sensor."""
        return "mdi:cash"

    async def async_update(self):
        """Update the state from the sensor."""
        _LOGGER.debug("Updating sensor: %s", self._name)

        resp = await self._client.async_get_account(self.account_id)

        self._attributes = resp["securitiesAccount"]
        if resp["securitiesAccount"]["type"] == "MARGIN":
            self.current_value = resp["securitiesAccount"]["currentBalances"][
                "availableFunds"
            ]
        elif resp["securitiesAccount"]["type"] == "CASH":
            self.current_value = resp["securitiesAccount"]["currentBalances"][
                "cashAvailableForTrading"
            ]
        else:
            self.current_value = 0.00
