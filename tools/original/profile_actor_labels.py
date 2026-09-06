#!/usr/bin/env python3
import argparse
import collections
import json
import re
import statistics
import urllib.parse
from datetime import datetime
from pathlib import Path


URL_PATTERN = re.compile(r"https?://[^\s\[\]<>\"']+", re.IGNORECASE)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("revision_index", type=Path)
    parser.add_argument("labels", nargs="+")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def parse_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def extract_urls(body):
    for match in URL_PATTERN.finditer(body):
        yield match.group(0).rstrip(".,;:)")


def main():
    args = parse_args()
    target_labels = set(args.labels)
    revisions = []
    domain_counts = collections.Counter()
    url_counts = collections.Counter()

    with args.revision_index.open(encoding="utf-8") as source:
        for line in source:
            revision = json.loads(line)
            if revision.get("label") not in target_labels:
                continue
            revisions.append(revision)
            for url in extract_urls(revision.get("body", "")):
                hostname = urllib.parse.urlsplit(url).hostname
                if hostname:
                    domain_counts[hostname.lower()] += 1
                    url_counts[url] += 1

    revisions.sort(key=lambda item: item["time"])
    times = [parse_time(item["time"]) for item in revisions]
    intervals = [
        (current - previous).total_seconds()
        for previous, current in zip(times, times[1:])
    ]

    labels = {}
    for label in sorted(target_labels):
        matches = [item for item in revisions if item["label"] == label]
        labels[label] = {
            "revision_count": len(matches),
            "page_count": len({item["page_id"] for item in matches}),
            "ip16_count": len({item.get("ip16") for item in matches}),
            "first_seen": matches[0]["time"] if matches else None,
            "last_seen": matches[-1]["time"] if matches else None,
            "pages": sorted({item["page_id"] for item in matches}),
            "ip16_values": sorted({item.get("ip16") for item in matches}),
        }

    report = {
        "source": str(args.revision_index),
        "labels": labels,
        "combined": {
            "revision_count": len(revisions),
            "page_count": len({item["page_id"] for item in revisions}),
            "ip16_count": len({item.get("ip16") for item in revisions}),
            "first_seen": revisions[0]["time"] if revisions else None,
            "last_seen": revisions[-1]["time"] if revisions else None,
            "median_interarrival_seconds": statistics.median(intervals) if intervals else None,
            "minimum_interarrival_seconds": min(intervals) if intervals else None,
            "domains": [
                {"domain": domain, "occurrences": count}
                for domain, count in domain_counts.most_common()
            ],
            "urls": [
                {"url": url, "occurrences": count}
                for url, count in url_counts.most_common()
            ],
            "timeline": [
                {
                    "time": item["time"],
                    "label": item["label"],
                    "ip16": item.get("ip16"),
                    "page_id": item["page_id"],
                    "change_summary": item.get("change_summary"),
                    "body_sha256": item.get("body_sha256"),
                }
                for item in revisions
            ],
        },
    }

    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
