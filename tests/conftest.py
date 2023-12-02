"""Core testing functionality."""

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def response_measurements():
    """Load measurements json."""
    filepath = Path(__file__).parent / "fixtures/measurements.json"
    with filepath.open(encoding="utf-8") as fid:
        response = fid.read()
    return response


@pytest.fixture(scope="session")
def response_parameters():
    """Load parameters json."""
    filepath = Path(__file__).parent / "fixtures/parameters.json"
    with filepath.open(encoding="utf-8") as fid:
        response = fid.read()
    return response
