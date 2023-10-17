"""Helpers for pysmaev."""

from datetime import datetime


def get_measurements_channel(
    measurements: list[dict], channel_id: str, component_id: str = "IGULD:SELF"
):
    """Return channel data from measurements."""
    for channel in measurements:
        if (
            channel["componentId"] == component_id
            and channel["channelId"] == channel_id
        ):
            break
    else:
        raise KeyError(
            f"component_id {component_id} with channel_id {channel_id} does not exist"
        )

    return channel["values"]


def get_parameters_channel(
    parameters: list[dict], channel_id: str, component_id: str = "IGULD:SELF"
):
    """Return channel data from parameters."""
    for component in parameters:
        if component["componentId"] == component_id:
            break
    else:
        raise KeyError(f"component_id {component_id} does not exist")

    for channel in component["values"]:
        if channel["channelId"] == channel_id:
            break
    else:
        raise KeyError(f"channel_id {channel_id} does not exist")

    return channel


def evchargerformat(timestamp: datetime):
    """Convert timestamp to EV Charger format."""
    return f"{timestamp.isoformat(timespec='milliseconds').split('+')[0]}Z"
