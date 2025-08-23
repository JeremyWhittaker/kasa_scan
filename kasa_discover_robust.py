#!/usr/bin/env python3
"""
Robust async discovery with python-kasa:
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
    print(f"{'MAC Address':<20} {'Device Name':<30} {'IP Address':<15} {'Status'}")
    print("-" * 80)
    
    test_device_found = False
    successful_devices = []
    failed_devices = []
    
    for ip, dev in devices.items():
        try:
            await dev.update()  # pulls full sysinfo
            mac = dev.mac if hasattr(dev, 'mac') else 'Unknown'
            alias = dev.alias if hasattr(dev, 'alias') else 'Unknown'
            
            logging.info("%-20s %-30s %-15s %s", mac, alias, ip, "✓ OK")
            successful_devices.append((mac, alias, ip))
            
            # Check for test device
            if alias.lower() == "office sconce left":
                test_device_found = True
                print("\n" + "=" * 80)
                print("TEST DEVICE FOUND!")
                print(f"Name: {alias}")
                print(f"MAC:  {mac}")
                print(f"IP:   {ip}")
                
                if mac.upper() == "98:25:4A:5F:4E:6F":
                    print("✓ MAC ADDRESS MATCHES EXPECTED VALUE!")
                else:
                    print(f"✗ MAC MISMATCH! Expected 98:25:4A:5F:4E:6F, got {mac}")
                print("=" * 80 + "\n")
                
        except Exception as e:
            error_msg = str(e).split('\n')[0]  # Get first line of error
            logging.info("%-20s %-30s %-15s %s", "Error", "Unable to connect", ip, f"✗ {error_msg[:40]}...")
            failed_devices.append((ip, error_msg))
    
    # Summary
    print(f"\nSummary:")
    print(f"  Successfully discovered: {len(successful_devices)} devices")
    print(f"  Failed to connect: {len(failed_devices)} devices")
    
    if not test_device_found:
        print("\n✗ Test device 'office sconce left' not found in discovered devices")
        print("\nSearching for device with MAC 98:25:4A:5F:4E:6F...")
        for mac, alias, ip in successful_devices:
            if mac.upper() == "98:25:4A:5F:4E:6F":
                print(f"Found device with target MAC: {alias} at {ip}")
                break
        else:
            print("Device with MAC 98:25:4A:5F:4E:6F not found")

if __name__ == "__main__":
    asyncio.run(main())