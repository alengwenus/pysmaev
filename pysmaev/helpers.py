"""Helpers for pysmaev."""


def get_channel(
    parameters: list[dict], channel_id: str, component_id: str = "IGULD:SELF"
):
    """Return channel data."""
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
