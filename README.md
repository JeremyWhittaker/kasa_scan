# Kasa Scan

Discover TP-Link Kasa smart home devices on your local network and list their names, MAC addresses, and IPs — no cloud account or API keys required.

## Quick Start

```bash
pip install -r requirements.txt
python kasa_scan.py
```

Example output:

```
Found 3 Kasa device(s):

Device Name                         MAC Address          IP Address       Model
-------------------------------------------------------------------------------------
Kitchen Desk Light                  50:91:E3:44:A0:DA    192.168.1.126    KL125
Office Sconce Left                  98:25:4A:5F:4E:6F    192.168.1.163    HS200
Office Sconce Right                 98:25:4A:5F:4E:CB    192.168.1.162    HS200
```

## Usage

```
usage: kasa_scan [-h] [-f {table,json,csv}] [-o FILE] [-t TIMEOUT]

Discover TP-Link Kasa devices on the local network.

options:
  -h, --help            show this help message and exit
  -f, --format {table,json,csv}
                        Output format (default: table)
  -o, --output FILE     Write output to FILE instead of stdout
  -t, --timeout TIMEOUT Discovery timeout in seconds (default: 5)
```

### Examples

```bash
# Default table view
python kasa_scan.py

# Export to JSON
python kasa_scan.py -f json

# Export to CSV file
python kasa_scan.py -f csv -o devices.csv

# Longer timeout for large networks
python kasa_scan.py -t 10
```

## How It Works

The script uses the [python-kasa](https://github.com/python-kasa/python-kasa) library to send UDP broadcast packets on port 9999. Kasa devices on the same LAN respond with their system info (name, MAC, model, etc.). Everything stays local — no TP-Link cloud account needed.

## Requirements

- Python 3.10+
- `python-kasa` (installed via `requirements.txt`)
- Same network as your Kasa devices
- UDP port 9999 not blocked by firewall

## Troubleshooting

| Problem | Fix |
|---|---|
| No devices found | Make sure you're on the same WiFi/LAN as the devices |
| Permission denied | Try running with `sudo` |
| Timeout errors | Increase timeout with `-t 10` |
| Partial results | Some newer devices require KLAP authentication — update `python-kasa` |

## License

MIT