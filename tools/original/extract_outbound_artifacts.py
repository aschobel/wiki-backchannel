#!/usr/bin/env python3
import argparse
import collections
import json
import re
import urllib.parse
from pathlib import Path


URL = re.compile(r"https?://[^\s\[\]<>\"']+", re.I)
TRAILING = ".,;:!?)}`"
HIGH_VALUE = re.compile(
    r"(?:\.(?:json|csv|xlsx?|pdf|zip|gz|tgz|tar|js|mjs|wasm|py|sh|txt|md)"
    r"(?:[?#]|$)|/download(?:/|[?#]|$)|/files?/|querydata|conceptualschema|"
    r"api\.microlink\.io|httpbin\.org/base64|paste\.|counterapi|webhook)",
    re.I,
)
RELAY_DOMAINS = {
    "api.allorigins.win",
    "allorigins.hexlet.app",
    "api.microlink.io",
    "httpbin.org",
    "jqp.vercel.app",
    "markdown.new",
    "md.succ.ai",
    "r.jina.ai",
    "proxy.corsfix.com",
}


def clean_url(value):
    return value.rstrip(TRAILING).replace("&amp;", "&")


def decoded_variants(text, rounds=4):
    current = text
    yield current
    for _ in range(rounds):
        decoded = urllib.parse.unquote(current)
        if decoded == current:
            break
        current = decoded
        yield current


def urls_in_text(text):
    found = set()
    queue = []
    for variant in decoded_variants(text):
        for match in URL.finditer(variant):
            value = clean_url(match.group(0))
            if value not in found:
                found.add(value)
                queue.append(value)

    while queue:
        outer = queue.pop()
        for variant in decoded_variants(outer):
            try:
                parsed = urllib.parse.urlsplit(variant)
            except ValueError:
                continue
            nested_texts = [value for _, value in urllib.parse.parse_qsl(parsed.query)]
            decoded_path = urllib.parse.unquote(parsed.path)
            inner_offset = min(
                (offset for offset in (decoded_path.find("http://"), decoded_path.find("https://")) if offset >= 0),
                default=-1,
            )
            if inner_offset >= 0:
                nested_texts.append(decoded_path[inner_offset:])
            for nested_text in nested_texts:
                for match in URL.finditer(nested_text):
                    value = clean_url(match.group(0))
                    if value not in found:
                        found.add(value)
                        queue.append(value)
    return found


def captured_urls(acquisition_root):
    captured = set()
    for path in acquisition_root.rglob("*.cdx"):
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.startswith(("http://", "https://")):
                    continue
                captured.add(line.split(" ", 1)[0])
    return captured


def canonical_url(value):
    try:
        parsed = urllib.parse.urlsplit(value)
    except ValueError:
        return None
    if not parsed.netloc:
        return None
    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return None
    port = parsed.port
    netloc = hostname
    if port and not ((parsed.scheme == "http" and port == 80) or (parsed.scheme == "https" and port == 443)):
        netloc = f"{hostname}:{port}"
    return urllib.parse.urlunsplit(
        ((parsed.scheme or "https").lower(), netloc, parsed.path or "/", "", "")
    )


def main():
    parser = argparse.ArgumentParser(
        description="Extract recursively decoded outbound URLs and compare them to CDX captures."
    )
    parser.add_argument("revisions", type=Path)
    parser.add_argument("--acquisition-root", type=Path, required=True)
    parser.add_argument("--decoded-summary", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--urls-output", type=Path, required=True)
    args = parser.parse_args()

    captured = captured_urls(args.acquisition_root)
    captured_canonical = {canonical_url(url) for url in captured}
    artifacts = {}
    domain_counts = collections.Counter()

    def add(url, page_id, label, timestamp, source):
        try:
            parsed = urllib.parse.urlsplit(url)
        except ValueError:
            return
        domain = parsed.netloc.lower().split("@")[-1].split(":")[0]
        if not domain:
            return
        domain_counts[domain] += 1
        item = artifacts.setdefault(
            url,
            {
                "url": url,
                "domain": domain,
                "occurrences": 0,
                "pages": set(),
                "labels": set(),
                "first_seen": timestamp,
                "last_seen": timestamp,
                "sources": set(),
            },
        )
        item["occurrences"] += 1
        if page_id:
            item["pages"].add(page_id)
        if label:
            item["labels"].add(label)
        if timestamp and (not item["first_seen"] or timestamp < item["first_seen"]):
            item["first_seen"] = timestamp
        if timestamp and (not item["last_seen"] or timestamp > item["last_seen"]):
            item["last_seen"] = timestamp
        item["sources"].add(source)

    with args.revisions.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            for url in urls_in_text(record.get("body") or ""):
                add(
                    url,
                    record.get("page_id"),
                    record.get("label"),
                    record.get("time"),
                    "revision_body",
                )

    if args.decoded_summary:
        summary = json.loads(args.decoded_summary.read_text(encoding="utf-8"))
        for field in (
            "decoded_base64_url_payloads",
            "decoded_atob_literals",
            "decoded_structured_base64_tokens",
        ):
            for artifact in summary.get(field, []):
                for url in urls_in_text(artifact.get("decoded_text") or ""):
                    for page_id in artifact.get("pages") or [None]:
                        add(
                            url,
                            page_id,
                            None,
                            artifact.get("first_seen"),
                            field,
                        )

    rendered = []
    for url, item in artifacts.items():
        item["pages"] = sorted(item["pages"])
        item["labels"] = sorted(item["labels"])
        item["sources"] = sorted(item["sources"])
        item["captured_exact_url"] = url in captured
        item["relay_domain"] = item["domain"] in RELAY_DOMAINS
        item["high_value_reference"] = bool(HIGH_VALUE.search(url))
        rendered.append(item)
    rendered.sort(
        key=lambda item: (
            item["high_value_reference"],
            not item["captured_exact_url"],
            item["occurrences"],
        ),
        reverse=True,
    )

    canonical = {}
    for item in rendered:
        canonical_value = canonical_url(item["url"])
        if not canonical_value:
            continue
        aggregate = canonical.setdefault(
            canonical_value,
            {
                "url": canonical_value,
                "domain": item["domain"],
                "url_variants": 0,
                "occurrences": 0,
                "pages": set(),
                "relay_domain": item["relay_domain"],
                "high_value_reference": False,
            },
        )
        aggregate["url_variants"] += 1
        aggregate["occurrences"] += item["occurrences"]
        aggregate["pages"].update(item["pages"])
        aggregate["high_value_reference"] = (
            aggregate["high_value_reference"] or item["high_value_reference"]
        )
    canonical_values = []
    for item in canonical.values():
        item["pages"] = sorted(item["pages"])
        item["captured_canonical_url"] = item["url"] in captured_canonical
        canonical_values.append(item)
    canonical_values.sort(
        key=lambda item: (
            item["high_value_reference"],
            not item["captured_canonical_url"],
            item["occurrences"],
            item["url_variants"],
        ),
        reverse=True,
    )

    result = {
        "source": str(args.revisions),
        "captured_cdx_urls": len(captured),
        "unique_outbound_urls": len(rendered),
        "unique_domains": len({item["domain"] for item in rendered}),
        "exact_urls_already_captured": sum(
            item["captured_exact_url"] for item in rendered
        ),
        "high_value_references": sum(item["high_value_reference"] for item in rendered),
        "uncaptured_high_value_references": sum(
            item["high_value_reference"] and not item["captured_exact_url"]
            for item in rendered
        ),
        "canonical_resources": canonical_values,
        "top_domains_by_unique_url": [
            {"domain": domain, "urls": count}
            for domain, count in collections.Counter(
                item["domain"] for item in rendered
            ).most_common(100)
        ],
        "artifacts": rendered,
    }
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    args.urls_output.write_text(
        "\n".join(item["url"] for item in rendered) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
