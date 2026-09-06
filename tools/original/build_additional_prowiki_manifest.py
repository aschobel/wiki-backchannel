#!/usr/bin/env python3

import html
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit


CASE_ROOT = Path(__file__).resolve().parent.parent
MIRROR_ROOT = CASE_ROOT / "acquisition" / "hn-candidates" / "mirror"
OUTPUT = CASE_ROOT / "manifests" / "additional-prowiki-pages.txt"
SHARDS_DIR = CASE_ROOT / "manifests" / "additional-prowiki-shards"


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)


def extract_page_ids(paths):
    page_ids = set()
    for path in paths:
        parser = LinkParser()
        parser.feed(path.read_text(encoding="latin-1"))
        for raw_href in parser.links:
            href = html.unescape(raw_href)
            if not href.startswith("wiki.cgi?"):
                continue
            query = href.split("?", 1)[1]
            if "=" not in query:
                page_ids.add(query)
                continue
            params = parse_qs(urlsplit(href).query, encoding="latin-1")
            if params.get("action") in (["browse"], ["rc"]) and "id" in params:
                page_ids.update(params["id"])
    return page_ids


def main():
    sites = {
        "wiki4d": {
            "base": "https://prowiki.org/wiki4d/wiki.cgi",
            "paths": [
                MIRROR_ROOT / "prowiki.org" / "wiki4d" / "wiki.cgi?action=spx",
                MIRROR_ROOT
                / "prowiki.org"
                / "wiki4d"
                / "wiki.cgi?action=rc&days=365&all=1",
            ],
        },
        "gruender": {
            "base": "https://www.wikiservice.at/gruender/wiki.cgi",
            "paths": [
                MIRROR_ROOT
                / "www.wikiservice.at"
                / "gruender"
                / "wiki.cgi?action=spx",
                MIRROR_ROOT
                / "www.wikiservice.at"
                / "gruender"
                / "wiki.cgi?action=rc&days=365&all=1",
            ],
        },
    }

    urls = set()
    for name, site in sites.items():
        page_ids = extract_page_ids(site["paths"])
        for page_id in page_ids:
            encoded_id = quote(page_id, safe="/%", encoding="latin-1")
            urls.add(f"{site['base']}?action=browse&id={encoded_id}")
            urls.add(f"{site['base']}?action=browse&diff=4&id={encoded_id}")
        print(f"{name}: {len(page_ids)} page IDs")

    ordered_urls = sorted(urls)
    OUTPUT.write_text("\n".join(ordered_urls) + "\n", encoding="utf-8")
    SHARDS_DIR.mkdir(parents=True, exist_ok=True)
    shards = [[] for _ in range(4)]
    for index, url in enumerate(ordered_urls):
        shards[index % len(shards)].append(url)
    for index, lines in enumerate(shards):
        (SHARDS_DIR / f"urls-{index:02d}.txt").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )
    print(f"URLs: {len(urls)}")


if __name__ == "__main__":
    main()
