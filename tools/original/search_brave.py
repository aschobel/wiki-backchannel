#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path


ENDPOINT = "https://api.search.brave.com/res/v1/web/search"


def load_key(env_path: Path) -> str:
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("BRAVE_SEARCH_API="):
            return line.split("=", 1)[1].strip().strip("'\"")
    raise RuntimeError("BRAVE_SEARCH_API is not present")


def main() -> int:
    if len(sys.argv) != 4:
        raise SystemExit("usage: search_brave.py ENV_FILE QUERY_FILE OUTPUT_DIR")

    key = load_key(Path(sys.argv[1]))
    query_file = Path(sys.argv[2])
    output_dir = Path(sys.argv[3])
    output_dir.mkdir(parents=True, exist_ok=True)
    queries = [line.strip() for line in query_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    results = []

    for index, query in enumerate(queries, start=1):
        parameters = urllib.parse.urlencode({"q": query, "count": 20, "safesearch": "off"})
        request = urllib.request.Request(
            f"{ENDPOINT}?{parameters}",
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "identity",
                "X-Subscription-Token": key,
                "User-Agent": "WikiIntrusionDefensiveArchive/1.0",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
        result_path = output_dir / f"{index:04d}.json"
        result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for rank, item in enumerate(payload.get("web", {}).get("results", []), start=1):
            results.append(
                {
                    "query_index": index,
                    "query": query,
                    "rank": rank,
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "description": item.get("description", ""),
                    "result_file": result_path.name,
                }
            )
        if index != len(queries):
            time.sleep(1.1)

    (output_dir / "results.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in results),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
