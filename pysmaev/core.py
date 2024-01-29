"""SMA EV Charger connection."""

import asyncio
from datetime import UTC, datetime
import json
import logging
from typing import Any
from urllib.parse import quote_plus

from aiohttp import ClientSession, ClientTimeout, client_exceptions, hdrs

from .const import (
    CONTENT_MEASUREMENT,
    CONTENT_PARAMETERS,
    HEADER_CONTENT_TYPE_JSON,
    HEADER_CONTENT_TYPE_TOKEN,
    REQUEST_TIMEOUT,
    TOKEN_TIMEOUT,
    URL_MEASUREMENTS,
    URL_PARAMETERS,
    URL_SET_PARAMETERS,
    URL_TOKEN,
)
from .exceptions import SmaEvChargerAuthenticationError, SmaEvChargerConnectionError
from .helpers import evchargerformat, get_parameters_channel

_LOGGER = logging.getLogger(__name__)
# _LOGGER.setLevel(logging.DEBUG)


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
        self.refresh_token = ""
        self.is_closed = True
        self.token_refresh_handle: asyncio.TimerHandle | None = None

    async def open(self) -> bool:
        """Establish a new session."""
        _LOGGER.debug("Establishing new SmaEvCharger session to %s.", self.url)
        try:
            await self.request_token(auto_refresh=True, force_credentials=True)
        except client_exceptions.ClientResponseError as exc:
            raise SmaEvChargerAuthenticationError(
                "Could not authorize. Invalid credentials?"
            ) from exc

        self.is_closed = False
        _LOGGER.debug("New SmaEvCharger session established.")
        return True

    async def close(self) -> None:
        """Close session."""
        self.is_closed = True
        if self.token_refresh_handle is not None:
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
        self, method: str, url: str, data: str, headers: str | None = None
    ) -> dict:
        """Request json document."""
        request_url = self.url + url
        data_encoded = data.encode()
        if headers is None:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": HEADER_CONTENT_TYPE_JSON,
                "Content-Length": f"{len(data_encoded)}",
            }
        _LOGGER.debug("Request %s to %s: %s", method, request_url, data)
        try:
            async with self.session.request(
                method,
                request_url,
                headers=headers,
                data=data_encoded,
                timeout=ClientTimeout(total=REQUEST_TIMEOUT),
            ) as response:
                response.raise_for_status()
                response_json = await response.json()
                _LOGGER.debug("Response received: %s", response_json)
                return response_json or {}
        except (client_exceptions.ContentTypeError, json.decoder.JSONDecodeError):
            _LOGGER.warning("Request to %s did not return valid json.", request_url)
        except client_exceptions.ServerDisconnectedError as exc:
            await self.close()
            raise SmaEvChargerConnectionError(
                f"Server at {self.url} disconnected."
            ) from exc
        except (
            client_exceptions.ClientConnectionError,
            asyncio.exceptions.TimeoutError,
        ) as exc:
            await self.close()
            raise SmaEvChargerConnectionError(
                f"Could not connect to SMA EV Charger at {self.url}"
            ) from exc
        return {}

    async def request_token(
        self, auto_refresh: bool = True, force_credentials: bool = True
    ) -> str:
        """Request new token document."""
        if self.token_refresh_handle is not None:
            self.token_refresh_handle.cancel()

        headers = {"Content-Type": HEADER_CONTENT_TYPE_TOKEN}
        if self.refresh_token and not force_credentials:
            _LOGGER.debug("Request token using refresh token.")
            data = f"grant_type=refresh_token&refresh_token={self.refresh_token}"
        else:
            _LOGGER.debug("Request token using credentials.")
            data = f"grant_type=password&username={quote_plus(self.username)}&password={quote_plus(self.password)}"
        result = await self.request_json(
            hdrs.METH_POST, URL_TOKEN, data, headers=headers
        )
        if not result:
            _LOGGER.debug("No token received.")
            self.refresh_token = ""
            return result

        self.access_token = result["access_token"]
        self.refresh_token = result["refresh_token"]
        expires_in = result.get("expires_in", TOKEN_TIMEOUT)
        _LOGGER.debug("New access token: %s", self.access_token)
        _LOGGER.debug("New refresh token: %s", self.refresh_token)

        if auto_refresh:
            self.token_refresh_handle = asyncio.get_event_loop().call_later(
                int(expires_in * 0.9),
                lambda: asyncio.create_task(self.request_token(auto_refresh=True)),
            )

        return result

    async def request_measurements(self) -> dict:
        """Request measurements."""
        return await self.request_json(
            hdrs.METH_POST, URL_MEASUREMENTS, CONTENT_MEASUREMENT
        )

    async def request_parameters(self) -> dict:
        """Request parameters."""
        return await self.request_json(
            hdrs.METH_POST, URL_PARAMETERS, CONTENT_PARAMETERS
        )

    async def get_measurement_channels(self) -> list[str]:
        """Get measurement channel names."""
        return [
            measurement["channelId"]
            for measurement in await self.request_measurements()
        ]

    async def get_parameter_channels(self) -> list[str]:
        """Get parameter channel names."""
        return [
            parameter["channelId"]
            for component in await self.request_parameters()
            for parameter in component["values"]
        ]

    async def set_parameter(
        self, value: str, channel_id: str, component_id: str = "IGULD:SELF"
    ) -> dict:
        """Set parameters."""
        request_url = URL_SET_PARAMETERS + "/" + component_id
        data = {
            "values": [
                {
                    "channelId": channel_id,
                    "timestamp": evchargerformat(datetime.now(tz=UTC)),
                    "value": value,
                }
            ]
        }
        data_json = json.dumps(data, separators=(",", ":"))
        return await self.request_json(hdrs.METH_PUT, request_url, data_json)

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
