#!/usr/bin/env python3
"""
Roth Touchline API Tester
Standalone script to test the XML API communication with Roth Touchline devices.

Usage: python tester.py <ip_address> [port] [max_zones]
Example: python tester.py 192.168.0.104
Example: python tester.py 192.168.0.104 80
Example: python tester.py 192.168.0.104 80 10
"""

import asyncio
import sys
import time
from typing import Optional
import aiohttp
import async_timeout

# Import our XML parser from the integration
from custom_components.roth_touchline.xml_parser import RothTouchlineXMLParser


class RothTouchlineTester:
    """Standalone tester for Roth Touchline XML API."""

    def __init__(self, host: str, port: int = 80, max_zones: int = 7):
        """Initialize the tester."""
        self.host = host
        self.port = port
        self.max_zones = max_zones
        self.base_url = f"http://{host}:{port}"
        self.endpoint = "/cgi-bin/ILRReadValues.cgi"
        self.timeout = 10

    def get_headers(self) -> dict[str, str]:
        """Get the required headers for Roth Touchline requests."""
        return {
            "Accept-Language": "*",
            "Content-Type": "text/xml",
            "User-Agent": "SpiderControl/1.0 (iniNet-Solutions GmbH)",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Accept": "text/html, image/gif, image/jpeg, *; q = .2, */*; q=.2",
        }

    async def test_basic_connection(self) -> bool:
        """Test basic HTTP connectivity to the device."""
        print(f"🔗 Testing basic connection to {self.base_url}...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with async_timeout.timeout(self.timeout):
                    async with session.get(self.base_url) as response:
                        print(f"   ✅ Basic connection successful (Status: {response.status})")
                        return True
        except asyncio.TimeoutError:
            print(f"   ❌ Connection timeout after {self.timeout} seconds")
            return False
        except aiohttp.ClientError as err:
            print(f"   ❌ Connection error: {err}")
            return False
        except Exception as err:
            print(f"   ❌ Unexpected error: {err}")
            return False

    async def test_xml_api(self, zones_to_test: list[str] = None) -> Optional[str]:
        """Test the XML API with temperature requests."""
        if zones_to_test is None:
            zones_to_test = [f"G{i}" for i in range(self.max_zones)]
        
        # Create XML request using integration's parser
        request_items = []
        for zone in zones_to_test:
            zone_num = zone.replace("G", "")
            request_items.extend([
                f"G{zone_num}.RaumTemp",
                f"G{zone_num}.SollTemp",
                f"G{zone_num}.name"
            ])
        
        # Add system status
        request_items.append("R0.SystemStatus")
        
        xml_body = RothTouchlineXMLParser.create_request_xml(request_items)
        
        print(f"📡 Testing XML API at {self.base_url}{self.endpoint}")
        print(f"📤 Sending XML request:")
        print(f"   {xml_body}")
        print()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with async_timeout.timeout(self.timeout):
                    async with session.post(
                        f"{self.base_url}{self.endpoint}",
                        data=xml_body,
                        headers=self.get_headers()
                    ) as response:
                        
                        print(f"📊 Response Status: {response.status}")
                        print(f"📋 Response Headers:")
                        for key, value in response.headers.items():
                            print(f"   {key}: {value}")
                        print()
                        
                        if response.status == 200:
                            response_text = await response.text()
                            print(f"✅ Response received ({len(response_text)} characters)")
                            return response_text
                        else:
                            error_text = await response.text()
                            print(f"❌ HTTP Error {response.status}")
                            print(f"Error response: {error_text}")
                            return None
                            
        except asyncio.TimeoutError:
            print(f"❌ Request timeout after {self.timeout} seconds")
            return None
        except aiohttp.ClientError as err:
            print(f"❌ Request error: {err}")
            return None
        except Exception as err:
            print(f"❌ Unexpected error: {err}")
            return None

    def analyze_response(self, response_text: str) -> dict:
        """Analyze and parse the XML response."""
        print("🔍 Analyzing XML response...")
        print("=" * 60)
        print("RAW RESPONSE:")
        print(response_text)
        print("=" * 60)
        print()
        
        # Try to parse using our integration's parser
        print("📊 Parsing with integration's XML parser...")
        values = RothTouchlineXMLParser.parse_values_response(response_text)
        
        if values:
            print(f"✅ Successfully parsed {len(values)} values:")
            for key, value in values.items():
                # Show if this is a temperature value that will be processed
                if key.endswith('.RaumTemp') or key.endswith('.SollTemp'):
                    try:
                        processed_temp = float(value) / 100.0
                        print(f"   {key}: {value} (raw) → {processed_temp:.1f}°C (processed)")
                    except (ValueError, TypeError):
                        print(f"   {key}: {value}")
                else:
                    print(f"   {key}: {value}")
        else:
            print("❌ No values parsed - response format may be different than expected")
        
        print()
        
        # Try to extract zone information
        print("🏠 Extracting zone information...")
        zones = RothTouchlineXMLParser.get_available_zones(values, self.max_zones)
        
        if zones:
            print(f"✅ Found {len(zones)} zones:")
            for zone in zones:
                zone_data = RothTouchlineXMLParser.extract_zone_data(values, zone['id'])
                print(f"   Zone {zone['id']} ({zone['name']}):")
                print(f"     Current temp: {zone_data.get('current_temperature', 'N/A')}°C")
                print(f"     Target temp:  {zone_data.get('target_temperature', 'N/A')}°C")
        else:
            print("❌ No zones detected")
        
        return values

    async def run_complete_test(self) -> bool:
        """Run the complete test sequence."""
        print("🏠 Roth Touchline API Tester")
        print("=" * 50)
        print(f"Target device: {self.host}:{self.port}")
        print(f"Max zones: {self.max_zones}")
        print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Test basic connection
        if not await self.test_basic_connection():
            print("❌ Cannot proceed - basic connection failed")
            return False
        
        print()
        
        # Test XML API
        response = await self.test_xml_api()
        if response is None:
            print("❌ Cannot proceed - XML API request failed")
            return False
        
        print()
        
        # Analyze response
        self.analyze_response(response)
        
        print()
        print("✅ Test completed successfully!")
        return True


async def main():
    """Main function to run the tester."""
    if len(sys.argv) < 2:
        print("Usage: python tester.py <ip_address> [port] [max_zones]")
        print("Example: python tester.py 192.168.0.104")
        print("Example: python tester.py 192.168.0.104 80")
        print("Example: python tester.py 192.168.0.104 80 10")
        sys.exit(1)
    
    host = sys.argv[1]
    port = 80
    max_zones = 7
    
    if len(sys.argv) >= 3:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print(f"Error: Invalid port number '{sys.argv[2]}'")
            sys.exit(1)
    
    if len(sys.argv) >= 4:
        try:
            max_zones = int(sys.argv[3])
            if max_zones < 1 or max_zones > 20:
                print(f"Error: max_zones must be between 1 and 20, got {max_zones}")
                sys.exit(1)
        except ValueError:
            print(f"Error: Invalid max_zones number '{sys.argv[3]}'")
            sys.exit(1)
    
    # Check if required dependencies are available
    try:
        import aiohttp
        import async_timeout
    except ImportError as e:
        print(f"❌ Missing required dependency: {e}")
        print("Please install with: pip install aiohttp async-timeout")
        sys.exit(1)
    
    # Create and run tester
    tester = RothTouchlineTester(host, port, max_zones)
    
    try:
        success = await tester.run_complete_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
