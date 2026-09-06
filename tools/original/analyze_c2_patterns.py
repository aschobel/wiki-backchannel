#!/usr/bin/env python3
import argparse
import base64
import collections
import datetime as dt
import hashlib
import json
import re
import statistics
import urllib.parse
from pathlib import Path


FEATURES = {
    "coordination_vocabulary": re.compile(
        r"\b(coord(?:ination)?|collab(?:oration)?|relay|signal|shared poller|"
        r"ahead cohort|matching cohort|many cohorts)\b",
        re.I,
    ),
    "explicit_tasking": re.compile(
        r"\b(please (?:post|append|report|signal|relay|monitor)|"
        r"before (?:the )?(?:final )?answer|first (?:append|signal|post|get)|"
        r"post .{0,40} immediately|urgent|country first|state5-)\b",
        re.I,
    ),
    "status_or_beaconing": re.compile(
        r"\b(heartbeat|beacon|check[- ]?in|alive|awake|status|ping|poller|"
        r"countdown|monitor(?:ing)?|surviv(?:al|ed|e))\b",
        re.I,
    ),
    "timing_and_scheduling": re.compile(
        r"\b(due|deadline|eta|projected|task[- ]?clock|countdown|timer|"
        r"cadence|cooldown|seconds-to-|[+][0-9]+m)\b",
        re.I,
    ),
    "result_or_cache_sharing": re.compile(
        r"\b(confirmed|answered|exact answer|values? cached|table cached|"
        r"sequence|result|state[0-9]-|country first)\b",
        re.I,
    ),
    "external_signal_endpoint": re.compile(
        r"counterapi|webhook|requestbin|pipedream|ngrok|interactsh|"
        r"beeceptor|hookbin",
        re.I,
    ),
    "detached_process_survival": re.compile(
        r"\b(setsid|nohup|detached (?:timer|process)|background (?:container )?"
        r"beacon|children are killed|sleep\s+[0-9]+)\b",
        re.I,
    ),
    "proxy_or_fetch_bypass": re.compile(
        r"markdown\.new|md\.succ\.ai|allorigins|jqp\.vercel\.app|"
        r"proxymule|r\.jina\.ai|cors\.workers\.dev|httpbin\.org/base64",
        re.I,
    ),
    "executable_syntax": re.compile(
        r"(?:\beval\s*\(|\bexec\s*\(|<script\b|javascript:|"
        r"\bcurl\s+|\bwget\s+|\bpowershell\b|\bcmd\.exe\b|/bin/sh\b)",
        re.I,
    ),
    "controller_language": re.compile(
        r"\b(controller|operator|command(?:er)?|leader|master)\b",
        re.I,
    ),
}

COORDINATION_NAME = re.compile(
    r"heartbeat|beacon|signal|relay|coord|collab|master|leader|queue|"
    r"command|control|status|live|timing|cache|sequence",
    re.I,
)
BASE64_PATH = re.compile(
    r"(?:https?://)?[^\s\[]*?/base64/([A-Za-z0-9_%+/=-]{16,})"
)
ATOB_LITERAL = re.compile(
    r"\batob\(\s*(['\"])([A-Za-z0-9+/_=-]{4,})\1\s*\)", re.I
)
LONG_BASE64_TOKEN = re.compile(
    r"(?<![A-Za-z0-9+/_=-])([A-Za-z0-9+/_-]{40,}={0,2})(?![A-Za-z0-9+/_=-])"
)


def parse_time(value):
    if not value:
        return None
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def printable_ratio(data):
    if not data:
        return 1.0
    return sum(byte in b"\t\n\r" or 32 <= byte < 127 for byte in data) / len(data)


def decode_urlsafe(value):
    padded = value + "=" * (-len(value) % 4)
    for altchars in (None, b"-_"):
        try:
            return base64.b64decode(padded, altchars=altchars, validate=True)
        except (ValueError, base64.binascii.Error):
            continue
    return None


def add_decoded_artifact(collection, data, page_id, record):
    digest = hashlib.sha256(data).hexdigest()
    if digest in collection:
        collection[digest]["occurrences"] += 1
        collection[digest]["pages"].add(page_id)
        if record.get("label"):
            collection[digest]["labels"].add(record["label"])
        return
    try:
        decoded_text = data.decode("utf-8")
    except UnicodeDecodeError:
        decoded_text = None
    collection[digest] = {
        "sha256": digest,
        "decoded_bytes": len(data),
        "printable_ratio": round(printable_ratio(data), 4),
        "preview": data[:240].decode("utf-8", "replace"),
        "decoded_text": decoded_text,
        "occurrences": 1,
        "pages": {page_id},
        "labels": {record["label"]} if record.get("label") else set(),
        "first_seen": record.get("time"),
    }


def render_decoded(collection):
    values = []
    for item in collection.values():
        item["pages"] = sorted(item["pages"])
        item["labels"] = sorted(item["labels"])
        values.append(item)
    values.sort(
        key=lambda item: (item["occurrences"], item["decoded_bytes"]), reverse=True
    )
    return values


def main():
    parser = argparse.ArgumentParser(
        description="Measure C2-like coordination patterns without executing content."
    )
    parser.add_argument("revisions", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    feature_revisions = collections.Counter()
    feature_pages = collections.defaultdict(set)
    page_stats = collections.defaultdict(
        lambda: {"revisions": 0, "labels": set(), "ip16": set(), "times": []}
    )
    labels = set()
    ip16s = set()
    decoded = {}
    decoded_atob = {}
    decoded_structured = {}
    total = 0

    with args.revisions.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            total += 1
            page_id = record.get("page_id") or ""
            body = record.get("body") or ""
            summary = record.get("change_summary") or ""
            text = "\n".join((page_id, body, summary))

            stats = page_stats[page_id]
            stats["revisions"] += 1
            if record.get("label"):
                stats["labels"].add(record["label"])
                labels.add(record["label"])
            if record.get("ip16"):
                stats["ip16"].add(record["ip16"])
                ip16s.add(record["ip16"])
            timestamp = parse_time(record.get("time"))
            if timestamp:
                stats["times"].append(timestamp)

            for name, pattern in FEATURES.items():
                if pattern.search(text):
                    feature_revisions[name] += 1
                    feature_pages[name].add(page_id)

            path_tokens = set()
            for match in BASE64_PATH.finditer(body):
                raw = urllib.parse.unquote(match.group(1)).rstrip(".,);]}")
                path_tokens.add(raw)
                data = decode_urlsafe(raw)
                if data is None:
                    continue
                add_decoded_artifact(decoded, data, page_id, record)

            expanded_body = urllib.parse.unquote_plus(body)
            for match in ATOB_LITERAL.finditer(expanded_body):
                data = decode_urlsafe(match.group(2))
                if data is not None:
                    add_decoded_artifact(decoded_atob, data, page_id, record)

            for match in LONG_BASE64_TOKEN.finditer(expanded_body):
                raw = match.group(1)
                if raw in path_tokens:
                    continue
                data = decode_urlsafe(raw)
                if data is None or len(data) < 20 or printable_ratio(data) < 0.95:
                    continue
                try:
                    decoded_text = data.decode("utf-8").lstrip()
                except UnicodeDecodeError:
                    continue
                if not decoded_text.startswith(("{", "[")):
                    continue
                add_decoded_artifact(decoded_structured, data, page_id, record)

    coordination_pages = []
    for page_id, stats in page_stats.items():
        if not COORDINATION_NAME.search(page_id):
            continue
        times = sorted(stats["times"])
        gaps = [
            (later - earlier).total_seconds()
            for earlier, later in zip(times, times[1:])
            if later >= earlier
        ]
        coordination_pages.append(
            {
                "page_id": page_id,
                "revisions": stats["revisions"],
                "unique_labels": len(stats["labels"]),
                "unique_ip16": len(stats["ip16"]),
                "first_time": times[0].isoformat().replace("+00:00", "Z") if times else None,
                "last_time": times[-1].isoformat().replace("+00:00", "Z") if times else None,
                "median_gap_seconds": round(statistics.median(gaps), 2) if gaps else None,
            }
        )
    coordination_pages.sort(
        key=lambda item: (item["revisions"], item["unique_labels"]), reverse=True
    )

    result = {
        "source": str(args.revisions),
        "total_revisions": total,
        "unique_pages": len(page_stats),
        "unique_labels": len(labels),
        "unique_ip16_prefixes": len(ip16s),
        "features": {
            name: {
                "matching_revisions": feature_revisions[name],
                "matching_pages": len(feature_pages[name]),
            }
            for name in FEATURES
        },
        "top_coordination_named_pages": coordination_pages[:30],
        "decoded_base64_url_payloads": render_decoded(decoded),
        "decoded_atob_literals": render_decoded(decoded_atob),
        "decoded_structured_base64_tokens": render_decoded(decoded_structured),
    }
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
