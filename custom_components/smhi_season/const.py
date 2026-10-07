"""Constants for SMHI Season integration."""

DOMAIN = "smhi_season"
CONF_TEMP_SENSOR = "temperature_sensor"

SEASON_VINTER = "vinter"
SEASON_VAR = "var"
SEASON_SOMMAR = "sommar"
SEASON_HOST = "host"

DEFAULT_NAME = "Meteorological Season"

# How many days of recorder history to replay when catching up / backfilling.
# Long enough to traverse a full winter->spring->summer cycle so the current
# season (and autumn/winter transitions) is computed correctly from data.
REPLAY_LOOKBACK_DAYS = 365
