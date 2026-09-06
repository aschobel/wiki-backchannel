#!/usr/bin/env python3

import argparse
import html
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.links.append(href)


def extract_page_ids(path):
    parser = LinkParser()
    parser.feed(path.read_text(encoding="latin-1"))
    page_ids = set()

    for raw_href in parser.links:
        href = html.unescape(raw_href)
        if not href.startswith("wiki.cgi?"):
            continue

        query = href.split("?", 1)[1]
        if "=" not in query:
            page_ids.add(query)
            continue

        params = parse_qs(urlsplit(href).query, encoding="latin-1")
        if params.get("action") == ["browse"] and "id" in params:
            page_ids.update(params["id"])

    return page_ids


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--shards-dir", type=Path, required=True)
    parser.add_argument("--shards", type=int, default=6)
    args = parser.parse_args()

    instances = {
        "dse": 150,
        "fractal": 120,
        "probier": 120,
    }
    urls = set()
    counts = {}

    for instance, days in instances.items():
        source_paths = [
            args.raw_dir / f"{instance}-spx.html",
            args.raw_dir / f"{instance}-recentchanges.html",
        ]
        page_ids = set()
        for source_path in source_paths:
            page_ids.update(extract_page_ids(source_path))

        base_url = f"https://www.wikiservice.at/{instance}/wiki.cgi"
        urls.add(f"{base_url}?action=spx")
        urls.add(f"{base_url}?action=browse&id=RecentChanges&days={days}")
        for page_id in page_ids:
            encoded_id = quote(page_id, safe="/%", encoding="latin-1")
            urls.add(f"{base_url}?action=browse&id={encoded_id}")
            urls.add(f"{base_url}?action=browse&diff=4&id={encoded_id}")
        counts[instance] = len(page_ids)

    ordered_urls = sorted(urls)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(ordered_urls) + "\n", encoding="utf-8")

    args.shards_dir.mkdir(parents=True, exist_ok=True)
    shard_lines = [[] for _ in range(args.shards)]
    for index, url in enumerate(ordered_urls):
        shard_lines[index % args.shards].append(url)
    for index, lines in enumerate(shard_lines):
        (args.shards_dir / f"urls-{index:02d}.txt").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )

    print(f"URLs: {len(ordered_urls)}")
    for instance, count in counts.items():
        print(f"{instance} page IDs: {count}")
    for index, lines in enumerate(shard_lines):
        print(f"shard {index:02d}: {len(lines)}")


if __name__ == "__main__":
    main()
