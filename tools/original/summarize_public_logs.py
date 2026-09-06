#!/usr/bin/env python3

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


def field(parts, key):
    try:
        index = parts.index(key)
    except ValueError:
        return ""
    if index + 1 >= len(parts):
        return ""
    return parts[index + 1]


def ip16(ip_address):
    address = ip_address.split("#", 1)[0]
    octets = address.split(".")
    if len(octets) == 4:
        return ".".join(octets[:2])
    return address


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    sources = {
        "dse": args.case_root
        / "acquisition/public-logs/mirror/20260905T050537Z/dse",
        "fractal": args.case_root
        / "acquisition/public-logs/mirror/20260905T050537Z/fractal",
        "probier": args.case_root
        / "acquisition/public-logs/mirror/20260905T050537Z/probier",
        "gruender": args.case_root / "acquisition/gruender-wiki4d/mirror",
    }

    summary = {}
    daily_writes = defaultdict(Counter)

    for site, source_dir in sources.items():
        total_requests = 0
        write_requests = 0
        full_ips = set()
        ip16s = set()
        names = Counter()
        monthly_writes = Counter()

        for path in sorted(source_dir.glob("log_26*")):
            month = path.name.removeprefix("log_")
            with path.open("r", encoding="latin-1", errors="replace") as log_file:
                for line in log_file:
                    total_requests += 1
                    if "action=form_edit" not in line or "Save=" not in line:
                        continue

                    parts = line.rstrip("\n").split("|")
                    write_requests += 1
                    monthly_writes[month] += 1
                    ip_address = field(parts, "IP")
                    if ip_address:
                        full_ips.add(ip_address)
                        ip16s.add(ip16(ip_address))
                    name = field(parts, "NAME")
                    if name:
                        names[name] += 1
                    timestamp = field(parts, "TS")
                    if timestamp.isdigit():
                        day = datetime.fromtimestamp(
                            int(timestamp), timezone.utc
                        ).strftime("%Y-%m-%d")
                        daily_writes[site][day] += 1

        summary[site] = {
            "total_requests": total_requests,
            "write_requests": write_requests,
            "unique_full_ips": len(full_ips),
            "unique_ip16s": len(ip16s),
            "unique_names": len(names),
            "writes_by_log_month": dict(sorted(monthly_writes.items())),
            "top_names": [
                {"name": name, "requests": count}
                for name, count in names.most_common(20)
            ],
        }

    output = {
        "method": "Counts application-log requests containing action=form_edit and Save=; IPs are aggregated and not emitted.",
        "sites": summary,
        "daily_write_requests": {
            site: dict(sorted(counts.items()))
            for site, counts in sorted(daily_writes.items())
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
