#!/usr/bin/env python3
"""Basic network scan for Kasa devices"""
import socket
import json
import struct
import time

def discover_kasa_devices():
    """Discover TP-Link devices on the network using UDP broadcast"""
    devices = []
    
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(3)
    
    # TP-Link discovery ports
    ports = [9999, 20002]
    
    # Discovery message for different device types
    messages = [
        b'{"system":{"get_sysinfo":{}}}',
        b'\x02\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x46\x3b\xe8\x78',
    ]
    
    print("Scanning network for Kasa devices...")
    print("-" * 80)
    
    for port in ports:
        for msg in messages:
            try:
                # Send broadcast
                sock.sendto(msg, ('255.255.255.255', port))
                
                # Receive responses
                start_time = time.time()
                while time.time() - start_time < 2:
                    try:
                        data, addr = sock.recvfrom(1024)
                        ip = addr[0]
                        
                        # Try to parse response
                        try:
                            # Decrypt if needed (XOR with 0xAB)
                            decrypted = bytes([b ^ 0xAB for b in data])
                            info = json.loads(decrypted)
                            
                            if 'system' in info and 'get_sysinfo' in info['system']:
                                sysinfo = info['system']['get_sysinfo']
                                alias = sysinfo.get('alias', 'Unknown')
                                mac = sysinfo.get('mac', 'Unknown')
                                devices.append({'ip': ip, 'mac': mac, 'alias': alias})
                        except:
                            # Try plain JSON
                            try:
                                info = json.loads(data)
                                if 'result' in info:
                                    alias = info['result'].get('device_alias', 'Unknown')
                                    mac = info['result'].get('mac', 'Unknown')
                                    devices.append({'ip': ip, 'mac': mac, 'alias': alias})
                            except:
                                pass
                                
                    except socket.timeout:
                        break
            except Exception as e:
                continue
    
    sock.close()
    return devices

def main():
    devices = discover_kasa_devices()
    
    if not devices:
        print("No devices found. Trying alternative method...")
        
        # Try using kasa library with just discovery, no auth
        import asyncio
        from kasa import Discover
        
        async def quick_discover():
            discovered = await Discover.discover(timeout=3)
            device_list = []
            
            for ip, dev in discovered.items():
                # Just get the basic attributes without update
                device_list.append({
                    'ip': ip,
                    'mac': getattr(dev, 'mac', 'Unknown'),
                    'alias': getattr(dev, 'alias', 'Unknown')
                })
            
            return device_list
        
        devices = asyncio.run(quick_discover())
    
    print(f"\nFound {len(devices)} devices:")
    print(f"{'MAC Address':<20} {'Device Name':<35} {'IP Address'}")
    print("-" * 80)
    
    target_mac = "98:25:4A:5F:4E:6F"
    found = False
    
    for dev in devices:
        mac = str(dev.get('mac', 'Unknown'))
        alias = str(dev.get('alias', 'Unknown'))
        ip = str(dev.get('ip', 'Unknown'))
        
        print(f"{mac:<20} {alias:<35} {ip}")
        
        if mac.upper() == target_mac.upper():
            found = True
            print(f"\n{'='*80}")
            print(f"✓ FOUND TARGET DEVICE!")
            print(f"  Name: {alias}")
            print(f"  MAC:  {mac}")
            print(f"  IP:   {ip}")
            if alias.lower() == "office sconce left":
                print(f"  ✓ TEST PASSED: Name matches 'office sconce left'")
            else:
                print(f"  ! Name is '{alias}', expected 'office sconce left'")
            print(f"{'='*80}\n")
    
    if not found:
        print(f"\n✗ Device with MAC {target_mac} not found")

if __name__ == "__main__":
    main()