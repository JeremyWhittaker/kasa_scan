#!/bin/bash

# Load environment variables
source .env

# Authenticate and get token
echo "Authenticating..."
TOKEN=$(curl -s -H "Content-Type: application/json" \
  -d "{\"method\":\"login\",\"params\":{\"appType\":\"Kasa_Android\",\"cloudUserName\":\"$KASA_EMAIL\",\"cloudPassword\":\"$KASA_PASSWORD\",\"terminalUUID\":\"MY_UUID_v1\"}}" \
  "https://wap.tplinkcloud.com" | jq -r '.result.token')

if [ -z "$TOKEN" ]; then
  echo "Failed to authenticate"
  exit 1
fi

echo "Token obtained successfully"
echo ""

# Get device list
echo "Kasa Devices (Name -> MAC Address):"
echo "===================================="
curl -s -H "Content-Type: application/json" \
  -d '{"method":"getDeviceList"}' \
  "https://wap.tplinkcloud.com?token=$TOKEN" | jq -r '.result.deviceList[] | "Name: \(.alias)\nMAC:  \(.deviceMac)\nID:   \(.deviceId)\n------------------------------------"'