"""Constants for pysmaev."""

URL_TOKEN = "/api/v1/token"
URL_MEASUREMENTS = "/api/v1/measurements/live"

PAYLOAD_MEASUREMENT = '[{"componentId":"IGULD:SELF"}]'

HEADER_AUTHORIZATION = "Bearer {token}"
HEADER_CONTENT_TYPE_TOKEN = "application/x-www-form-urlencoded"
HEADER_CONTENT_TYPE_JSON = "application/json"

TOKEN_TIMEOUT = 3000
