"""API for TDAmeritrade bound to Home Assistant OAuth."""
# from asyncio import run_coroutine_threadsafe

from aiohttp import ClientSession
import td_ameritrade_api as td

# from homeassistant import config_entries, core
from homeassistant.helpers import config_entry_oauth2_flow


class AsyncConfigEntryAuth(td.AbstractAuth):
    """Provide TDAmeritrade authentication tied to an OAuth2 based config entry."""

    def __init__(
        self,
        websession: ClientSession,
        oauth_session: config_entry_oauth2_flow.OAuth2Session,
        host,
    ):
        """Initialize TDAmeritrade auth."""
        super().__init__(websession, host)
        self._oauth_session = oauth_session

    async def async_get_access_token(self):
        """Return a valid access token."""
        if not self._oauth_session.is_valid:
            await self._oauth_session.async_ensure_token_valid()

        return self._oauth_session.token
