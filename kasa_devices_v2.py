#!/usr/bin/env python3
"""Dump all Kasa devices & MACs via cloud API."""
import json
import logging
import uuid
import requests
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(message)s')

API = "https://wap.tplinkcloud.com"
UUID = str(uuid.uuid4())

def _call(data: dict, token: str | None = None) -> dict:
    url = f"{API}?token={token}" if token else API
    r = requests.post(url, json=data, timeout=10)
    r.raise_for_status()
    result = r.json()
    
    if result.get('error_code') != 0:
        logging.error(f"API Error: {result}")
        raise Exception(f"API call failed: {result.get('msg', 'Unknown error')}")
    
    return result

def login(username: str, password: str) -> str:
    payload = {
        "method": "login",
        "params": {
            "appType": "Kasa_Android",
            "cloudUserName": username,
            "cloudPassword": password,
            "terminalUUID": UUID,
            "appName": "Kasa_Android",
            "ospf": "Android+6.0.1",
            "netType": "wifi",
            "locale": "en_US"
        },
    }
    return _call(payload)["result"]["token"]

def get_devices(token: str) -> list[dict]:
    return _call({"method": "getDeviceList"}, token)["result"]["deviceList"]

if __name__ == "__main__":
    username = os.getenv('KASA_EMAIL')
    password = os.getenv('KASA_PASSWORD')
    
    if not username or not password:
        logging.error("Error: KASA_EMAIL and KASA_PASSWORD must be set in .env file")
        return
    
    token = login(username, password)
    devices = get_devices(token)
    
    logging.info("%-20s %-30s %s", "MAC Address", "Device Name", "Device ID")
    logging.info("-" * 80)
    
    for dev in devices:
        logging.info("%-20s %-30s %s", dev["deviceMac"], dev["alias"], dev["deviceId"])