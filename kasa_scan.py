#!/usr/bin/env python3
"""
kasa_scan - Discover and list TP-Link Kasa smart home devices on your local network.

Maps device names to MAC addresses and IP addresses. Supports multiple output
formats (table, JSON, CSV) for integration with other tools.
"""

import argparse
import asyncio
import csv
import io
import json
import sys
from datetime import datetime, timezone

from kasa import Discover


async def discover_devices(timeout: int = 5) -> list[dict]:
    """Discover all Kasa devices on the local network.

    Args:
        timeout: Seconds to wait for device responses.

    Returns:
        Sorted list of device dicts with keys: name, mac, ip, model, type.
    """
    found = await Discover.discover(timeout=timeout)
    devices = []

    for ip, dev in found.items():
        try:
            await dev.update()
        except Exception:
            pass  # Use whatever attributes are available pre-update

        devices.append({
            "name": getattr(dev, "alias", "Unknown"),
            "mac": getattr(dev, "mac", "Unknown"),
            "ip": ip,
            "model": getattr(dev, "model", "Unknown"),
            "type": str(getattr(dev, "device_type", "Unknown")),
        })

    return sorted(devices, key=lambda d: d["name"].lower())


def print_table(devices: list[dict]) -> None:
    """Print devices as a formatted table to stdout."""
    header = f"{'Device Name':<35} {'MAC Address':<20} {'IP Address':<16} {'Model'}"
    print(header)
    print("-" * len(header))
    for d in devices:
        print(f"{d['name']:<35} {d['mac']:<20} {d['ip']:<16} {d['model']}")


def to_json(devices: list[dict]) -> str:
    """Return devices as a JSON string."""
    return json.dumps(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "device_count": len(devices),
            "devices": devices,
        },
        indent=2,
    )


def to_csv(devices: list[dict]) -> str:
    """Return devices as a CSV string."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["name", "mac", "ip", "model", "type"])
    writer.writeheader()
    writer.writerows(devices)
    return buf.getvalue()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kasa_scan",
        description="Discover TP-Link Kasa devices on the local network.",
    )
    parser.add_argument(
        "-f", "--format",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "-o", "--output",
        metavar="FILE",
        help="Write output to FILE instead of stdout",
    )
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=5,
        help="Discovery timeout in seconds (default: 5)",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    devices = asyncio.run(discover_devices(timeout=args.timeout))

    if not devices:
        print("No Kasa devices found on the network.", file=sys.stderr)
        print("Make sure you are on the same network and UDP port 9999 is not blocked.", file=sys.stderr)
        sys.exit(1)

    # Format output
    if args.format == "json":
        output = to_json(devices)
    elif args.format == "csv":
        output = to_csv(devices)
    else:
        # For table, print directly unless writing to file
        if args.output:
            buf = io.StringIO()
            # Build table string for file output
            header = f"{'Device Name':<35} {'MAC Address':<20} {'IP Address':<16} {'Model'}"
            lines = [header, "-" * len(header)]
            for d in devices:
                lines.append(f"{d['name']:<35} {d['mac']:<20} {d['ip']:<16} {d['model']}")
            output = "\n".join(lines) + "\n"
        else:
            print(f"\nFound {len(devices)} Kasa device(s):\n")
            print_table(devices)
            return

    # Write to file or stdout
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Wrote {len(devices)} devices to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
