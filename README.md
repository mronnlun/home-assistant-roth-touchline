# Home Assistant Roth Touchline Temperature Logger

A custom integration for Home Assistant to monitor and log room temperatures from Roth Touchline classic series heating systems.

## Features

- **Comprehensive Temperature Monitoring**: Track current, target, daily average, minimum, and maximum temperatures for each room
- **Climate Control**: Full thermostat functionality with temperature setting and HVAC mode control
- **Historical Data**: Access temperature history and daily statistics
- **Data Export**: Export temperature data to CSV files for analysis
- **Additional Sensors**: Connectivity status and system monitoring
- **Real-time Updates**: Automatic polling and logging of temperature data
- **Easy Configuration**: Simple setup through Home Assistant's UI

## Supported Devices

This integration supports the classic Roth Touchline series thermostats and heating controllers for multi-room temperature monitoring and logging.

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Navigate to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/mronnlun/home-assistant-roth-touchline`
6. Select "Integration" as the category
7. Click "Add"
8. Search for "Roth Touchline" and install

### Manual Installation

1. Download the latest release from this repository
2. Extract the `custom_components/roth_touchline` folder to your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Roth Touchline"
4. Enter your configuration:
   - **Host/IP Address**: Your Roth Touchline system's IP address
   - **Port**: Connection port (default: 80)
   - **Maximum number of zones**: Number of zones to monitor (default: 7, range: 1-20)
5. Click "Submit"

The integration will automatically detect which zones are available on your system.

## Entities

### Climate
- `climate.roth_touchline_[zone_name]` - Main thermostat control

### Sensors
- `sensor.roth_touchline_[zone_name]_current_temperature` - Current room temperature (from RaumTemp)
- `sensor.roth_touchline_[zone_name]_target_temperature` - Target temperature setting (from SollTemp)
- `sensor.roth_touchline_[zone_name]_last_seen` - Last communication timestamp

**Note**: Additional sensors like daily statistics may not be available via the XML API and depend on your specific Roth Touchline model and firmware.

### Climate Entities
- `climate.roth_touchline_[zone_name]` - Climate control (primarily read-only monitoring)

**Note**: Temperature and HVAC mode setting capabilities depend on your Roth Touchline system's XML API support.

### Binary Sensors
- `binary_sensor.roth_touchline_[zone_name]_heating` - Heating status
- `binary_sensor.roth_touchline_[zone_name]_cooling` - Cooling status
- `binary_sensor.roth_touchline_[zone_name]_online` - Connectivity status

## Services

### `roth_touchline.set_temperature`
Set the target temperature for a specific zone.

**Note**: This service may not work depending on your Roth Touchline system's XML API capabilities.

**Parameters:**
- `zone_id` (required): The zone identifier (e.g., "G0", "G1")
- `temperature` (required): Target temperature in Celsius (5-35°C)

### `roth_touchline.set_hvac_mode`
Set the HVAC mode for a specific zone.

**Note**: This service may not work depending on your Roth Touchline system's XML API capabilities.

**Parameters:**
- `zone_id` (required): The zone identifier (e.g., "G0", "G1")
- `hvac_mode` (required): HVAC mode (off, heat, cool, auto)

### `roth_touchline.get_temperature_history`
Get temperature history for a specific zone.

**Note**: This service may not be available as the XML API typically provides only current values.

**Parameters:**
- `zone_id` (required): The zone identifier
- `hours` (optional): Number of hours of history to retrieve (default: 24, max: 168)

### `roth_touchline.export_temperature_data`
Export temperature data for all zones to a CSV file.

**Note**: This service may have limited functionality due to XML API constraints.

**Parameters:**
- `days` (optional): Number of days of data to export (default: 7, max: 30)
- `file_path` (optional): Custom file path for the export (default: auto-generated)

## API Communication

This integration communicates with the Roth Touchline system using XML-based HTTP POST requests to the endpoint:

```
http://[TOUCHLINE_IP]/cgi-bin/ILRReadValues.cgi
```

### Temperature Value Processing

The Roth Touchline system returns temperature values in hundredths of degrees Celsius (e.g., 2100 for 21.0°C). The integration automatically converts these values by dividing by 100 to display the correct temperature in degrees Celsius.

### XML Request Format

The integration sends XML POST requests in this format:

```xml
<body>
  <item_list>
    <i>
      <n>G0.RaumTemp</n>
    </i>
    <i>
      <n>G0.SollTemp</n>
    </i>
    <i>
      <n>G0.name</n>
    </i>
    <i>
      <n>R0.SystemStatus</n>
    </i>
    <!-- Additional zones G1-G6 -->
  </item_list>
</body>
```

### Required Headers

The integration uses these HTTP headers as required by the Roth Touchline system:

```
Accept-Language: *
Content-Type: text/xml
User-Agent: SpiderControl/1.0 (iniNet-Solutions GmbH)
Cache-Control: no-cache
Pragma: no-cache
Accept: text/html, image/gif, image/jpeg, *; q = .2, */*; q=.2
```

### Data Points

For each zone (G0-G6), the integration requests:
- **RaumTemp**: Current room temperature
- **SollTemp**: Target/setpoint temperature
- **name**: Room name/identifier

Additional system information:
- **R0.SystemStatus**: Overall system status

## Example Automations

### Morning Heating
```yaml
automation:
  - alias: "Morning Heating"
    trigger:
      platform: time
      at: "06:00:00"
    action:
      - service: roth_touchline.set_temperature
        data:
          zone_id: "living_room"
          temperature: 21
      - service: roth_touchline.set_hvac_mode
        data:
          zone_id: "living_room"
          hvac_mode: "heat"
```

### Daily Temperature Data Export
```yaml
automation:
  - alias: "Daily Temperature Export"
    trigger:
      platform: time
      at: "23:55:00"
    action:
      - service: roth_touchline.export_temperature_data
        data:
          days: 1
```

### Temperature Alert
```yaml
automation:
  - alias: "Low Temperature Alert"
    trigger:
      platform: numeric_state
      entity_id: sensor.roth_touchline_bedroom_current_temperature
      below: 18
    action:
      - service: notify.mobile_app
        data:
          message: "Bedroom temperature is too low: {{ states('sensor.roth_touchline_bedroom_current_temperature') }}°C"
```

### Weekly Temperature History Report
```yaml
automation:
  - alias: "Weekly Temperature Report"
    trigger:
      platform: time
      at: "08:00:00"
    condition:
      condition: time
      weekday: 
        - sun
    action:
      - service: roth_touchline.get_temperature_history
        data:
          zone_id: "living_room"
          hours: 168  # 7 days
```

## Troubleshooting

### Connection Issues
- Verify the IP address and port of your Roth Touchline system
- Ensure Home Assistant can reach the device on your network
- Check that the Roth Touchline system is powered on and connected

### Missing Entities
- Check the Home Assistant logs for any error messages
- Verify that your Roth Touchline system supports the expected API endpoints
- Restart the integration from Settings → Devices & Services

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues, please check the [Issues](https://github.com/mronnlun/home-assistant-roth-touchline/issues) page or create a new issue with detailed information about your problem.
