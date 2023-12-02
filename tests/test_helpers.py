"""Tests for helpers."""

from datetime import datetime
import json

import pytest

from pysmaev import helpers


def test_evchargerformat():
    """Test EV Charger time formatting."""
    timestamp = datetime(2023, 12, 3, 4, 56, 7, 123456)
    formatted_timestamp = helpers.evchargerformat(timestamp)
    assert formatted_timestamp == "2023-12-03T04:56:07.123Z"


@pytest.mark.parametrize(
    "channel_id, value",
    [
        ("Measurement.ChaSess.WhIn", 420),
        ("Measurement.Chrg.ModSw", 4950),
        ("Measurement.Operation.EVeh.Health", 307),
    ],
)
def test_get_measurements_channel(response_measurements, channel_id, value):
    """Test get_measurements_channel."""
    measurements = json.loads(response_measurements)
    component_id = "IGULD:SELF"
    values = helpers.get_measurements_channel(measurements, channel_id, component_id)
    assert values[0]["time"] == "2023-12-03T04:56:07.123Z"
    assert values[0]["value"] == value


@pytest.mark.parametrize(
    "component_id, channel_id, message",
    [
        (
            "DUMMY:SELF",
            "Measurement.Chrg.ModSw",
            "component_id DUMMY:SELF with channel_id Measurement.Chrg.ModSw does not exist",
        ),
        (
            "IGULD:SELF",
            "Non.Existing.Channel",
            "component_id IGULD:SELF with channel_id Non.Existing.Channel does not exist",
        ),
    ],
)
def test_get_measurements_channel_keyerror(
    response_measurements, component_id, channel_id, message
):
    """Test get_measurements_channel KeyError."""
    measurements = json.loads(response_measurements)
    with pytest.raises(KeyError) as exc_info:
        helpers.get_measurements_channel(measurements, channel_id, component_id)
    assert exc_info.match(message)


@pytest.mark.parametrize(
    "channel_id, value",
    [
        ("Parameter.Chrg.ActChaMod", "4719"),
        ("Parameter.Chrg.Plan.DurTmm", "0"),
        ("Parameter.Chrg.Plan.StopTm", "1701579367"),
    ],
)
def test_get_parameters_channel(response_parameters, channel_id, value):
    """Test get_parameters_channel."""
    parameters = json.loads(response_parameters)
    component_id = "IGULD:SELF"
    channel = helpers.get_parameters_channel(parameters, channel_id, component_id)
    assert channel["channelId"] == channel_id
    assert channel["timestamp"] == "2023-12-03T04:56:07.123Z"
    assert channel["editable"] is True
    assert channel["state"] == "Confirmed"
    assert channel["value"] == value


@pytest.mark.parametrize(
    "component_id, channel_id, message",
    [
        (
            "DUMMY:SELF",
            "Parameter.Chrg.ActChaMod",
            "component_id DUMMY:SELF does not exist",
        ),
        (
            "IGULD:SELF",
            "Non.Existing.Channel",
            "channel_id Non.Existing.Channel does not exist",
        ),
    ],
)
def test_get_parameters_channel_keyerror(
    response_parameters, component_id, channel_id, message
):
    """Test get_parameters_channel KeyError."""
    measurements = json.loads(response_parameters)
    with pytest.raises(KeyError) as exc_info:
        helpers.get_parameters_channel(measurements, channel_id, component_id)
    assert exc_info.match(message)
