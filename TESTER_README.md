# Roth Touchline API Tester

A standalone testing script to verify communication with your Roth Touchline device before installing the Home Assistant integration.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r tester-requirements.txt
```

Or manually:
```bash
pip install aiohttp async-timeout
```

### 2. Run the Tester

```bash
python tester.py <your_device_ip> [port] [max_zones]
```

Examples:
```bash
python tester.py 192.168.0.104
python tester.py 192.168.1.100 80
python tester.py 192.168.1.100 80 10
```

### Parameters

- `<your_device_ip>` - IP address of your Roth Touchline device (required)
- `[port]` - Port number (optional, defaults to 80)
- `[max_zones]` - Maximum number of zones to test (optional, defaults to 7, range: 1-20)

## What It Does

The tester will:

1. **Test Basic Connection** - Verify your device is reachable
2. **Send XML Request** - Use the exact same XML format as the integration
3. **Display Raw Response** - Show you exactly what your device returns
4. **Parse Response** - Attempt to extract temperature data using the integration's parser
5. **Show Zone Information** - Display detected rooms and their temperatures

## Example Output

```
🏠 Roth Touchline API Tester
==================================================
Target device: 192.168.0.104:80
Max zones: 7
Timestamp: 2025-07-25 14:30:00

🔗 Testing basic connection to http://192.168.0.104:80...
   ✅ Basic connection successful (Status: 200)

📡 Testing XML API at http://192.168.0.104:80/cgi-bin/ILRReadValues.cgi
📤 Sending XML request:
   <body><item_list><i><n>G0.RaumTemp</n></i><i><n>G0.SollTemp</n></i>...</item_list></body>

📊 Response Status: 200
📋 Response Headers:
   Content-Type: text/xml
   Content-Length: 1234

✅ Response received (1234 characters)

🔍 Analyzing XML response...
============================================================
RAW RESPONSE:
[Your device's actual XML response will be shown here]
============================================================

📊 Parsing with integration's XML parser...
✅ Successfully parsed 21 values:
   G0.RaumTemp: 2150 (raw) → 21.5°C (processed)
   G0.SollTemp: 2200 (raw) → 22.0°C (processed)
   G0.name: Living Room
   G1.RaumTemp: 1980 (raw) → 19.8°C (processed)
   G1.SollTemp: 2000 (raw) → 20.0°C (processed)
   G1.name: Bedroom
   ...

🏠 Extracting zone information...
✅ Found 3 zones:
   Zone G0 (Living Room):
     Current temp: 21.5°C
     Target temp:  22.0°C
   Zone G1 (Bedroom):
     Current temp: 19.8°C
     Target temp:  20.0°C
   Zone G2 (Kitchen):
     Current temp: 23.1°C
     Target temp:  23.0°C

✅ Test completed successfully!
```

## Troubleshooting

### Connection Issues

If you get connection errors:

1. **Check IP Address** - Make sure the IP is correct
2. **Check Network** - Ensure your computer can reach the device
3. **Check Firewall** - Temporarily disable firewall to test
4. **Try Browser** - Visit `http://your_device_ip` in a web browser

### Dependency Issues

If you get import errors:
```bash
pip install --upgrade pip
pip install aiohttp async-timeout
```

### XML Parsing Issues

If the parser shows "No values parsed":

1. The response format may be different than expected
2. Check the "RAW RESPONSE" section to see what your device actually returns
3. Share this output so the parser can be updated

## Using Results for Integration

Once you get a successful response:

1. **Note the Zone IDs** - These will be your entity names in Home Assistant
2. **Verify Temperature Values** - Make sure they match your physical thermostats
3. **Check Room Names** - These will be used for entity naming
4. **Share Response Format** - If parsing fails, share the raw response for parser updates

## Command Line Options

```bash
python tester.py <ip_address> [port]
```

- `ip_address` - Required: IP address of your Roth Touchline device
- `port` - Optional: Port number (default: 80)

## Integration with VS Code

If you're using VS Code, you can run this directly in the terminal:

1. Open terminal in VS Code (Ctrl+`)
2. Navigate to the project folder
3. Run: `python tester.py YOUR_IP_ADDRESS`
