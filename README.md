# Home Assistant Roth Touchline Temperature Logger

A read-only custom integration for Home Assistant that monitors room temperatures
and configured setpoints from Roth Touchline classic series heating systems.

## Features

- **Temperature Monitoring**: Track current and target temperatures for each room
- **Read-only Operation**: The integration does not change controller settings
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
   - **Maximum number of zones**: Number of zones to monitor (default: 10, range: 1-20)
   - **Update interval**: How often to fetch temperature data in seconds (default: 300 = 5 minutes, range: 30-3600)
5. Click "Submit"

The integration will automatically detect which zones are available on your system.

### Recommended Update Intervals

- **30-60 seconds**: For active monitoring and quick response to temperature changes
- **300 seconds (5 minutes)**: Default - good balance between responsiveness and system load
- **600-1800 seconds (10-30 minutes)**: For basic temperature logging with minimal network traffic
- **3600 seconds (1 hour)**: For long-term temperature monitoring only

## Entities

### Sensors
- `sensor.roth_touchline_[zone_name]_current_temperature` - Current room temperature (from RaumTemp)
- `sensor.roth_touchline_[zone_name]_target_temperature` - Target temperature setting (from SollTemp)
- `sensor.roth_touchline_[zone_name]_last_seen` - Last communication timestamp

Home Assistant's recorder can be used to retain and graph these sensor values.

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

## Example Automation

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

### Versioning and releases

This project follows [Semantic Versioning](https://semver.org/) and uses
[Conventional Commits](https://www.conventionalcommits.org/) for pull request
titles:

- `fix:` and `perf:` publish a patch release.
- `feat:` publishes a minor release.
- A `!` after the type or a `BREAKING CHANGE:` footer publishes a major release.

Release Please maintains a release pull request containing the next version and
changelog. Merging that pull request creates the GitHub release and uploads the
`roth_touchline.zip` archive used by HACS.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues, please check the [Issues](https://github.com/mronnlun/home-assistant-roth-touchline/issues) page or create a new issue with detailed information about your problem.
