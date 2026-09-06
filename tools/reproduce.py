#!/usr/bin/env python3
"""Recompute the published metrics offline from the pinned original revision corpus."""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('revisions', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = args.revisions.read_bytes()
    assert hashlib.sha256(data).hexdigest() == '60df4a515178230aa952d9f64f6215aea4bd95ab2f05e31e484cf9b887e3f793'
    args.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        results = {}
        for script, extra, key in [
            ('analyze_c2_patterns.py', [], 'c2'),
            ('analyze_state_encoding.py', [], 'county'),
            ('profile_actor_labels.py', ['AgentOJUnit', 'AgentOJUnitLinks', 'AgentOJUnitFix'], 'actor')]:
            dest = Path(tmp) / (key + '.json')
            subprocess.run([sys.executable, str(ROOT/'tools/original'/script), str(args.revisions),
                            *extra, '--output', str(dest)], check=True)
            results[key] = json.loads(dest.read_text())
            results[key]['source'] = 'revisions.jsonl (SHA-256 pinned in PROVENANCE.md)'
        c2 = results['c2']
        for key in list(c2):
            if key.startswith('decoded_'):
                del c2[key]
        actor = results['actor']
        # Retain the complete 39-event metadata timeline, without its large copied URL inventory.
        del actor['combined']['urls']
        rows = [json.loads(line) for line in data.splitlines()]
        daily = Counter(r['time'][:10] for r in rows)
        wiki = Counter(r['wiki'] for r in rows)
        c2['revisions_by_day'] = dict(sorted(daily.items()))
        c2['revisions_by_wiki'] = dict(sorted(wiki.items()))
        for key, name in [('c2', 'corpus-metrics.json'), ('county', 'county-metrics.json'),
                          ('actor', 'agentojunit-profile.json')]:
            (args.output/name).write_text(json.dumps(results[key], indent=2, ensure_ascii=False)+'\n')
    print('Recomputed corpus, county-cluster, and AgentOJUnit metrics offline.')


if __name__ == '__main__':
    main()
