#!/usr/bin/env python3
"""Alternative Kasa cloud API approach"""
import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Try different API endpoints
API_ENDPOINTS = [
    "https://wap.tplinkcloud.com",
    "https://eu-wap.tplinkcloud.com",
    "https://use1-wap.tplinkcloud.com"
]

def try_login(email, password, endpoint):
    """Try different login methods"""
    methods = [
        # Method 1: Current Kasa app format
        {
            "method": "login",
            "params": {
                "appType": "Kasa_Android",
                "cloudUserName": email,
                "cloudPassword": password,
                "terminalUUID": "12345"
            }
        },
        # Method 2: With version
        {
            "method": "login", 
            "params": {
                "appType": "Kasa_Android",
                "cloudUserName": email,
                "cloudPassword": password,
                "terminalUUID": "12345",
                "appVer": "2.35.0.1021"
            }
        },
        # Method 3: Newer format
        {
            "method": "login",
            "params": {
                "appType": "TAPO_ANDROID",
                "cloudUserName": email,
                "cloudPassword": password,
                "terminalUUID": "12345"
            }
        }
    ]
    
    for i, method in enumerate(methods):
        try:
            print(f"Trying method {i+1} on {endpoint}...")
            response = requests.post(endpoint, json=method, timeout=10)
            result = response.json()
            
            if result.get('error_code') == 0:
                print(f"Success with method {i+1}!")
                return result.get('result', {}).get('token')
            else:
                print(f"Method {i+1} failed: {result.get('msg', 'Unknown error')}")
        except Exception as e:
            print(f"Method {i+1} error: {e}")
    
    return None

def main():
    email = os.getenv('KASA_EMAIL')
    password = os.getenv('KASA_PASSWORD')
    
    if not email or not password:
        print("Error: KASA_EMAIL and KASA_PASSWORD must be set in .env file")
        return
    
    # Try different endpoints
    for endpoint in API_ENDPOINTS:
        print(f"\nTrying endpoint: {endpoint}")
        token = try_login(email, password, endpoint)
        
        if token:
            print(f"\nAuthenticated! Token: {token[:20]}...")
            
            # Get device list
            device_url = f"{endpoint}?token={token}"
            response = requests.post(device_url, json={"method": "getDeviceList"})
            result = response.json()
            
            if result.get('error_code') == 0:
                devices = result.get('result', {}).get('deviceList', [])
                print(f"\nFound {len(devices)} devices:")
                print("-" * 80)
                print(f"{'MAC Address':<20} {'Device Name':<30} {'Device ID'}")
                print("-" * 80)
                
                for device in devices:
                    mac = device.get('deviceMac', 'Unknown')
                    alias = device.get('alias', 'Unknown')
                    device_id = device.get('deviceId', 'Unknown')
                    print(f"{mac:<20} {alias:<30} {device_id}")
                    
                    # Check for our test device
                    if alias.lower() == "office sconce left":
                        print(f"\n✓ Found test device: {alias} with MAC {mac}")
                        if mac == "98:25:4A:5F:4E:6F":
                            print("✓ MAC address matches expected value!")
                        else:
                            print(f"✗ MAC mismatch! Expected 98:25:4A:5F:4E:6F, got {mac}")
                
                return
            else:
                print(f"Failed to get devices: {result.get('msg', 'Unknown error')}")

if __name__ == "__main__":
    main()