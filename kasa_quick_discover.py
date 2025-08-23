#!/usr/bin/env python3
"""Quick discovery - just get basic info without full update"""
import asyncio
from kasa import Discover

async def main():
    print("Quick discovery of Kasa devices...")
    print("-" * 80)
    
    # Discover with shorter timeout
    devices = await Discover.discover(timeout=5)
    
    print(f"Found {len(devices)} devices:\n")
    print(f"{'MAC Address':<20} {'Device Name':<35} {'IP Address'}")
    print("-" * 80)
    
    target_mac = "98:25:4A:5F:4E:6F"
    found_target = False
    
    for ip, dev in devices.items():
        try:
            # Try to get basic info without full update
            await dev.update()
            mac = getattr(dev, 'mac', 'Unknown')
            alias = getattr(dev, 'alias', 'Unknown')
            
            print(f"{mac:<20} {alias:<35} {ip}")
            
            # Check for our test device
            if mac.upper() == target_mac.upper():
                found_target = True
                print(f"\n{'='*80}")
                print(f"✓ FOUND TARGET DEVICE!")
                print(f"  Name: {alias}")
                print(f"  MAC:  {mac}")
                print(f"  IP:   {ip}")
                
                if alias.lower() == "office sconce left":
                    print(f"  ✓ Name matches expected 'office sconce left'")
                else:
                    print(f"  ! Name is '{alias}', expected 'office sconce left'")
                print(f"{'='*80}\n")
                
        except Exception as e:
            # Just skip devices that error
            continue
    
    if not found_target:
        print(f"\n✗ Device with MAC {target_mac} not found")
        print("\nDevices found with 'office' in name:")
        for ip, dev in devices.items():
            try:
                await dev.update()
                alias = getattr(dev, 'alias', 'Unknown')
                mac = getattr(dev, 'mac', 'Unknown')
                if 'office' in alias.lower():
                    print(f"  {mac} - {alias}")
            except:
                pass

if __name__ == "__main__":
    asyncio.run(main())