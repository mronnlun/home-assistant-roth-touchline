# Installation and Setup Guide

## Prerequisites

1. **Home Assistant** version 2023.1.0 or newer
2. **Roth Touchline** classic series system with network connectivity
3. Network access between Home Assistant and your Roth Touchline system

## Step 1: Installation

### Option A: HACS Installation (Recommended)

1. Ensure [HACS](https://hacs.xyz/) is installed in your Home Assistant
2. Open HACS → Integrations
3. Click the three dots menu → Custom repositories
4. Add repository URL: `https://github.com/mronnlun/home-assistant-roth-touchline`
5. Category: Integration
6. Click "Add"
7. Search for "Roth Touchline Temperature Logger"
8. Click "Download"
9. Restart Home Assistant

### Option B: Manual Installation

1. Download the latest release from the [releases page](https://github.com/mronnlun/home-assistant-roth-touchline/releases)
2. Extract the ZIP file
3. Copy the `custom_components/roth_touchline` folder to your Home Assistant's `custom_components` directory
4. Restart Home Assistant

## Step 2: Configuration

### Find Your Roth Touchline System

1. Check your router's admin panel for connected devices
2. Look for a device named similar to "Roth-Touchline" or check the device's IP address
3. Note down the IP address and port (usually 80)

### Add the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"**
3. Search for **"Roth Touchline Temperature Logger"**
4. Enter your system details:
   - **Host/IP Address**: Your Roth Touchline system's IP address
   - **Port**: Usually 80 (default)
5. Click **"Submit"**

## Step 3: Verify Installation

### Check Entities

After successful setup, you should see entities like:

- `climate.roth_touchline_[room_name]`
- `sensor.roth_touchline_[room_name]_current_temperature`
- `sensor.roth_touchline_[room_name]_target_temperature`
- `sensor.roth_touchline_[room_name]_daily_avg_temperature`
- `binary_sensor.roth_touchline_[room_name]_heating`

### Test Services

1. Go to **Developer Tools** → **Services**
2. Try the service `roth_touchline.get_temperature_history`
3. Set parameters:
   ```yaml
   zone_id: "your_zone_id"  # Replace with actual zone ID
   hours: 1
   ```
4. Click **"Call Service"**

## Step 4: Configure Temperature Logging

### Enable Long-term Statistics

Add to your `configuration.yaml`:

```yaml
recorder:
  purge_keep_days: 90
  include:
    entity_globs:
      - sensor.roth_touchline_*_temperature
      - sensor.roth_touchline_*_humidity

history:
  include:
    entity_globs:
      - sensor.roth_touchline_*_temperature
      - climate.roth_touchline_*
```

### Set Up Automation for Data Export

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

## Step 5: Create Dashboard

### Basic Temperature Dashboard

1. Go to your Home Assistant dashboard
2. Click **"Edit Dashboard"**
3. Add a new card with this YAML:

```yaml
type: entities
title: Room Temperatures
entities:
  - sensor.roth_touchline_living_room_current_temperature
  - sensor.roth_touchline_bedroom_current_temperature
  - sensor.roth_touchline_kitchen_current_temperature
show_header_toggle: false
```

### Historical Graph

```yaml
type: history-graph
entities:
  - sensor.roth_touchline_living_room_current_temperature
  - sensor.roth_touchline_bedroom_current_temperature
hours_to_show: 24
refresh_interval: 300
```

## Troubleshooting

### Connection Issues

1. **Verify IP and Port**: Ensure the IP address and port are correct
2. **Network Connectivity**: Test if Home Assistant can reach the Roth Touchline system:
   ```bash
   ping YOUR_ROTH_IP
   ```
3. **Firewall**: Check if any firewalls are blocking the connection

### No Entities Appearing

1. Check **Settings** → **Devices & Services** → **Roth Touchline**
2. Look for any error messages
3. Check Home Assistant logs: **Settings** → **System** → **Logs**
4. Enable debug logging:
   ```yaml
   logger:
     logs:
       custom_components.roth_touchline: debug
   ```

### Service Errors

1. Verify zone IDs are correct:
   - Go to **Developer Tools** → **States**
   - Find your climate entities and note the zone IDs
2. Check service parameters match the expected format

### Temperature Data Not Updating

1. Check the update interval in integration settings
2. Verify the Roth Touchline system is responding to API calls
3. Check for network connectivity issues

## Advanced Configuration

### Custom Update Intervals

You can adjust the polling frequency by reloading the integration and changing the settings.

### Data Export Scheduling

Set up multiple export schedules for different time periods:

```yaml
automation:
  - alias: "Hourly Temperature Export"
    trigger:
      platform: time_pattern
      minutes: 0
    action:
      - service: roth_touchline.export_temperature_data
        data:
          days: 1
          file_path: "/config/exports/hourly_temp_{{ now().strftime('%Y%m%d_%H') }}.csv"
```

### Integration with Other Systems

The exported CSV files can be used with:
- Excel/Google Sheets for analysis
- Grafana for advanced visualization
- InfluxDB for time-series database storage
- Custom Python scripts for data processing

## Support

If you encounter issues:

1. Check the [Issues page](https://github.com/mronnlun/home-assistant-roth-touchline/issues)
2. Review Home Assistant logs for error messages
3. Create a new issue with:
   - Home Assistant version
   - Integration version
   - Error logs
   - Description of the problem
