"""Helper functions for pysmaev."""

from .const import HEADER_AUTHORIZATION


def authorization_bearer(token: str) -> str:
    """Generate authorization header."""
    return HEADER_AUTHORIZATION.format(token)
