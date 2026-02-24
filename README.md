# kasa-scan

Discover, monitor, and control TP-Link Kasa smart home devices from the command line. Everything runs locally over your LAN — no cloud account needed.

## Install

```bash
git clone https://github.com/JeremyWhittaker/kasa_scan.git
cd kasa_scan
pip install -e .
```

You can now run `kasa-scan` from anywhere. Or run directly with `python kasa_scan.py`.

## Quick Start

```bash
kasa-scan                              # scan and list all devices
kasa-scan on "office sconce"           # turn on by name (partial match)
kasa-scan off 192.168.1.163            # turn off by IP
kasa-scan toggle "kitchen"             # toggle power state
kasa-scan watch                        # live-updating monitor
```

## Commands

### `scan` (default)

Discover all Kasa devices on the network.

```bash
kasa-scan scan                         # table view (default)
kasa-scan scan --energy                # include power/voltage/current
kasa-scan scan -f json                 # JSON output
kasa-scan scan -f csv -o devices.csv   # export CSV to file
kasa-scan scan --filter "office"       # filter by name
kasa-scan scan --type plug             # filter by device type
kasa-scan scan --ip 192.168.1.126      # query a single device
kasa-scan scan --sort ip               # sort by ip, mac, model, or type
kasa-scan scan -t 10                   # longer timeout for large networks
```

Example output:

```
Found 14 Kasa device(s):

Device Name                     MAC                 IP Address        Model       State  RSSI
──────────────────────────────────────────────────────────────────────────────────────────────
Dining Room Light               50:91:E3:44:A1:2B   192.168.1.110     KL125       ON     -45
Kitchen Desk Light              50:91:E3:44:A0:DA   192.168.1.126     KL125       OFF    -52
Office Sconce Left              98:25:4A:5F:4E:6F   192.168.1.163     HS200       ON     -38
Office Sconce Right             98:25:4A:5F:4E:CB   192.168.1.162     HS200       ON     -41
```

### `on` / `off` / `toggle`

Control devices by name (partial, case-insensitive) or IP address.

```bash
kasa-scan on "office sconce left"      # exact name
kasa-scan off "kitchen"                # partial match
kasa-scan toggle 192.168.1.126         # by IP
```

If multiple devices match a partial name, you'll be asked to be more specific.

### `watch`

Live-updating display that rescans at a set interval.

```bash
kasa-scan watch                        # refresh every 5 seconds
kasa-scan watch -i 10                  # refresh every 10 seconds
kasa-scan watch --energy               # include power draw
```

### `baseline` / `diff`

Save a snapshot of your devices, then compare later to detect new, missing, or changed devices.

```bash
kasa-scan baseline                     # save current state
# ... time passes, devices change ...
kasa-scan diff                         # compare to saved baseline
```

Example diff output:

```
Baseline : 2026-02-24T20:00:00+00:00  (14 devices)
Current  : 2026-02-25T08:30:00+00:00  (15 devices)

  + 1 NEW device(s):
    + Guest Room Lamp  A0:B1:C2:D3:E4:F5  192.168.1.180

  ~ 1 IP change(s):
    ~ Kitchen Desk Light: 192.168.1.126 → 192.168.1.130
```

## Running CSV Log

Every scan automatically saves results to `~/.kasa_scan/`:

| File | Contents |
|---|---|
| `devices.csv` | Latest snapshot (overwritten each scan) |
| `scan_log.csv` | Append-only history with timestamps |

## Energy Monitoring

Devices with built-in energy meters (HS110, HS300, KP115, etc.) report real-time power data when you use the `--energy` flag:

```bash
kasa-scan scan --energy
kasa-scan watch --energy
```

Columns: **Watts**, **Volts**, **Amps**, **kWh** (cumulative).

## Requirements

- Python 3.10+
- Same LAN as your Kasa devices
- UDP port 9999 not blocked by firewall

## Troubleshooting

| Problem | Fix |
|---|---|
| No devices found | Confirm you're on the same WiFi/LAN |
| Permission denied | Try `sudo kasa-scan` |
| Timeout / partial results | Increase timeout: `-t 10` |
| Authentication errors | Some newer devices need KLAP auth — update python-kasa |

## License

MIT