#!/usr/bin/env python3
"""
kasa-scan — Discover, monitor, and control TP-Link Kasa smart home devices.

Subcommands:
  scan       Discover devices on the network (default if omitted)
  on         Turn a device on by name or IP
  off        Turn a device off by name or IP
  toggle     Toggle a device by name or IP
  watch      Live-updating device monitor
  baseline   Save current device list for diff comparison
  diff       Compare current devices to saved baseline
"""

import argparse
import asyncio
import csv
import io
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from kasa import Discover

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DATA_DIR = Path.home() / ".kasa_scan"
DEVICES_CSV = DATA_DIR / "devices.csv"
SCAN_LOG = DATA_DIR / "scan_log.csv"
BASELINE_FILE = DATA_DIR / "baseline.json"


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe(obj, attr, default=None):
    """Get an attribute, returning *default* on any error or None value."""
    try:
        val = getattr(obj, attr, default)
        return val if val is not None else default
    except Exception:
        return default


def _clean_type(raw: str) -> str:
    """DeviceType.Plug → Plug"""
    return raw.replace("DeviceType.", "")


def _get_rssi(dev) -> int | None:
    try:
        si = getattr(dev, "sys_info", None) or {}
        return si.get("rssi")
    except Exception:
        return None


def _get_firmware(dev) -> str | None:
    try:
        hi = getattr(dev, "hw_info", None) or {}
        return hi.get("sw_ver")
    except Exception:
        return None


def _get_energy(dev) -> dict:
    """Return energy metrics for devices with an emeter."""
    energy: dict = {
        "power_w": None,
        "voltage_v": None,
        "current_a": None,
        "total_kwh": None,
    }
    try:
        if not getattr(dev, "has_emeter", False):
            return energy
        rt = dev.emeter_realtime
        if isinstance(rt, dict):
            # Some firmware reports milliwatts, some watts
            energy["power_w"] = rt.get("power_mw", rt.get("power"))
            if energy["power_w"] is not None and "power_mw" in rt:
                energy["power_w"] = round(energy["power_w"] / 1000, 2)
            energy["voltage_v"] = rt.get("voltage_mv", rt.get("voltage"))
            if energy["voltage_v"] is not None and "voltage_mv" in rt:
                energy["voltage_v"] = round(energy["voltage_v"] / 1000, 1)
            energy["current_a"] = rt.get("current_ma", rt.get("current"))
            if energy["current_a"] is not None and "current_ma" in rt:
                energy["current_a"] = round(energy["current_a"] / 1000, 3)
            energy["total_kwh"] = rt.get("total_wh", rt.get("total"))
            if energy["total_kwh"] is not None and "total_wh" in rt:
                energy["total_kwh"] = round(energy["total_kwh"] / 1000, 3)
        else:
            energy["power_w"] = getattr(rt, "power", None)
            energy["voltage_v"] = getattr(rt, "voltage", None)
            energy["current_a"] = getattr(rt, "current", None)
            energy["total_kwh"] = getattr(rt, "total", None)
    except Exception:
        pass
    return energy


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

async def discover_devices(
    timeout: int = 5,
    target_ip: str | None = None,
    include_energy: bool = False,
) -> list[dict]:
    """Discover Kasa devices and return enriched info dicts."""

    if target_ip:
        try:
            dev = await Discover.discover_single(target_ip, timeout=timeout)
            found = {target_ip: dev}
        except Exception as e:
            print(f"Error reaching {target_ip}: {e}", file=sys.stderr)
            return []
    else:
        found = await Discover.discover(timeout=timeout)

    devices: list[dict] = []

    for ip, dev in found.items():
        try:
            await dev.update()
        except Exception:
            pass

        info: dict = {
            "name": _safe(dev, "alias", "Unknown"),
            "mac": _safe(dev, "mac", "Unknown"),
            "ip": ip,
            "model": _safe(dev, "model", "Unknown"),
            "type": _clean_type(str(_safe(dev, "device_type", "Unknown"))),
            "is_on": _safe(dev, "is_on"),
            "rssi": _get_rssi(dev),
            "brightness": _safe(dev, "brightness"),
            "firmware": _get_firmware(dev),
        }

        if include_energy:
            info.update(_get_energy(dev))

        devices.append(info)

        try:
            await dev.disconnect()
        except Exception:
            pass

    return sorted(devices, key=lambda d: (d["name"] or "").lower())


# ---------------------------------------------------------------------------
# Device control
# ---------------------------------------------------------------------------

async def _find_device(name_or_ip: str, timeout: int = 5):
    """Locate a single device by IP address or partial name match."""

    # IP address?
    parts = name_or_ip.split(".")
    if len(parts) == 4 and all(p.isdigit() for p in parts):
        try:
            dev = await Discover.discover_single(name_or_ip, timeout=timeout)
            await dev.update()
            return dev
        except Exception as e:
            print(f"Could not reach {name_or_ip}: {e}", file=sys.stderr)
            return None

    # Name search — scan the network and match
    found = await Discover.discover(timeout=timeout)
    needle = name_or_ip.lower()
    matches: list[tuple[str, object]] = []

    for ip, dev in found.items():
        try:
            await dev.update()
        except Exception:
            pass
        alias = (_safe(dev, "alias") or "").lower()
        if needle in alias:
            matches.append((ip, dev))

    # Disconnect non-matches
    for ip, dev in found.items():
        if not any(ip == m[0] for m in matches):
            try:
                await dev.disconnect()
            except Exception:
                pass

    if not matches:
        print(f"No device matching '{name_or_ip}' found.", file=sys.stderr)
        return None

    if len(matches) > 1:
        print(f"Multiple devices match '{name_or_ip}':", file=sys.stderr)
        for ip, dev in matches:
            print(f"  {_safe(dev, 'alias', 'Unknown')} ({ip})", file=sys.stderr)
            try:
                await dev.disconnect()
            except Exception:
                pass
        print("Be more specific.", file=sys.stderr)
        return None

    return matches[0][1]


async def control_device(name_or_ip: str, action: str, timeout: int = 5) -> None:
    dev = await _find_device(name_or_ip, timeout=timeout)
    if dev is None:
        sys.exit(1)

    alias = _safe(dev, "alias", dev.host)
    try:
        if action == "on":
            await dev.turn_on()
            await dev.update()
            print(f"✓ {alias} → ON")
        elif action == "off":
            await dev.turn_off()
            await dev.update()
            print(f"✓ {alias} → OFF")
        elif action == "toggle":
            if _safe(dev, "is_on", False):
                await dev.turn_off()
                await dev.update()
                print(f"✓ {alias} → OFF")
            else:
                await dev.turn_on()
                await dev.update()
                print(f"✓ {alias} → ON")
    except Exception as e:
        print(f"✗ Failed to {action} {alias}: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        try:
            await dev.disconnect()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

_STATUS_FIELDS = [
    "name", "mac", "ip", "model", "type",
    "is_on", "rssi", "brightness", "firmware",
]
_ENERGY_FIELDS = ["power_w", "voltage_v", "current_a", "total_kwh"]


def _fmt(val) -> str:
    if val is None:
        return "—"
    if isinstance(val, bool):
        return "ON" if val else "OFF"
    if isinstance(val, float):
        return f"{val:.1f}"
    return str(val)


def print_table(devices: list[dict], energy: bool = False) -> None:
    """Pretty-print devices as an aligned table."""
    cols = [
        ("Device Name", "name", 30),
        ("MAC", "mac", 18),
        ("IP Address", "ip", 16),
        ("Model", "model", 10),
        ("State", "is_on", 5),
        ("RSSI", "rssi", 5),
    ]
    if energy:
        cols += [
            ("Watts", "power_w", 7),
            ("Volts", "voltage_v", 6),
            ("Amps", "current_a", 6),
            ("kWh", "total_kwh", 8),
        ]

    header = "  ".join(f"{lbl:<{w}}" for lbl, _, w in cols)
    print(header)
    print("─" * len(header))
    for d in devices:
        row = "  ".join(f"{_fmt(d.get(k)):<{w}}" for _, k, w in cols)
        print(row)


def to_json(devices: list[dict]) -> str:
    return json.dumps(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "device_count": len(devices),
            "devices": devices,
        },
        indent=2,
    )


def to_csv_string(devices: list[dict], energy: bool = False) -> str:
    fields = _STATUS_FIELDS + (_ENERGY_FIELDS if energy else [])
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(devices)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Running CSV
# ---------------------------------------------------------------------------

def save_running_csv(devices: list[dict]) -> None:
    """Overwrite ~/.kasa_scan/devices.csv with latest snapshot and append to
    the historical scan log."""
    _ensure_data_dir()
    ts = datetime.now(timezone.utc).isoformat()

    has_energy = any(d.get("power_w") is not None for d in devices)
    fields = _STATUS_FIELDS + (_ENERGY_FIELDS if has_energy else [])

    # Latest snapshot (overwrite)
    with open(DEVICES_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["timestamp"] + fields, extrasaction="ignore")
        w.writeheader()
        for d in devices:
            w.writerow({"timestamp": ts, **d})

    # Append to history log
    write_header = not SCAN_LOG.exists() or SCAN_LOG.stat().st_size == 0
    with open(SCAN_LOG, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["timestamp"] + fields, extrasaction="ignore")
        if write_header:
            w.writeheader()
        for d in devices:
            w.writerow({"timestamp": ts, **d})


# ---------------------------------------------------------------------------
# Filter / Sort
# ---------------------------------------------------------------------------

def filter_devices(
    devices: list[dict],
    name_filter: str | None = None,
    type_filter: str | None = None,
) -> list[dict]:
    result = devices
    if name_filter:
        n = name_filter.lower()
        result = [d for d in result if n in d["name"].lower()]
    if type_filter:
        t = type_filter.lower()
        result = [d for d in result if t in d["type"].lower()]
    return result


def sort_devices(devices: list[dict], key: str) -> list[dict]:
    return sorted(devices, key=lambda d: str(d.get(key, "")).lower())


# ---------------------------------------------------------------------------
# Diff / baseline
# ---------------------------------------------------------------------------

def save_baseline(devices: list[dict]) -> None:
    _ensure_data_dir()
    data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "devices": devices,
    }
    BASELINE_FILE.write_text(json.dumps(data, indent=2))
    print(f"Baseline saved ({len(devices)} devices) → {BASELINE_FILE}")


def load_baseline() -> dict | None:
    if not BASELINE_FILE.exists():
        return None
    return json.loads(BASELINE_FILE.read_text())


def print_diff(current: list[dict], baseline: dict) -> None:
    bl = {d["mac"]: d for d in baseline["devices"]}
    cur = {d["mac"]: d for d in current}

    new_devs = [d for mac, d in cur.items() if mac not in bl]
    missing = [d for mac, d in bl.items() if mac not in cur]
    ip_changes = [
        (bl[mac], cur[mac])
        for mac in cur
        if mac in bl and cur[mac]["ip"] != bl[mac]["ip"]
    ]
    name_changes = [
        (bl[mac], cur[mac])
        for mac in cur
        if mac in bl and cur[mac]["name"] != bl[mac]["name"]
    ]

    print(f"Baseline : {baseline['timestamp']}  ({len(bl)} devices)")
    print(f"Current  : {datetime.now(timezone.utc).isoformat()}  ({len(cur)} devices)")
    print()

    if not any([new_devs, missing, ip_changes, name_changes]):
        print("No changes detected.")
        return

    if new_devs:
        print(f"  + {len(new_devs)} NEW device(s):")
        for d in new_devs:
            print(f"    + {d['name']}  {d['mac']}  {d['ip']}")
        print()

    if missing:
        print(f"  − {len(missing)} MISSING device(s):")
        for d in missing:
            print(f"    − {d['name']}  {d['mac']}  was {d['ip']}")
        print()

    if ip_changes:
        print(f"  ~ {len(ip_changes)} IP change(s):")
        for old, new_d in ip_changes:
            print(f"    ~ {new_d['name']}: {old['ip']} → {new_d['ip']}")
        print()

    if name_changes:
        print(f"  ~ {len(name_changes)} name change(s):")
        for old, new_d in name_changes:
            print(f"    ~ {old['name']} → {new_d['name']}  ({new_d['mac']})")


# ---------------------------------------------------------------------------
# Watch mode
# ---------------------------------------------------------------------------

async def watch_loop(
    timeout: int = 5,
    interval: int = 5,
    energy: bool = False,
) -> None:
    print(f"Watching Kasa devices every {interval}s  (Ctrl-C to stop)\n")
    try:
        while True:
            devices = await discover_devices(
                timeout=timeout, include_energy=energy,
            )
            os.system("clear" if os.name != "nt" else "cls")
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"kasa-scan watch — {ts}  (every {interval}s, Ctrl-C to stop)")
            print(f"Found {len(devices)} device(s)\n")
            if devices:
                print_table(devices, energy=energy)
                save_running_csv(devices)
            await asyncio.sleep(interval)
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nStopped.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="kasa-scan",
        description="Discover, monitor, and control TP-Link Kasa smart home devices.",
    )
    sub = p.add_subparsers(dest="command")

    # ── scan ──────────────────────────────────────────────────────────────
    s = sub.add_parser("scan", help="Discover devices on the network (default)")
    s.add_argument("-f", "--format", choices=["table", "json", "csv"], default="table")
    s.add_argument("-o", "--output", metavar="FILE")
    s.add_argument("-t", "--timeout", type=int, default=5)
    s.add_argument("--filter", dest="name_filter", metavar="TEXT",
                   help="Show only devices whose name contains TEXT")
    s.add_argument("--type", dest="type_filter", metavar="TYPE",
                   help="Show only devices of TYPE (plug, bulb, etc.)")
    s.add_argument("--ip", dest="target_ip", metavar="IP",
                   help="Query a single device by IP")
    s.add_argument("--sort", choices=["name", "ip", "mac", "model", "type"],
                   default="name")
    s.add_argument("--energy", action="store_true",
                   help="Include energy monitoring data")

    # ── on / off / toggle ─────────────────────────────────────────────────
    for action in ("on", "off", "toggle"):
        a = sub.add_parser(action, help=f"Turn a device {action}")
        a.add_argument("device", help="Device name (partial match) or IP address")
        a.add_argument("-t", "--timeout", type=int, default=5)

    # ── watch ─────────────────────────────────────────────────────────────
    w = sub.add_parser("watch", help="Live-updating device monitor")
    w.add_argument("-i", "--interval", type=int, default=5,
                   help="Refresh interval in seconds (default: 5)")
    w.add_argument("-t", "--timeout", type=int, default=5)
    w.add_argument("--energy", action="store_true",
                   help="Include energy monitoring data")

    # ── baseline ──────────────────────────────────────────────────────────
    b = sub.add_parser("baseline", help="Save current state for diff comparison")
    b.add_argument("-t", "--timeout", type=int, default=5)

    # ── diff ──────────────────────────────────────────────────────────────
    d = sub.add_parser("diff", help="Compare current state to saved baseline")
    d.add_argument("-t", "--timeout", type=int, default=5)

    return p


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    cmd = args.command or "scan"

    # ── scan (default) ────────────────────────────────────────────────────
    if cmd == "scan":
        timeout = getattr(args, "timeout", 5)
        target_ip = getattr(args, "target_ip", None)
        energy = getattr(args, "energy", False)
        name_filter = getattr(args, "name_filter", None)
        type_filter = getattr(args, "type_filter", None)
        sort_key = getattr(args, "sort", "name")
        fmt = getattr(args, "format", "table")
        output = getattr(args, "output", None)

        devices = asyncio.run(
            discover_devices(timeout=timeout, target_ip=target_ip,
                             include_energy=energy)
        )
        if not devices:
            print("No Kasa devices found on the network.", file=sys.stderr)
            sys.exit(1)

        devices = filter_devices(devices, name_filter, type_filter)
        if sort_key != "name":
            devices = sort_devices(devices, sort_key)

        # Always save running CSV
        save_running_csv(devices)

        if fmt == "json":
            text = to_json(devices)
        elif fmt == "csv":
            text = to_csv_string(devices, energy=energy)
        else:
            print(f"\nFound {len(devices)} Kasa device(s):\n")
            print_table(devices, energy=energy)
            print(f"\n📄 {DEVICES_CSV}")
            return

        if output:
            Path(output).write_text(text)
            print(f"Wrote {len(devices)} devices → {output}")
        else:
            print(text)

    # ── on / off / toggle ─────────────────────────────────────────────────
    elif cmd in ("on", "off", "toggle"):
        asyncio.run(control_device(args.device, cmd, timeout=args.timeout))

    # ── watch ─────────────────────────────────────────────────────────────
    elif cmd == "watch":
        asyncio.run(watch_loop(
            timeout=args.timeout,
            interval=args.interval,
            energy=getattr(args, "energy", False),
        ))

    # ── baseline ──────────────────────────────────────────────────────────
    elif cmd == "baseline":
        devices = asyncio.run(discover_devices(timeout=args.timeout))
        if not devices:
            print("No devices found.", file=sys.stderr)
            sys.exit(1)
        save_baseline(devices)

    # ── diff ──────────────────────────────────────────────────────────────
    elif cmd == "diff":
        bl = load_baseline()
        if bl is None:
            print("No baseline found. Run 'kasa-scan baseline' first.",
                  file=sys.stderr)
            sys.exit(1)
        devices = asyncio.run(discover_devices(timeout=args.timeout))
        if not devices:
            print("No devices found.", file=sys.stderr)
            sys.exit(1)
        print_diff(devices, bl)


if __name__ == "__main__":
    main()
