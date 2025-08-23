#!/usr/bin/env python3
"""Modern Kasa API with updated parameters"""
import json
import requests
import hashlib
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

def md5_hash(string):
    return hashlib.md5(string.encode()).hexdigest()

def authenticate(email, password):
    """Authenticate using modern Kasa API"""
    url = "https://wap.tplinkcloud.com"
    
    # Generate UUID
    terminal_uuid = str(uuid.uuid4())
    
    # Try with latest app version
    payload = {
        "method": "login",
        "params": {
            "appType": "Kasa_Android", 
            "cloudUserName": email,
            "cloudPassword": password,
            "terminalUUID": terminal_uuid
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Kasa/2.35.0 (Android 10)",
        "Accept": "application/json"
    }
    
    # First attempt - standard auth
    print("Attempting standard authentication...")
    response = requests.post(url, json=payload, headers=headers)
    result = response.json()
    
    if result.get('error_code') == -23003:  # App version too old
        # Try with requestTimeMils
        import time
        payload["requestTimeMils"] = int(time.time() * 1000)
        print("Retrying with timestamp...")
        response = requests.post(url, json=payload, headers=headers)
        result = response.json()
    
    return result

def get_devices_local():
    """Alternative: Try to discover devices locally"""
    print("\nAttempting local device discovery...")
    import socket
    import struct
    
    # Broadcast discovery message
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(3)
    
    # TP-Link discovery port
    discovery_msg = b'{"system":{"get_sysinfo":{}}}'
    
    try:
        sock.sendto(discovery_msg, ('<broadcast>', 9999))
        print("Sent discovery broadcast...")
        
        devices = []
        while True:
            try:
                data, addr = sock.recvfrom(2048)
                print(f"Found device at {addr[0]}")
                devices.append(addr[0])
            except socket.timeout:
                break
    except Exception as e:
        print(f"Local discovery error: {e}")
    finally:
        sock.close()
    
    return devices

def main():
    email = os.getenv('KASA_EMAIL')
    password = os.getenv('KASA_PASSWORD')
    
    if not email or not password:
        print("Error: KASA_EMAIL and KASA_PASSWORD must be set in .env file")
        return
    
    # Try cloud authentication
    result = authenticate(email, password)
    
    print(f"\nAuthentication result: {json.dumps(result, indent=2)}")
    
    if result.get('error_code') == 0:
        token = result['result']['token']
        print(f"\nSuccess! Token: {token[:20]}...")
        
        # Get devices
        device_url = f"https://wap.tplinkcloud.com?token={token}"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Kasa/2.35.0 (Android 10)"
        }
        
        response = requests.post(
            device_url, 
            json={"method": "getDeviceList"},
            headers=headers
        )
        devices_result = response.json()
        
        if devices_result.get('error_code') == 0:
            devices = devices_result['result']['deviceList']
            print(f"\nFound {len(devices)} devices:")
            print("-" * 80)
            
            found_test_device = False
            for device in devices:
                mac = device.get('deviceMac', 'Unknown')
                alias = device.get('alias', 'Unknown')
                print(f"MAC: {mac:<20} Name: {alias}")
                
                if alias.lower() == "office sconce left":
                    found_test_device = True
                    if mac == "98:25:4A:5F:4E:6F":
                        print("✓ TEST PASSED: Found 'office sconce left' with correct MAC!")
                    else:
                        print(f"✗ TEST FAILED: 'office sconce left' has MAC {mac}, expected 98:25:4A:5F:4E:6F")
            
            if not found_test_device:
                print("\n✗ TEST FAILED: Device 'office sconce left' not found")
    else:
        print(f"\nAuthentication failed: {result.get('msg', 'Unknown error')}")
        print("\nTrying local discovery as fallback...")
        get_devices_local()

if __name__ == "__main__":
    main()