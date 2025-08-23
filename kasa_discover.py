#!/usr/bin/env python3
"""
Async discovery with python-kasa:
prints alias, IP, and MAC for every device it can see on the LAN.
"""
import asyncio
import logging
from kasa import Discover

logging.basicConfig(level=logging.INFO, format='%(message)s')

async def main() -> None:
    print("Discovering Kasa devices on the network...")
    print("-" * 80)
    
    devices = await Discover.discover()
    
    if not devices:
        print("No devices found on the network.")
        return
        
    print(f"Found {len(devices)} devices:\n")
    print(f"{'MAC Address':<20} {'Device Name':<30} {'IP Address'}")
    print("-" * 80)
    
    test_device_found = False
    
    for ip, dev in devices.items():
        await dev.update()  # pulls full sysinfo
        logging.info("%-20s %-30s %s", dev.mac, dev.alias, ip)
        
        # Check for test device
        if dev.alias.lower() == "office sconce left":
            test_device_found = True
            print("\n" + "=" * 80)
            print("TEST DEVICE FOUND!")
            print(f"Name: {dev.alias}")
            print(f"MAC:  {dev.mac}")
            print(f"IP:   {ip}")
            
            if dev.mac.upper() == "98:25:4A:5F:4E:6F":
                print("✓ MAC ADDRESS MATCHES EXPECTED VALUE!")
            else:
                print(f"✗ MAC MISMATCH! Expected 98:25:4A:5F:4E:6F, got {dev.mac}")
            print("=" * 80 + "\n")
    
    if not test_device_found:
        print("\n✗ Test device 'office sconce left' not found in discovered devices")

if __name__ == "__main__":
    asyncio.run(main())