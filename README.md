# Kasa Device Scanner

A Python tool to discover and map TP-Link Kasa smart home devices on your local network, matching device names to their MAC addresses.

## Features

- Local network discovery (no cloud API required)
- Maps device names to MAC addresses
- Multiple output formats (JSON, CSV, TXT)
- Works around cloud API authentication issues
- Fast discovery using broadcast UDP

## Installation

1. Clone this repository:
```bash
git clone git@github.com:JeremyWhittaker/kasa_scan.git
cd kasa_scan
```

2. Install dependencies:
```bash
pip install python-kasa python-dotenv requests
```

3. Create a `.env` file (only needed for cloud API scripts):
```bash
KASA_EMAIL=your_email@example.com
KASA_PASSWORD=your_password
```

## Usage

### Basic Local Discovery (Recommended)

The main script discovers devices on your local network without needing cloud authentication:

```bash
python kasa_basic_scan.py
```

This will:
- Scan your network for Kasa devices
- Display device names, MAC addresses, and IP addresses
- Work even when cloud API authentication fails

### Generate Device Mapping Files

To create output files with device mappings:

```bash
python kasa_map_devices.py
```

This creates:
- `kasa_devices.json` - Full device details in JSON format
- `kasa_devices.csv` - Spreadsheet-compatible format
- `kasa_device_map.txt` - Simple text mapping table

### Other Scripts

- `kasa_devices.py` - Original cloud API script (requires valid credentials)
- `kasa_cloud_api.py` - Alternative cloud API implementation
- `kasa_discover.py` - Uses python-kasa library for discovery
- `kasa_device_mapper.py` - Alternative mapping implementation

## Output Example

```
MAC Address          Device Name                         IP Address
--------------------------------------------------------------------------------
98:25:4a:5f:4e:6f    Office Sconce Left                  172.16.106.163
98:25:4a:5f:4e:cb    Office Sconce Right                 172.16.106.162
50:91:E3:44:A0:DA    kitchen desk light                  172.16.106.126
```

## Troubleshooting

### Cloud API Authentication Fails
The TP-Link cloud API frequently changes authentication requirements. If cloud scripts fail with "App version is too old", use the local discovery scripts (`kasa_basic_scan.py`) instead.

### No Devices Found
- Ensure you're on the same network as your Kasa devices
- Check that your firewall allows UDP port 9999
- Try running with sudo/admin privileges if needed

### Device Not Responding
Some newer devices may require authentication. The script will show these as discovered but may not retrieve full details.

## Technical Details

The scanner uses multiple discovery methods:
1. UDP broadcast on port 9999 (primary method)
2. python-kasa library discovery
3. Cloud API (when credentials are available)

Discovery works by sending broadcast packets that Kasa devices respond to with their basic information.

## Security Notes

- Never commit your `.env` file or credentials
- The `.gitignore` file excludes sensitive files
- Cloud API credentials are only needed for cloud-based scripts
- Local discovery doesn't require any authentication

## License

MIT License - See LICENSE file for details

## Contributing

Pull requests welcome! Please:
1. Keep credentials out of code
2. Test with multiple device types
3. Update documentation as needed