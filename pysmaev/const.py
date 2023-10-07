"""Constants for pysmaev."""

URL_TOKEN = "/api/v1/token"
URL_MEASUREMENTS = "/api/v1/measurements/live"
URL_PARAMETERS = "/api/v1/parameters/search"

CONTENT_MEASUREMENT = '[{"componentId":"IGULD:SELF"}]'
CONTENT_PARAMETERS = '{"queryItems":[{"componentId":"IGULD:SELF"}]}'

HEADER_CONTENT_TYPE_TOKEN = "application/x-www-form-urlencoded"
HEADER_CONTENT_TYPE_JSON = "application/json"

REQUEST_TIMEOUT = 15
TOKEN_TIMEOUT = 3000
