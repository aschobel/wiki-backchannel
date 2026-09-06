#!/bin/zsh

set -euo pipefail

script_dir=${0:A:h}
case_root=${script_dir:h}
manifest_dir="$case_root/manifests/additional-prowiki-shards"
output_root="$case_root/acquisition/additional-prowiki"
temp_dir="$case_root/acquisition/warc-tmp"
run_id=$(date -u +%Y%m%dT%H%M%SZ)
process_ids=()

mkdir -p "$output_root/mirror/$run_id" "$output_root/warc" "$output_root/logs" "$temp_dir"

for shard_file in "$manifest_dir"/urls-*.txt; do
  shard_name=${shard_file:t:r}
  mkdir -p "$output_root/mirror/$run_id/$shard_name"
  wget \
    --https-only \
    --input-file="$shard_file" \
    --directory-prefix="$output_root/mirror/$run_id/$shard_name" \
    --warc-file="$output_root/warc/$shard_name-$run_id" \
    --warc-cdx \
    --warc-tempdir="$temp_dir" \
    --warc-header="operator: Backroom defensive research" \
    --warc-header="scope: Wiki4D and GruenderWiki indexed pages and diff views" \
    --no-cookies \
    --hsts-file="$case_root/manifests/wget-hsts-additional-prowiki" \
    --domains=prowiki.org,www.wikiservice.at \
    --timeout=30 \
    --tries=3 \
    --retry-on-http-error=429,500,502,503,504 \
    --waitretry=2 \
    --user-agent='Backroom-Defensive-Archive/1.0' \
    --no-verbose \
    --output-file="$output_root/logs/$shard_name-$run_id.log" &
  process_ids+=("$!")
done

overall_status=0
for process_id in "${process_ids[@]}"; do
  if ! wait "$process_id"; then
    overall_status=1
  fi
done

exit "$overall_status"
