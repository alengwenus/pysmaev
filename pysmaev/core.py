"""SMA EV Charger connection."""

import asyncio
import json
import logging
from typing import Any

from aiohttp import ClientSession, ClientTimeout, client_exceptions

from .const import (
    CONTENT_MEASUREMENT,
    CONTENT_PARAMETERS,
    HEADER_CONTENT_TYPE_JSON,
    HEADER_CONTENT_TYPE_TOKEN,
    REQUEST_TIMEOUT,
    TOKEN_TIMEOUT,
    URL_MEASUREMENTS,
    URL_PARAMETERS,
    URL_TOKEN,
)
from .helpers import get_parameters_channel

_LOGGER = logging.getLogger(__name__)
# _LOGGER.setLevel(logging.DEBUG)


class SmaEvChargerException(Exception):
    """Base exception for pysmaev."""


class SmaEvChargerConnectionException(SmaEvChargerException):
    """Server connection exception."""


class SmaEvChargerAuthenticationException(SmaEvChargerException):
    """Server authentication exception."""


class SmaEvCharger:
    """Class to connect to the SMA EV Charger."""

    def __init__(
        self,
        session: ClientSession,
        url: str,
        username: str,
        password: str,
    ) -> None:
        """Initialize a connection to SMA EV Charger."""
        self.session = session
        self.username = username
        self.password = password
        self.url = url.rstrip("/")
        if not url.startswith("http"):
            self.url = f"http://{self.url}"
        self.client = None
        self.access_token = ""
        self.is_closed = True
        self.token_refresh_handle: asyncio.TimerHandle | None = None

    async def open(self) -> bool:
        """Establish a new session."""
        _LOGGER.debug("Establishing new SmaEvCharger session to %s.", self.url)
        self.is_closed = False
        try:
            await self.request_token(auto_refresh=True)
        except client_exceptions.ClientResponseError as exc:
            raise SmaEvChargerAuthenticationException(
                "Could not authorize. Invalid credentials?"
            ) from exc

        _LOGGER.debug("New SmaEvCharger session established.")
        return True

    async def close(self) -> None:
        """Close session."""
        self.is_closed = True
        self.token_refresh_handle.cancel()
        _LOGGER.debug("SmaEVCharger session is closed.")

    async def __aenter__(self):
        """Enter async context."""
        await self.open()
        return self

    async def __aexit__(self, exception_type: Any, exception: Any, traceback: Any):
        """Exit async context."""
        await self.close()

    async def request_json(
        self, url: str, data: str, headers: str | None = None
    ) -> dict:
        """Request json document."""
        request_url = self.url + url
        if headers is None:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": HEADER_CONTENT_TYPE_JSON,
            }
        _LOGGER.debug("Request to %s: %s", request_url, data)
        try:
            async with self.session.post(
                request_url,
                headers=headers,
                data=data.encode(),
                timeout=ClientTimeout(total=REQUEST_TIMEOUT),
            ) as response:
                response.raise_for_status()
                response_json = await response.json()
                _LOGGER.debug("Response received: %s", response_json)
                return response_json or {}
        except (client_exceptions.ContentTypeError, json.decoder.JSONDecodeError):
            _LOGGER.warning("Request to %s did not return valid json.", request_url)
        except client_exceptions.ServerDisconnectedError as exc:
            raise SmaEvChargerConnectionException(
                f"Server at {self.url} disconnected."
            ) from exc
        except (
            client_exceptions.ClientConnectionError,
            asyncio.exceptions.TimeoutError,
        ) as exc:
            raise SmaEvChargerConnectionException(
                f"Could not connect to SMA EV Charger at {self.url}: {exc}"
            ) from exc

        return {}

    async def request_token(self, auto_refresh: bool = True) -> str:
        """Request new token document."""
        headers = {"Content-Type": HEADER_CONTENT_TYPE_TOKEN}
        data = f"grant_type=password&username={self.username}&password={self.password}"
        result = await self.request_json(URL_TOKEN, data, headers=headers)
        self.access_token = result["access_token"]
        _LOGGER.debug("New access_token: %s", self.access_token)

        if auto_refresh:
            self.token_refresh_handle = asyncio.get_event_loop().call_later(
                TOKEN_TIMEOUT,
                lambda: asyncio.create_task(self.request_token(auto_refresh=True)),
            )

        return result

    async def request_measurements(self) -> str:
        """Request measurements document."""
        return await self.request_json(URL_MEASUREMENTS, CONTENT_MEASUREMENT)

    async def request_parameters(self) -> str:
        """Request parameters document."""
        return await self.request_json(URL_PARAMETERS, CONTENT_PARAMETERS)

    async def device_info(self) -> dict:
        """Read device info."""
        params = await self.request_parameters()
        name_channel = get_parameters_channel(
            params, channel_id="Parameter.Nameplate.Location"
        )
        serial_channel = get_parameters_channel(
            params, channel_id="Parameter.Nameplate.SerNum"
        )
        model_channel = get_parameters_channel(
            params, channel_id="Parameter.Nameplate.ModelStr"
        )
        manu_channel = get_parameters_channel(
            params, channel_id="Parameter.Nameplate.Vendor"
        )
        pkgrev_channel = get_parameters_channel(
            params, channel_id="Parameter.Nameplate.PkgRev"
        )
        device_info = {
            "name": name_channel["value"],
            "serial": serial_channel["value"],
            "model": model_channel["value"],
            "manufacturer": "SMA" if manu_channel["value"] == "461" else "unknown",
            "sw_version": pkgrev_channel["value"],
        }
        return device_info
