#!/usr/bin/env python3
import collections
import json
import re
import sys
from pathlib import Path


TOKEN_RE = re.compile(r"\b(?:OpenAI|Agent)[A-Za-z0-9_-]{4,}\b")


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: build_actor_candidates.py RECONSTRUCTED_DIR OUTPUT_TSV")

    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    counts: collections.Counter[tuple[str, str]] = collections.Counter()

    for filename in ("revisions.jsonl", "pages.jsonl", "events.jsonl"):
        path = source / filename
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                record = json.loads(line)
                for field in ("name", "label", "page_id", "page_key"):
                    value = record.get(field)
                    if not isinstance(value, str):
                        continue
                    for token in TOKEN_RE.findall(value):
                        counts[(token, field)] += 1
                body = record.get("body")
                if isinstance(body, str):
                    for token in TOKEN_RE.findall(body):
                        counts[(token, "body")] += 1

    totals: collections.Counter[str] = collections.Counter()
    fields: dict[str, set[str]] = collections.defaultdict(set)
    for (token, field), count in counts.items():
        totals[token] += count
        fields[token].add(field)

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as stream:
        stream.write("identifier\tcount\tfields\n")
        for token, count in sorted(totals.items(), key=lambda item: (-item[1], item[0])):
            stream.write(f"{token}\t{count}\t{','.join(sorted(fields[token]))}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
