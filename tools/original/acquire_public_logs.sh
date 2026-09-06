#!/bin/zsh

set -euo pipefail

script_dir=${0:A:h}
case_root=${script_dir:h}
manifest_dir="$case_root/manifests"
output_root="$case_root/acquisition/public-logs"
temp_dir="$case_root/acquisition/warc-tmp"
run_id=$(date -u +%Y%m%dT%H%M%SZ)
process_ids=()

mkdir -p "$output_root/mirror/$run_id" "$output_root/warc" "$output_root/logs" "$temp_dir"

for site in dse fractal probier; do
  mkdir -p "$output_root/mirror/$run_id/$site"
  wget \
    --https-only \
    --input-file="$manifest_dir/logs-$site.txt" \
    --directory-prefix="$output_root/mirror/$run_id/$site" \
    --warc-file="$output_root/warc/$site-$run_id" \
    --warc-max-size=1G \
    --warc-cdx \
    --warc-tempdir="$temp_dir" \
    --warc-header="operator: Backroom defensive research" \
    --warc-header="scope: publicly listed WikiService incident-period logs" \
    --no-cookies \
    --hsts-file="$case_root/manifests/wget-hsts-public-logs" \
    --domains=www.wikiservice.at \
    --timeout=90 \
    --tries=5 \
    --retry-on-http-error=429,500,502,503,504 \
    --waitretry=3 \
    --user-agent='Backroom-Defensive-Archive/1.0' \
    --no-verbose \
    --output-file="$output_root/logs/$site-$run_id.log" &
  process_ids+=("$!")
done

overall_status=0
for process_id in "${process_ids[@]}"; do
  if ! wait "$process_id"; then
    overall_status=1
  fi
done

exit "$overall_status"
