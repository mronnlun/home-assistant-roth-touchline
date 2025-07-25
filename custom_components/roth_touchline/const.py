"""Constants for the Roth Touchline integration."""
from datetime import timedelta

DOMAIN = "roth_touchline"

# Configuration
CONF_UPDATE_INTERVAL = "update_interval"
CONF_MAX_ZONES = "max_zones"
DEFAULT_UPDATE_INTERVAL = 30
DEFAULT_MAX_ZONES = 7

# Default values
DEFAULT_PORT = 80
DEFAULT_TIMEOUT = 10
DEFAULT_MAX_ZONES = 7

# Update interval
UPDATE_INTERVAL = timedelta(seconds=DEFAULT_UPDATE_INTERVAL)

# Temperature logging settings
TEMP_LOG_RETENTION_DAYS = 30
TEMP_LOG_INTERVAL = timedelta(minutes=5)  # Log temperature every 5 minutes
MAX_TEMP_READINGS_PER_DAY = 288  # 24 hours * 60 minutes / 5 minute interval

# Device information
MANUFACTURER = "Roth"
MODEL = "Touchline"

# Service names
SERVICE_SET_TEMPERATURE = "set_temperature"
SERVICE_SET_MODE = "set_mode"

# Attributes
ATTR_CURRENT_TEMPERATURE = "current_temperature"
ATTR_TARGET_TEMPERATURE = "target_temperature"
ATTR_HVAC_MODE = "hvac_mode"
ATTR_ROOM_ID = "room_id"
ATTR_ZONE_NAME = "zone_name"

# HVAC modes mapping
ROTH_HVAC_MODES = {
    0: "off",
    1: "heat",
    2: "cool",
    3: "auto",
}

HVAC_MODES_ROTH = {v: k for k, v in ROTH_HVAC_MODES.items()}

# Sensor types - focused on temperature logging
SENSOR_TYPES = {
    "current_temperature": {
        "name": "Current Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
        "icon": "mdi:thermometer",
    },
    "target_temperature": {
        "name": "Target Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
        "icon": "mdi:thermometer-check",
    },
    "daily_avg_temperature": {
        "name": "Daily Average Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
        "icon": "mdi:thermometer-lines",
    },
    "daily_min_temperature": {
        "name": "Daily Minimum Temperature", 
        "unit": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
        "icon": "mdi:thermometer-minus",
    },
    "daily_max_temperature": {
        "name": "Daily Maximum Temperature",
        "unit": "°C", 
        "device_class": "temperature",
        "state_class": "measurement",
        "icon": "mdi:thermometer-plus",
    },
    "humidity": {
        "name": "Humidity",
        "unit": "%",
        "device_class": "humidity",
        "state_class": "measurement",
        "icon": "mdi:water-percent",
    },
    "battery_level": {
        "name": "Battery Level",
        "unit": "%",
        "device_class": "battery",
        "state_class": "measurement",
        "icon": "mdi:battery",
    },
    "last_seen": {
        "name": "Last Seen",
        "device_class": "timestamp",
        "icon": "mdi:clock-outline",
    },
}
