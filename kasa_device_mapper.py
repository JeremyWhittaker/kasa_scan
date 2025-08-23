#!/usr/bin/env python3
"""Map Kasa device names to MAC addresses and save to file"""
import asyncio
import json
import csv
from datetime import datetime
from kasa import Discover

async def discover_and_map():
    print("Discovering Kasa devices...")
    devices = await Discover.discover(timeout=5)
    
    device_map = []
    for ip, dev in devices.items():
        try:
            # Get basic info without full auth
            mac = getattr(dev, 'mac', 'Unknown')
            alias = getattr(dev, 'alias', 'Unknown')
            device_type = getattr(dev, 'device_type', 'Unknown')
            model = getattr(dev, 'model', 'Unknown')
            
            device_map.append({
                'name': alias,
                'mac': mac,
                'ip': ip,
                'type': str(device_type),
                'model': model
            })
        except:
            continue
    
    return sorted(device_map, key=lambda x: x['name'].lower())

def save_results(devices):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Save as JSON
    with open('kasa_devices.json', 'w') as f:
        json.dump({
            'timestamp': timestamp,
            'device_count': len(devices),
            'devices': devices
        }, f, indent=2)
    
    # Save as CSV
    with open('kasa_devices.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'mac', 'ip', 'type', 'model'])
        writer.writeheader()
        writer.writerows(devices)
    
    # Save as simple text mapping
    with open('kasa_device_map.txt', 'w') as f:
        f.write(f"Kasa Device Map - {timestamp}\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"{'Device Name':<35} {'MAC Address':<20} {'IP Address'}\n")
        f.write("-" * 80 + "\n")
        for dev in devices:
            f.write(f"{dev['name']:<35} {dev['mac']:<20} {dev['ip']}\n")

def main():
    devices = asyncio.run(discover_and_map())
    
    print(f"\nDiscovered {len(devices)} devices")
    print("-" * 80)
    
    # Display results
    for dev in devices:
        print(f"{dev['name']:<35} {dev['mac']:<20} {dev['ip']}")
    
    # Save to files
    save_results(devices)
    
    print(f"\nResults saved to:")
    print("  - kasa_devices.json (full details)")
    print("  - kasa_devices.csv (spreadsheet format)")  
    print("  - kasa_device_map.txt (simple text map)")
    
    # Verify test device
    for dev in devices:
        if dev['name'].lower() == 'office sconce left':
            if dev['mac'].upper() == '98:25:4A:5F:4E:6F':
                print(f"\n✓ TEST PASSED: Found 'Office Sconce Left' with correct MAC!")
            break

if __name__ == "__main__":
    main()