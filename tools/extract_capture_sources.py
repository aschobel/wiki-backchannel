#!/usr/bin/env python3
"""Extract selected WARC metadata and verify dechunked bodies against local mirrors."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dechunk(data):
    stream = io.BytesIO(data)
    result = bytearray()
    while True:
        size = int(stream.readline().strip().split(b';', 1)[0], 16)
        if size == 0:
            return bytes(result)
        chunk = stream.read(size)
        if len(chunk) != size or stream.read(2) != b'\r\n':
            raise ValueError('Invalid HTTP chunk framing')
        result.extend(chunk)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    pivot = args.case / 'acquisition/agentojunit-pivots/20260905T060456Z'
    warc = pivot / 'agentojunit-pivots-20260905T060456Z.warc.gz'
    records = []
    with gzip.open(warc, 'rb') as stream:
        while True:
            line = stream.readline()
            if not line:
                break
            if not line.startswith(b'WARC/'):
                continue
            headers = {}
            while True:
                line = stream.readline()
                if line in (b'\r\n', b'\n', b''):
                    break
                key, _, value = line.partition(b':')
                headers[key.decode().lower()] = value.strip().decode()
            payload = stream.read(int(headers['content-length']))
            uri = headers.get('warc-target-uri', '')
            if headers.get('warc-type') != 'response' or not any(s in uri for s in ['maallraw260618', 'MYLABI']):
                continue
            head, _, body = payload.partition(b'\r\n\r\n')
            if b'transfer-encoding: chunked' not in head.lower():
                raise ValueError('Unexpected transfer encoding in selected response')
            decoded = dechunk(body)
            filename = 'maallraw260618+' if 'maallraw260618' in uri else 'index.php?search_in=all&sort_by=timestamp&sort_order=desc&page=1077&perpage=15&total_pages=8547&search='
            mirror = pivot/'mirror'/filename
            if decoded != mirror.read_bytes():
                raise ValueError('WARC response differs from mirror')
            entry = {k: headers.get(k) for k in ['warc-record-id', 'warc-date', 'warc-target-uri', 'warc-payload-digest']}
            entry.update({'http_status_line': head.splitlines()[0].decode(),
                          'transfer_encoding': 'chunked', 'transfer_encoded_body_sha256': sha(body),
                          'decoded_response_body_sha256': sha(decoded),
                          'mirror_source_path': str(mirror.relative_to(args.case)),
                          'mirror_matches_decoded_warc_body': True})
            records.append(entry)
    if len(records) != 2:
        raise ValueError('Expected exactly two selected responses')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({'source_warc': str(warc.relative_to(args.case)),
                                      'source_warc_sha256': sha(warc.read_bytes()),
                                      'records': records}, indent=2)+'\n')
    print('Verified two HTTP response bodies against the original WARC after dechunking.')


if __name__ == '__main__':
    main()
