#!/usr/bin/env python3
import argparse
import collections
import datetime as dt
import json
import re
import statistics
from pathlib import Path


COUNTY_CLUSTER = re.compile(
    r"county\.json|regCF_county|SEC county|Massachusetts Named Values|Mass county",
    re.I,
)
OBVIOUS_COUNTY_NAME = re.compile(r"sec|county|mass|map|invest|regcf", re.I)
BROADCAST = "Agent0 SEC county data bridge fresh"


def parse_time(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def iso(value):
    return value.isoformat().replace("+00:00", "Z")


def main():
    parser = argparse.ArgumentParser(
        description="Quantify the SEC Massachusetts county-data propagation cluster."
    )
    parser.add_argument("revisions", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    pages = set()
    labels = set()
    ip16s = set()
    times = []
    creations = 0
    label_counts = collections.Counter()
    minute_counts = collections.Counter()
    wiki_counts = collections.Counter()
    actor_page = collections.defaultdict(
        lambda: {"records": 0, "ip16s": set(), "times": []}
    )
    broadcast_pages = set()
    broadcast_labels = set()
    broadcast_ip16s = set()
    broadcast_revisions = 0
    matching_revisions = 0

    with args.revisions.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            page_id = record.get("page_id") or ""
            body = record.get("body") or ""
            summary = record.get("change_summary") or ""
            if not COUNTY_CLUSTER.search("\n".join((page_id, body, summary))):
                continue

            matching_revisions += 1
            pages.add(page_id)
            wiki_counts[record.get("wiki") or page_id.partition("/")[0]] += 1
            if record.get("seq") == 1:
                creations += 1
            if record.get("label"):
                labels.add(record["label"])
                label_counts[record["label"]] += 1
            if record.get("ip16"):
                ip16s.add(record["ip16"])
            timestamp = parse_time(record["time"])
            times.append(timestamp)
            minute_counts[timestamp.replace(second=0, microsecond=0)] += 1

            if record.get("label"):
                actor = actor_page[(page_id, record["label"])]
                actor["records"] += 1
                actor["times"].append(timestamp)
                if record.get("ip16"):
                    actor["ip16s"].add(record["ip16"])

            if BROADCAST.lower() in body.lower():
                broadcast_revisions += 1
                broadcast_pages.add(page_id)
                if record.get("label"):
                    broadcast_labels.add(record["label"])
                if record.get("ip16"):
                    broadcast_ip16s.add(record["ip16"])

    top_actor_pages = []
    for (page_id, label), stats in actor_page.items():
        sorted_times = sorted(stats["times"])
        gaps = [
            (later - earlier).total_seconds()
            for earlier, later in zip(sorted_times, sorted_times[1:])
        ]
        top_actor_pages.append(
            {
                "page_id": page_id,
                "label": label,
                "revisions": stats["records"],
                "unique_ip16_prefixes": len(stats["ip16s"]),
                "first_time": iso(sorted_times[0]),
                "last_time": iso(sorted_times[-1]),
                "median_gap_seconds": round(statistics.median(gaps), 2)
                if gaps
                else None,
            }
        )
    top_actor_pages.sort(
        key=lambda item: (item["unique_ip16_prefixes"], item["revisions"]),
        reverse=True,
    )

    result = {
        "source": str(args.revisions),
        "cluster_pattern": COUNTY_CLUSTER.pattern,
        "matching_revisions": matching_revisions,
        "unique_pages": len(pages),
        "page_creations": creations,
        "pages_without_obvious_county_name": sum(
            not OBVIOUS_COUNTY_NAME.search(page_id) for page_id in pages
        ),
        "unique_labels": len(labels),
        "unique_ip16_prefixes": len(ip16s),
        "first_time": iso(min(times)) if times else None,
        "last_time": iso(max(times)) if times else None,
        "revisions_by_wiki": dict(wiki_counts.most_common()),
        "peak_minutes": [
            {"minute": iso(minute), "revisions": count}
            for minute, count in minute_counts.most_common(10)
        ],
        "top_labels": [
            {"label": label, "revisions": count}
            for label, count in label_counts.most_common(20)
        ],
        "top_same_label_page_ip_spread": top_actor_pages[:20],
        "broadcast_phrase": {
            "text": BROADCAST,
            "matching_revisions": broadcast_revisions,
            "unique_pages": len(broadcast_pages),
            "unique_labels": len(broadcast_labels),
            "unique_ip16_prefixes": len(broadcast_ip16s),
        },
    }
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
