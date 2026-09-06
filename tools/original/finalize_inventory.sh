#!/bin/sh
set -eu

case_root=$(cd "${1:-.}" && pwd)
manifest="$case_root/manifests/ALL-SHA256SUMS"
temporary_manifest="$manifest.tmp"

cd "$case_root"
find . -type f \
  ! -path './manifests/ALL-SHA256SUMS' \
  ! -path './manifests/ALL-SHA256SUMS.sha256' \
  ! -path './manifests/ALL-SHA256SUMS.tmp' \
  -print0 \
  | LC_ALL=C sort -z \
  | xargs -0 shasum -a 256 > "$temporary_manifest"
mv "$temporary_manifest" "$manifest"

shasum -a 256 "$manifest" > "$case_root/manifests/ALL-SHA256SUMS.sha256"
