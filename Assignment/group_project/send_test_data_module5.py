#!/usr/bin/env python3
"""
Command-line tool to send test data to Module 5 displays
Usage:
    python send_test_data_module5.py [scenario] [--court-id ID] [--custom KEY=VALUE]
    
Examples:
    python send_test_data_module5.py normal
    python send_test_data_module5.py full --court-id basketball_a
    python send_test_data_module5.py normal --custom current.people_count=8 --custom weather.temp_c=35
"""

import socketio
import sys
import argparse
import json

# Default server URL
DEFAULT_SERVER_URL = 'http://192.168.72.161:5000'

def send_test_data(server_url, scenario='normal', court_id='basketball_a', custom_data=None):
    """Send test data to Module 5 via Socket.IO"""
    print(f"Connecting to server: {server_url}")
    
    sio = socketio.Client()
    
    try:
        sio.connect(server_url)
        print("✓ Connected to server")
        
        # Prepare request data
        request_data = {
            'court_id': court_id,
            'scenario': scenario
        }
        
        if custom_data:
            request_data['custom_data'] = custom_data
        
        print(f"\nSending test data:")
        print(f"  Scenario: {scenario}")
        print(f"  Court ID: {court_id}")
        if custom_data:
            print(f"  Custom data: {json.dumps(custom_data, indent=2)}")
        
        # Send test data request
        response = sio.call('send_test_data_module5', request_data, timeout=5)
        
        if response and response.get('status') == 'success':
            print(f"\n✓ Test data sent successfully!")
            print(f"  Response: {json.dumps(response, indent=2)}")
            return True
        else:
            print(f"\n✗ Failed to send test data")
            print(f"  Response: {response}")
            return False
            
    except socketio.exceptions.ConnectionError as e:
        print(f"✗ Connection error: {e}")
        print(f"  Make sure the server is running at {server_url}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if sio.connected:
            sio.disconnect()
            print("\nDisconnected from server")

def parse_custom_data(custom_args):
    """Parse --custom KEY=VALUE arguments into a dict"""
    if not custom_args:
        return None
    
    custom_data = {}
    for arg in custom_args:
        if '=' not in arg:
            print(f"Warning: Invalid custom data format '{arg}' (expected KEY=VALUE), skipping")
            continue
        
        key, value = arg.split('=', 1)
        key = key.strip()
        value = value.strip()
        
        # Try to parse value as number or boolean
        try:
            if '.' in value:
                value = float(value)
            else:
                value = int(value)
        except ValueError:
            # Keep as string
            if value.lower() in ('true', 'false'):
                value = value.lower() == 'true'
        
        # Handle dot notation (e.g., "current.people_count" -> nested dict)
        if '.' in key:
            parts = key.split('.')
            current = custom_data
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
        else:
            custom_data[key] = value
    
    return custom_data

def main():
    parser = argparse.ArgumentParser(
        description='Send test data to Module 5 displays',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Send normal scenario
  python send_test_data_module5.py normal
  
  # Send full scenario for specific court
  python send_test_data_module5.py full --court-id basketball_b
  
  # Send normal with custom people count
  python send_test_data_module5.py normal --custom current.people_count=8
  
  # Send with multiple custom values
  python send_test_data_module5.py normal --custom current.people_count=8 --custom weather.temp_c=35 --custom info.rating_avg=4.5
        """
    )
    
    parser.add_argument(
        'scenario',
        choices=['normal', 'full', 'empty', 'busy', 'light', 'custom'],
        help='Test scenario to send'
    )
    
    parser.add_argument(
        '--server-url',
        default=DEFAULT_SERVER_URL,
        help=f'Server URL (default: {DEFAULT_SERVER_URL})'
    )
    
    parser.add_argument(
        '--court-id',
        default='basketball_a',
        help='Court ID (default: basketball_a)'
    )
    
    parser.add_argument(
        '--custom',
        action='append',
        dest='custom_data',
        help='Custom data in KEY=VALUE format (can be used multiple times). Supports dot notation (e.g., current.people_count=8)'
    )
    
    args = parser.parse_args()
    
    custom_data = parse_custom_data(args.custom_data)
    
    success = send_test_data(
        server_url=args.server_url,
        scenario=args.scenario,
        court_id=args.court_id,
        custom_data=custom_data
    )
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
