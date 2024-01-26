"""SMA EV Charger exceptions."""


class SmaEvChargerException(Exception):
    """Base exception for pysmaev."""


class SmaEvChargerConnectionError(SmaEvChargerException):
    """Server connection exception."""


class SmaEvChargerAuthenticationError(SmaEvChargerException):
    """Server authentication exception."""


class SmaEvChargerChannelError(SmaEvChargerException):
    """Channel error."""
