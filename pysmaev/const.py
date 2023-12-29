"""Constants for pysmaev."""
from enum import IntEnum, StrEnum

URL_TOKEN = "/api/v1/token"
URL_MEASUREMENTS = "/api/v1/measurements/live"
URL_PARAMETERS = "/api/v1/parameters/search"
URL_SET_PARAMETERS = "/api/v1/parameters"

CONTENT_MEASUREMENT = '[{"componentId":"IGULD:SELF"}]'
CONTENT_PARAMETERS = '{"queryItems":[{"componentId":"IGULD:SELF"}]}'

HEADER_CONTENT_TYPE_TOKEN = "application/x-www-form-urlencoded;charset=UTF-8"
HEADER_CONTENT_TYPE_JSON = "application/json"

REQUEST_TIMEOUT = 15
TOKEN_TIMEOUT = 3600


class SmaEvChargerMeasurements(IntEnum):
    """EV Charger Measurements."""

    # Status
    OK = 307
    WARNING = 455
    ALARM = 35
    OFF = 303

    # Position of rotary switch
    SMART_CHARGING = 4950
    BOOST_CHARGING = 4718

    # Charging session status
    NOT_CONNECTED = 200111
    SLEEP_MODE = 200112
    ACTIVE_MODE = 200113
    STATION_LOCKED = 5169


class SmaEvChargerParameters(StrEnum):
    """EV Charger Parameters."""

    # General
    YES = "1129"
    NO = "1130"
    NONE = "302"
    EXECUTE = "1146"

    # Operating mode of charge session
    BOOST_CHARGING = "4718"
    OPTIMIZED_CHARGING = "4719"
    SETPOINT_CHARGING = "4720"
    CHARGE_STOP = "4721"

    # Manual charging release
    CHARGING_LOCK = "5171"
    CHARGING_RELEASE = "5172"

    # Light brightness
    LED_LOW = "5191"
    LED_AVERAGE = "5190"
    LED_HIGH = "5173"
