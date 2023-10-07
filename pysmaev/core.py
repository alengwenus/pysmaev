"""SMA EV Charger connection."""

import asyncio
import logging

import httpx

from .const import (
    CONTENT_MEASUREMENT,
    CONTENT_PARAMETERS,
    HEADER_CONTENT_TYPE_JSON,
    HEADER_CONTENT_TYPE_TOKEN,
    TOKEN_TIMEOUT,
    URL_MEASUREMENTS,
    URL_PARAMETERS,
    URL_TOKEN,
)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


class SmaEvChargerSession:
    """Class to connect to the SMA EV Charger."""

    def __init__(
        self, url: str, username: str, password: str, ssl_verify=False
    ) -> None:
        """Initialize a connection to SMA EV Charger."""
        self.username = username
        self.password = password
        self.url = url.rstrip("/")
        if not url.startswith("http"):
            self.url = f"https://{self.url}"
        self.ssl_verify = ssl_verify
        self.client = None
        self.access_token = ""
        self.access_token_received = asyncio.Event()
        self.is_closed = True
        self.token_refresh_task: asyncio.Task | None = None

    async def open(self) -> bool:
        """Establish a new session."""
        # TODO: Error Handling
        _LOGGER.debug("Establishing new SmaEvCharger session to %s.", self.url)
        self.client = httpx.AsyncClient(verify=self.ssl_verify)
        self.is_closed = False
        self.token_refresh_task = asyncio.create_task(self.token_refresh())
        await self.access_token_received.wait()
        _LOGGER.debug("New SmaEvCharger session established.")
        return True

    async def close(self) -> None:
        """Close session."""
        self.is_closed = True
        self.token_refresh_task.cancel()
        await self.token_refresh_task
        self.client = None
        _LOGGER.debug("SmaEVCharger session is closed.")

    async def token_refresh(self) -> None:
        """Refresh token loop."""
        while not self.is_closed:
            try:
                self.access_token_received.clear()
                result = await self.request_token()
                self.access_token = result["access_token"]
                expires_in = int(result["expires_in"])
                _LOGGER.debug("New access_token: %s", self.access_token)
                self.access_token_received.set()
                await asyncio.sleep(min(expires_in, TOKEN_TIMEOUT))
            except asyncio.CancelledError:
                self.access_token_received.clear()
                self.access_token = ""
                break

    async def request_token(self) -> str:
        """Request new token."""
        url = f"{self.url}{URL_TOKEN}"
        headers = {"Content-Type": HEADER_CONTENT_TYPE_TOKEN}
        content = f"grant_type=password&username={self.username}&password={self.password}".encode()
        response = await self.client.post(url, headers=headers, content=content)
        response.raise_for_status()
        result = response.json()
        return result

    async def request_measurements(self) -> str:
        """Request measurements document."""
        url = f"{self.url}{URL_MEASUREMENTS}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": HEADER_CONTENT_TYPE_JSON,
        }
        content = CONTENT_MEASUREMENT.encode()
        response = await self.client.post(url, headers=headers, content=content)
        response.raise_for_status()
        result = response.json()
        return result

    async def request_parameters(self) -> str:
        """Request parameters document."""
        url = f"{self.url}{URL_PARAMETERS}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": HEADER_CONTENT_TYPE_JSON,
        }
        content = CONTENT_PARAMETERS.encode()
        response = await self.client.post(url, headers=headers, content=content)
        response.raise_for_status()
        result = response.json()
        return result
