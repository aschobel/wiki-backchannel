#!/usr/bin/env python3

import argparse
import html
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


class ContentParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.text_parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(html.unescape(href))

    def handle_data(self, data):
        self.text_parts.append(data)


def walk(item):
    yield item
    for child in item.get("children", []):
        yield from walk(child)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--links", type=Path, required=True)
    parser.add_argument("--domains", type=Path, required=True)
    args = parser.parse_args()

    root = json.loads(args.input.read_text(encoding="utf-8"))
    rows = []
    domain_counts = {}

    for item in walk(root):
        content = item.get("text") or item.get("story_text") or ""
        content_parser = ContentParser()
        content_parser.feed(content)
        context = " ".join(" ".join(content_parser.text_parts).split())
        for url in content_parser.links:
            if not url.startswith(("http://", "https://")):
                continue
            domain = urlsplit(url).netloc.lower()
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
            rows.append(
                (
                    str(item.get("id", "")),
                    item.get("author") or "",
                    domain,
                    url,
                    context,
                )
            )

    args.links.parent.mkdir(parents=True, exist_ok=True)
    with args.links.open("w", encoding="utf-8") as output:
        output.write("item_id\tauthor\tdomain\turl\tcontext\n")
        for row in rows:
            output.write("\t".join(value.replace("\t", " ") for value in row) + "\n")

    with args.domains.open("w", encoding="utf-8") as output:
        output.write("count\tdomain\n")
        for domain, count in sorted(
            domain_counts.items(), key=lambda pair: (-pair[1], pair[0])
        ):
            output.write(f"{count}\t{domain}\n")

    print(f"comments/items: {sum(1 for _ in walk(root))}")
    print(f"links: {len(rows)}")
    print(f"domains: {len(domain_counts)}")


if __name__ == "__main__":
    main()
