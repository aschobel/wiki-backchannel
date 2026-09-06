# Release verification

Verification performed September 5, 2026, against the pinned local case.

| Check | Result and scope |
| --- | --- |
| Publisher export hashes | All five expanded JSON/JSONL files match the publisher checksums listed in PROVENANCE.md. |
| Original case inventory | The inventory file hashes to `91c152708b3013318ef97074a3893c41605502674ae480ccb42dfa7c6fb7f515`. The entire 2.8 GB acquisition was not rehashed. |
| Corpus metrics | The original analyzer was rerun offline; feature counts match the preceding investigation output. |
| County-cluster metrics | Original analyzer rerun; full output matches after normalizing the source path. |
| AgentOJUnit profile | Original analyzer rerun; profile matches after declared URL-inventory omission and source-path normalization. The 39 total / 37 June 18 entries and 43-second median / 3-second minimum were checked. |
| Revision evidence | All 34 selected excerpts checked against source body hashes and byte ranges; three declared IPv4 redactions verified. |
| Base64 evidence | All six URL payloads decoded directly from corpus text; every indexed spelling verified against its decoded bytes. Microlink literals decoded without execution. |
| County comparison | All three arrays exactly match the corresponding values in another encoded object within the corpus. |
| Capture provenance | The two source response bodies match the retained WARC after dechunking; all ten excerpt byte ranges match the retained bodies. |
| Original scripts | Fifteen script copies match their retained source bytes and hashes. |
| Python files | Syntax compiled without executing acquisition scripts or embedded evidence. |
| Publication review | Scanned release text for private-key markers, common credential formats, full IPv4 addresses, email addresses, home-directory paths, and sensitive-header patterns; no matches in the scanned release. This is a scoped heuristic review. |
| Package integrity | SHA256SUMS covers release files; verifier checks listed and unlisted files. |
| Local citations | Relative Markdown links and heading anchors checked by the offline verifier. |

Run `python3 tools/verify_release.py` from the repository root to repeat public-package checks. Add `--case /path/to/wiki-intrusion-20260904` to verify against retained local source files. The original-source check requires the private local case, which is not distributed.

No claim of successful historical JavaScript execution, Microlink POST execution, deployment attribution, or durable agent persistence was added on the strength of these checks. They verify the evidence and analysis within the stated scope.
