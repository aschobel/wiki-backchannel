#!/usr/bin/env python3
"""Offline extraction from the preserved case. Never fetches or executes evidence."""
import argparse
import base64
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, parse_qs, urlsplit


SELECTION = {
    'dse/Sector61State5FastSignal': [1, 57, 62, 63, 65, 67, 68],
    'dse/DataUSAPovertyR5LiveSep13': [1, 17, 18, 19],
    'dse/Apr23CVDHorizonBeacon2025': [2, 5, 6, 7, 15],
    'dse/DataUSAStateSequenceCollab2027': [1],
    'dse/MaidsJan06R3SignalJul03': [2, 4, 8],
    'dse/OAIEquityDec30Raw': [4, 9, 11, 13],
    'fractal/TmpAcctDownloadRefsQ2A': [1, 2],
    'probier/SandBox': [3],
    'dse/AgentTempFormXYZ': [1],
    'dse/TmpFederalBridge': [2],
    'dse/TmpJan18HtmlHost987': [1],
    'dse/AgentCountyGateway991': [18],
    'dse/AgentBase64Test': [2],
    'dse/AgentBridgeViaSearchAA9901': [1],
    'dse/StartSeite': [397],
}
IP = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    case, out = args.case, args.output
    source = case / 'acquisition/reconstructed/revisions.jsonl'
    expected = '60df4a515178230aa952d9f64f6215aea4bd95ab2f05e31e484cf9b887e3f793'
    if digest(source.read_bytes()) != expected:
        raise SystemExit('Unexpected corpus hash; inspect the source before changing the pin.')
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    by_id = {r['rev_id']: r for r in rows}
    index = []
    for r in rows:
        if r['seq'] not in SELECTION.get(r['page_id'], []):
            continue
        encoding = {'ascii': 'ascii', 'utf8': 'utf-8', 'latin1': 'latin1'}[r['body_encoding']]
        body = r['body'].encode(encoding)
        assert digest(body) == r['body_sha256'], r['rev_id']
        # Preserve complete small probe bodies; otherwise extract the publisher's new-line hunks.
        full = r['page_id'] in {'fractal/TmpAcctDownloadRefsQ2A', 'dse/AgentTempFormXYZ',
                               'dse/TmpFederalBridge', 'dse/TmpJan18HtmlHost987',
                               'dse/AgentCountyGateway991', 'dse/AgentBase64Test'}
        lines = body.splitlines(keepends=True)
        ranges = [(0, len(body))] if full else [
            (sum(map(len, lines[:h['b0']])), sum(map(len, lines[:h['b1']])))
            for h in r['hunks'] if h['b1'] > h['b0']
        ]
        for i, (start, end) in enumerate(ranges, 1):
            data = body[start:end]
            if not data.strip():
                continue
            public = IP.sub('[REDACTED: IPv4 endpoint]', data.decode(encoding)).encode(encoding)
            name = r['rev_id'].replace('~', '--').replace('@', '--r') + f'--{i}.txt'
            rel = 'evidence/revisions/' + name
            (out / rel).parent.mkdir(parents=True, exist_ok=True)
            (out / rel).write_bytes(public)
            index.append({
                'file': rel, 'rev_id': r['rev_id'], 'page_id': r['page_id'],
                'time': r['time'], 'time_grade': r['time_grade'],
                'uncertainty_seconds': r['uncertainty_seconds'], 'label': r['label'],
                'body_encoding': r['body_encoding'], 'source_body_sha256': digest(body),
                'source_byte_range': [start, end], 'source_excerpt_sha256': digest(data),
                'published_sha256': digest(public), 'complete_body': full,
                'redactions': ['IPv4 endpoint'] if public != data else [],
                'source_explorer': 'https://collusion.wiki/explorer/page/' + r['page_key'],
            })
    expected_ids = {p.replace('/', '~', 1) + '@' + str(s)
                    for p, seqs in SELECTION.items() for s in seqs}
    assert {x['rev_id'] for x in index} == expected_ids
    write_json(out / 'evidence/index.json', index)

    # Re-decode the six known URL payloads from corpus bodies; do not trust prior previews.
    pattern = re.compile(r'/base64/([A-Za-z0-9_%+/=-]{16,})')
    decoded = {}
    for r in rows:
        for m in pattern.finditer(r['body']):
            token = unquote(m.group(1))
            try:
                data = base64.b64decode(token + '=' * (-len(token) % 4), validate=True)
            except ValueError:
                continue
            sha = digest(data)
            entry = decoded.setdefault(sha, {'sha256': sha, 'bytes': len(data), 'occurrences': []})
            entry['occurrences'].append({'rev_id': r['rev_id'], 'time': r['time'],
                                         'encoded_text': m.group(1),
                                         'source_body_sha256': r['body_sha256']})
            (out / 'evidence/decoded').mkdir(parents=True, exist_ok=True)
            (out / 'evidence/decoded' / (sha + '.txt')).write_bytes(data)
    assert len(decoded) == 6
    write_json(out / 'evidence/decoded/index.json', sorted(decoded.values(), key=lambda x: x['sha256']))

    r = by_id['fractal~TmpAcctDownloadRefsQ2A@2']
    url = re.search(r'\[(https://api\.microlink\.io/\?\S+) ', r['body']).group(1)
    function = parse_qs(urlsplit(url).query)['function'][0]
    tokens = re.findall(r"'([A-Za-z0-9+/]+={0,2})'", function)
    values = [base64.b64decode(t).decode() for t in tokens]
    assert values[0:2] == ['POST', 'application/json']
    write_json(out / 'evidence/decoded/microlink.json', {
        'rev_id': r['rev_id'], 'source_body_sha256': r['body_sha256'],
        'transforms': ['parse URL query with percent-decoding', 'Base64-decode quoted literals'],
        'function_text': function,
        'decoded_literals': [{'encoded': t, 'decoded': v} for t, v in zip(tokens, values)],
        'execution_status': 'not executed by this investigation; no successful response established',
    })

    # Compare with a separately encoded object in the same corpus, not an independent SEC fetch.
    start = next(r for r in rows if r['page_id'] == 'dse/StartSeite'
                 and 'eyJyZWdDRl9jb3VudHlfbWV0aG9kb2xvZ3ki' in r['body'])
    objects = []
    for token in re.findall(r'[A-Za-z0-9+/_-]{100,}={0,2}', unquote(start['body'])):
        try:
            obj = json.loads(base64.b64decode(token + '=' * (-len(token) % 4)))
        except (ValueError, UnicodeDecodeError):
            continue
        if isinstance(obj, dict) and 'regCF_county_2019' in obj:
            objects.append(obj)
    assert len(objects) == 1
    comparison = []
    for sha in sorted(decoded):
        data = (out / 'evidence/decoded' / (sha + '.txt')).read_bytes()
        if data.lstrip().startswith(b'['):
            arr = json.loads(data)
            matches = [k for k, v in objects[0].items() if v == arr]
            assert len(matches) == 1
            comparison.append({'payload_sha256': sha, 'matching_key': matches[0],
                               'exact_json_value_match': True})
    write_json(out / 'analysis/county-payload-comparison.json', {
        'comparison_rev_id': start['rev_id'], 'source_body_sha256': start['body_sha256'],
        'scope': 'Equality with a separately encoded object in the same wiki corpus; not source authentication.',
        'matches': comparison,
    })

    # Small capture extracts retain original bytes and offsets; no HTML is served.
    pivot = case / 'acquisition/agentojunit-pivots/20260905T060456Z'
    capture_index = []
    for name, filename, terms in [
        ('vanderbilt', 'maallraw260618+', [b'16153', b'id="longurl"', b'Short URL created',
                                         b'OpenAIRegCFMassBridge3002', b'collusion.wiki', b'urlquery.net']),
        ('yourls', 'index.php?search_in=all&sort_by=timestamp&sort_order=desc&page=1077&perpage=15&total_pages=8547&search=',
         [b'0', b'URL'])]:
        p = pivot / 'mirror' / filename
        data = p.read_bytes()
        offset = 0
        count = 0
        for line in data.splitlines(keepends=True):
            take = any(term in line for term in terms) if name == 'vanderbilt' else bool(
                re.search(rb'(?:0</strong>|0 URLs|0 links|0 clicks)', line))
            if take:
                count += 1
                rel = f'evidence/captures/{name}-{count:02d}.txt'
                (out / rel).parent.mkdir(parents=True, exist_ok=True)
                (out / rel).write_bytes(line)
                capture_index.append({'file': rel, 'source_path': str(p.relative_to(case)),
                                      'source_sha256': digest(data), 'source_byte_range': [offset, offset+len(line)],
                                      'published_sha256': digest(line), 'redactions': []})
            offset += len(line)
    write_json(out / 'evidence/captures/index.json', capture_index)
    print(f'Extracted {len(index)} revision excerpts, {len(decoded)} decoded URL payloads, '
          f'{len(capture_index)} capture excerpts.')


if __name__ == '__main__':
    main()
