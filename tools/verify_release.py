#!/usr/bin/env python3
"""Verify release bytes, evidence provenance, decodes and local document links offline."""
import argparse
import base64
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
IP = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(rel):
    return json.loads((ROOT / rel).read_text())


def check(condition, message):
    if not condition:
        raise SystemExit('FAIL: ' + message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', type=Path, help='Optionally verify against the original local acquisition.')
    args = parser.parse_args()
    manifest = ROOT / 'SHA256SUMS'
    check(manifest.exists(), 'missing SHA256SUMS')
    covered = set()
    for line in manifest.read_text().splitlines():
        expected, rel = line.split('  ', 1)
        p = ROOT / rel
        check(p.resolve().is_relative_to(ROOT), 'manifest path outside repository')
        check(p.is_file() and not p.is_symlink(), 'missing or symlinked file: ' + rel)
        check(sha(p.read_bytes()) == expected, 'checksum: ' + rel)
        covered.add(rel)
    actual = {str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file()
              and not any(part in {'.git', '__pycache__', 'reproduced'} for part in p.relative_to(ROOT).parts)
              and p.name not in {'SHA256SUMS', '.DS_Store'}}
    check(actual == covered, 'unmanifested or missing release files: ' + str(actual ^ covered))

    index = read_json('evidence/index.json')
    rows = None
    if args.case:
        corpus = args.case / 'acquisition/reconstructed/revisions.jsonl'
        check(sha(corpus.read_bytes()) == '60df4a515178230aa952d9f64f6215aea4bd95ab2f05e31e484cf9b887e3f793', 'corpus hash')
        rows = {r['rev_id']: r for r in map(json.loads, corpus.read_text().splitlines())}
    for item in index:
        public = (ROOT / item['file']).read_bytes()
        check(sha(public) == item['published_sha256'], item['file'])
        if not item['redactions']:
            check(sha(public) == item['source_excerpt_sha256'], 'unchanged excerpt ' + item['file'])
        if rows:
            r = rows[item['rev_id']]
            encoding = {'ascii': 'ascii', 'utf8': 'utf-8', 'latin1': 'latin1'}[r['body_encoding']]
            body = r['body'].encode(encoding)
            check(sha(body) == item['source_body_sha256'], 'source body ' + item['rev_id'])
            a, b = item['source_byte_range']
            excerpt = body[a:b]
            check(sha(excerpt) == item['source_excerpt_sha256'], 'source excerpt ' + item['file'])
            expected = IP.sub('[REDACTED: IPv4 endpoint]', excerpt.decode(encoding)).encode(encoding)
            check(expected == public, 'redaction transform ' + item['file'])

    for item in read_json('evidence/captures/index.json'):
        public = (ROOT / item['file']).read_bytes()
        check(sha(public) == item['published_sha256'], item['file'])
        if args.case:
            body = (args.case/item['source_path']).read_bytes()
            check(sha(body) == item['source_sha256'], 'capture source ' + item['file'])
            a, b = item['source_byte_range']
            check(body[a:b] == public, 'capture selection ' + item['file'])

    for item in read_json('evidence/decoded/index.json'):
        public = (ROOT/'evidence/decoded'/(item['sha256']+'.txt')).read_bytes()
        check(sha(public) == item['sha256'] and len(public) == item['bytes'], 'decoded-byte hash')
        for occurrence in item['occurrences']:
            token = unquote(occurrence['encoded_text'])
            check(base64.b64decode(token + '=' * (-len(token) % 4), validate=True) == public, 'Base64 round trip')
            if rows:
                r = rows[occurrence['rev_id']]
                check(occurrence['encoded_text'] in r['body'], 'encoded spelling missing from source')
                check(r['body_sha256'] == occurrence['source_body_sha256'], 'decoded occurrence source hash')
    microlink = read_json('evidence/decoded/microlink.json')
    for item in microlink['decoded_literals']:
        check(base64.b64decode(item['encoded'], validate=True).decode() == item['decoded'], 'Microlink literal')
    check([x['decoded'] for x in microlink['decoded_literals'][:2]] == ['POST', 'application/json'], 'Microlink request interpretation')

    for item in read_json('analysis/original-tools.json'):
        data = (ROOT/item['path']).read_bytes()
        check(sha(data) == item['sha256'], 'original script hash')
        if args.case:
            check((args.case/item['source_path']).read_bytes() == data, 'original script copy')

    for p in ROOT.rglob('*.md'):
        # Only Markdown links are checked; evidence URLs and code examples are not fetched.
        text = re.sub(r'```.*?```', '', p.read_text(), flags=re.S)
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', text):
            if re.match(r'https?://|mailto:', target):
                continue
            name, _, anchor = target.partition('#')
            dest = (p.parent/unquote(name)).resolve() if name else p
            check(dest.is_relative_to(ROOT) and dest.is_file(), 'local link ' + str(p.relative_to(ROOT)) + ': ' + target)
            if anchor and dest.suffix == '.md':
                headings = re.findall(r'^#+\s+(.+)$', dest.read_text(), re.M)
                slugs = {re.sub(r'[^\w\- ]', '', h.lower()).replace(' ', '-') for h in headings}
                check(anchor in slugs, 'anchor: ' + target)
    print(f'PASS: {len(covered)} release files; {len(index)} revision excerpts; 6 decoded payloads; '
          'capture excerpts, original scripts, and local document links verified.'
          + (' Original local sources also verified.' if args.case else ''))


if __name__ == '__main__':
    main()
