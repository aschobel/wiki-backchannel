#!/bin/zsh

set -euo pipefail

script_dir=${0:A:h}
case_root=${script_dir:h}
manifest_dir="$case_root/manifests"
warc_dir="$case_root/acquisition/warc"
mirror_dir="$case_root/acquisition/mirror"
log_dir="$case_root/acquisition/logs"
temp_dir="$case_root/acquisition/warc-tmp"

mkdir -p "$warc_dir" "$mirror_dir" "$log_dir" "$temp_dir"

if rg -n -v '^https://www\.wikiservice\.at/(dse|fractal|probier)/wiki\.cgi\?action=(browse|spx)(&|$)' "$manifest_dir/urls.txt"; then
  echo "Refusing to acquire a manifest containing a non-allowlisted URL." >&2
  exit 1
fi

acquired_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
run_id=$(date -u +%Y%m%dT%H%M%SZ)
process_ids=()

for shard_file in "$manifest_dir"/shards/urls-*.txt; do
  shard_name=${shard_file:t:r}
  mkdir -p "$mirror_dir/$run_id/$shard_name"
  wget \
    --https-only \
    --input-file="$shard_file" \
    --directory-prefix="$mirror_dir/$run_id/$shard_name" \
    --warc-file="$warc_dir/$shard_name-$run_id" \
    --warc-cdx \
    --warc-tempdir="$temp_dir" \
    --warc-header="operator: Backroom defensive research" \
    --warc-header="acquisition-start: $acquired_at" \
    --warc-header="scope: read-only dse, fractal, probier pages and diff views" \
    --no-cookies \
    --hsts-file="$case_root/manifests/wget-hsts" \
    --domains=www.wikiservice.at \
    --page-requisites \
    --timeout=30 \
    --tries=3 \
    --retry-on-http-error=429,500,502,503,504 \
    --waitretry=2 \
    --user-agent='Backroom-Defensive-Archive/1.0' \
    --no-verbose \
    --output-file="$log_dir/$shard_name-$run_id.log" &
  process_ids+=("$!")
done

overall_status=0
for process_id in "${process_ids[@]}"; do
  if ! wait "$process_id"; then
    overall_status=1
  fi
done

exit "$overall_status"
