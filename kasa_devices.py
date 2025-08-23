#!/usr/bin/env python3
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def get_kasa_token():
    email = os.getenv('KASA_EMAIL')
    password = os.getenv('KASA_PASSWORD')
    
    auth_url = "https://wap.tplinkcloud.com"
    auth_payload = {
        "method": "login",
        "params": {
            "appType": "Kasa_Android",
            "cloudUserName": email,
            "cloudPassword": password,
            "terminalUUID": "MY_UUID_v1"
        }
    }
    
    response = requests.post(auth_url, json=auth_payload)
    result = response.json()
    
    if result.get('error_code') == 0:
        return result['result']['token']
    else:
        raise Exception(f"Authentication failed: {result}")

def get_device_list(token):
    url = f"https://wap.tplinkcloud.com?token={token}"
    payload = {"method": "getDeviceList"}
    
    response = requests.post(url, json=payload)
    result = response.json()
    
    if result.get('error_code') == 0:
        return result['result']['deviceList']
    else:
        raise Exception(f"Failed to get device list: {result}")

def main():
    try:
        print("Authenticating with Kasa...")
        token = get_kasa_token()
        
        print("Fetching device list...")
        devices = get_device_list(token)
        
        print("\nKasa Devices (Name -> MAC Address):")
        print("-" * 50)
        
        for device in devices:
            name = device.get('alias', 'Unknown')
            mac = device.get('deviceMac', 'Unknown')
            device_id = device.get('deviceId', 'Unknown')
            
            print(f"Name: {name}")
            print(f"MAC:  {mac}")
            print(f"ID:   {device_id}")
            print("-" * 50)
        
        print("\nCSV Format:")
        print("Name,MAC,DeviceID")
        for device in devices:
            print(f"{device.get('alias', 'Unknown')},{device.get('deviceMac', 'Unknown')},{device.get('deviceId', 'Unknown')}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()