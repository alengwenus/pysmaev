"""Helpers for pysmaev."""

from datetime import datetime
from typing import Any, cast

from .exceptions import SmaEvChargerChannelError

type JsonValueType = (
    dict[str, JsonValueType] | list[JsonValueType] | str | int | float | bool | None
)
"""Any data that can be returned by the standard JSON deserializing process."""
type JsonArrayType = list[JsonValueType]
"""List that can be returned by the standard JSON deserializing process."""
type JsonObjectType = dict[str, JsonValueType]
"""Dictionary that can be returned by the standard JSON deserializing process."""

type PossibleValuesType = list[str]

type MeasurementChannelType = list[dict[str, str | int | float | bool]]

type ParameterChannelType = dict[str, str | int | float | bool | PossibleValuesType]


def expect_type(expected_type: type, value: Any) -> Any:
    """Check if value is of expected type."""
    if not isinstance(value, expected_type):
        raise TypeError(f"Expected {expected_type}, got {type(value)}")
    return value


def get_measurements_channel(
    measurements: JsonArrayType,
    channel_id: str,
    component_id: str = "IGULD:SELF",
) -> MeasurementChannelType:
    """Return channel data from measurements."""
    for channel in measurements:
        if not isinstance(channel, dict):
            raise TypeError("measurements must be a list of dictionaries")
        if (
            channel["componentId"] == component_id
            and channel["channelId"] == channel_id
        ):
            return cast(MeasurementChannelType, channel["values"])

    raise KeyError(
        f"component_id {component_id} with channel_id {channel_id} does not exist"
    )


def get_parameters_channel(
    parameters: JsonArrayType,
    channel_id: str,
    component_id: str = "IGULD:SELF",
) -> ParameterChannelType:
    """Return channel data from parameters."""
    for component in parameters:
        if expect_type(dict, component)["componentId"] == component_id:
            break
    else:
        raise SmaEvChargerChannelError(f"component_id {component_id} does not exist")

    for channel in expect_type(dict, component)["values"]:
        if channel["channelId"] == channel_id:
            break
    else:
        raise SmaEvChargerChannelError(f"channel_id {channel_id} does not exist")

    return cast(ParameterChannelType, channel)


def evchargerformat(timestamp: datetime) -> str:
    """Convert timestamp to EV Charger format."""
    return f"{timestamp.isoformat(timespec='milliseconds').split('+')[0]}Z"
