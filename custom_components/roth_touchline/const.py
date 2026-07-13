"""Constants for the Roth Touchline integration."""

DOMAIN = "roth_touchline"

# Configuration
CONF_UPDATE_INTERVAL = "update_interval"
CONF_MAX_ZONES = "max_zones"
DEFAULT_UPDATE_INTERVAL = 300  # 5 minutes
DEFAULT_MAX_ZONES = 10

# Default values
DEFAULT_PORT = 80
DEFAULT_TIMEOUT = 10

# Device information
MANUFACTURER = "Roth"
MODEL = "Touchline"

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
    "last_seen": {
        "name": "Last Seen",
        "device_class": "timestamp",
        "icon": "mdi:clock-outline",
    },
}
