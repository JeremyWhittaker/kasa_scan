#!/usr/bin/env python3
"""Final script to map Kasa device names to MAC addresses"""
import subprocess
import json
import csv
from datetime import datetime

# Run the working basic scan and capture output
result = subprocess.run(['python', 'kasa_basic_scan.py'], 
                       capture_output=True, text=True)

# Parse the output
lines = result.stdout.split('\n')
devices = []

# Find the device listing section
in_device_list = False
for line in lines:
    if 'MAC Address' in line and 'Device Name' in line:
        in_device_list = True
        continue
    if in_device_list and line.strip() and not line.startswith('-'):
        parts = line.split()
        if len(parts) >= 3:
            mac = parts[0]
            ip = parts[-1]
            # Device name is everything between MAC and IP
            name = ' '.join(parts[1:-1])
            
            if mac != 'Unknown' and name != 'None':
                devices.append({
                    'name': name,
                    'mac': mac,
                    'ip': ip
                })

# Sort by name
devices = sorted(devices, key=lambda x: x['name'].lower())

# Save outputs
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# JSON format
with open('kasa_devices.json', 'w') as f:
    json.dump({
        'timestamp': timestamp,
        'device_count': len(devices),
        'devices': devices
    }, f, indent=2)

# CSV format
with open('kasa_devices.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['name', 'mac', 'ip'])
    writer.writeheader()
    writer.writerows(devices)

# Simple text map
with open('kasa_device_map.txt', 'w') as f:
    f.write(f"Kasa Device Map - {timestamp}\n")
    f.write("=" * 80 + "\n\n")
    f.write(f"Total devices: {len(devices)}\n\n")
    f.write(f"{'Device Name':<40} {'MAC Address':<20} {'IP Address'}\n")
    f.write("-" * 80 + "\n")
    for dev in devices:
        f.write(f"{dev['name']:<40} {dev['mac']:<20} {dev['ip']}\n")

print(f"Successfully mapped {len(devices)} Kasa devices!")
print("\nFiles created:")
print("  - kasa_devices.json")
print("  - kasa_devices.csv")
print("  - kasa_device_map.txt")

# Test verification
for dev in devices:
    if dev['name'].lower() == 'office sconce left':
        if dev['mac'].upper() == '98:25:4A:5F:4E:6F':
            print(f"\n✓ TEST PASSED: 'Office Sconce Left' has MAC {dev['mac']}")
        else:
            print(f"\n✗ TEST FAILED: Expected MAC 98:25:4A:5F:4E:6F, got {dev['mac']}")
        break