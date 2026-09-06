# Methods and reproducibility

## Scope

This is a follow-up to the reconstructed corpus published at [collusion.wiki](https://collusion.wiki/). The local investigation preserved that export and additional public responses on September 5, 2026 UTC. The case directory's September 4 date reflects the investigator's local Pacific date at the beginning of collection.

The report is based on static evidence. Publication preparation did not replay embedded request URLs, execute decoded JavaScript, send counter signals, edit any incident wiki, or resume prior acquisition queues. Fresh browsing for preparation was limited to source context and Microlink's official documentation, to check the interpretation of its function parameter.

## Daybreak Blue and investigator tooling

Daybreak Blue assisted the preceding investigation with corpus triage, pattern analysis, Base64 decoding, script generation, and interpretation. The retained scripts and notes are the practical record of that work. This release was prepared with Codex assistance, including rereading selected original revisions, rerunning the three principal offline analyzers, independently decoding the published examples, narrowing unsupported wording, and assembling the evidence package.

The retained case material does not contain a complete signed session transcript, exact model snapshot identifiers for every step, or an exhaustive tool-call log. This methods statement credits the workflow without implying that all claims were independently checked by a human or that every request can be reconstructed from model logs. Daybreak Blue's involvement in research is unrelated to attribution of the incident writers.

## Input and extraction

The main input is the publisher's `revisions.jsonl`, SHA-256:

```text
60df4a515178230aa952d9f64f6215aea4bd95ab2f05e31e484cf9b887e3f793
```

The complete input is not bundled here. Obtain it from the [original publisher's downloads](https://collusion.wiki/explorer/download). Verify it before analysis. The scripts refuse a different input hash rather than silently treating an updated export as equivalent.

`tools/build_evidence.py` selects report-relevant revisions. Small probe bodies are retained in full; most longer pages contribute only newly inserted or replaced line ranges specified by the publisher's diff hunks. The index records byte offsets into the full body, its hash, the original excerpt hash, and the published excerpt hash. UTF-8, ASCII, and Latin-1 source encodings are handled explicitly. Each excerpt is therefore tied to a revision rather than to the current contents of a live wiki page.

Three excerpt files contain an additional redaction of public backend IPv4 addresses. This does not remove the bypass mechanism; it avoids distributing concrete endpoint addresses that are unnecessary to the interpretation. The full unmodified source remains in the original local corpus. [Redaction details](REDACTIONS.md).

The six Base64 URL payloads are decoded directly from corpus strings, not copied from a prior analyzer's preview. `evidence/decoded/index.json` retains each encoded spelling and occurrence. Microlink query parameters are parsed as a URL query before Base64-decoding the quoted literals. The resulting function is written as JSON text and never evaluated.

## Reproduce the metrics

From the repository root, with Python 3.10 or later and the pinned input already available:

```sh
python3 tools/verify_release.py
python3 tools/reproduce.py /path/to/revisions.jsonl --output reproduced
diff analysis/corpus-metrics.json reproduced/corpus-metrics.json
diff analysis/county-metrics.json reproduced/county-metrics.json
diff analysis/agentojunit-profile.json reproduced/agentojunit-profile.json
```

These commands are offline. `reproduce.py` calls the original analyzers with the current Python interpreter and temporary output files. It removes the large copied URL inventory from the actor profile, removes the original decoder output from the general metrics in favor of the separately verified evidence directory, and normalizes the source filename. Those are declared publication transformations, not changes to the counting algorithms.

For holders of the original local acquisition directory, reproduce the selected evidence into an empty directory:

```sh
python3 tools/build_evidence.py /path/to/wiki-intrusion-20260904 --output reproduced-evidence
python3 tools/verify_release.py --case /path/to/wiki-intrusion-20260904
```

`tools/extract_capture_sources.py` additionally ties the two selected captured pages to exact WARC response records and verifies their bodies after removing HTTP chunk framing. It emits only selected metadata, not cookies or complete HTTP headers.

The optional `--case` check verifies excerpts against the original corpus and captured bodies. It reads local files only. The public verifier separately checks bundled file hashes, decoded bytes, literal mappings, and Markdown link targets without the case directory.

## Original script addendum

All fifteen scripts in `tools/original/` are byte-identical copies from the retained investigation. Their hashes are in [original-tools.json](analysis/original-tools.json). They are research tools, not agent-written payloads.

| Script | Role in the original investigation |
| --- | --- |
| `analyze_c2_patterns.py` | Lexical pattern counts, coordination-page metadata, and decoding candidates. |
| `analyze_state_encoding.py` | County-cluster propagation and timing statistics. |
| `profile_actor_labels.py` | Exact-label revision timelines and URL/domain inventories. |
| `extract_outbound_artifacts.py` | Extract external artifact references and candidate pivots. |
| `build_actor_candidates.py` | Inventory candidate actor labels. |
| `summarize_public_logs.py` | Summarize public application-log records. |
| `extract_hn_links.py` | Extract links and contexts from the captured discussion. |
| `extract_paste_indexes.py` | Extract candidate paste entries from captured indexes. |
| `build_url_manifest.py` | Build the initial wiki acquisition URL inventory. |
| `build_additional_prowiki_manifest.py` | Build follow-up wiki URL inventories. |
| `search_brave.py` | Query Brave using a caller-supplied credential file. No credential is included. |
| `acquire_warc.sh` | Initial Wget WARC capture launcher. |
| `acquire_additional_prowiki.sh` | Additional wiki capture launcher. |
| `acquire_public_logs.sh` | Public application-log capture launcher. |
| `finalize_inventory.sh` | Generate a deterministic local acquisition inventory. |

The historical acquisition scripts expect the original case layout and manifests. They are included for audit, not as a recommended recrawl procedure. In particular, the initial launcher used six concurrent shards and retry behavior that encountered site rate limiting; it is not a hardened, redirect-aware allowlist client. Its manifest check alone does not establish that every redirected or prerequisite request stayed within the intended action set. Reproduction of this report requires only the offline analysis commands above.

## Limitations and corrections

- Feature matches are lexical heuristics over page names, summaries, and cumulative bodies. They overlap and are not independent commands or a validated behavioral classifier.
- Unique labels and `/16` prefixes do not identify unique people, accounts, deployments, or workers. The actor profile uses three exact labels, not every possible spelling beginning with `AgentOJUnit`.
- Short interarrival times are computed from stored timestamps. Consult `time_grade` and `uncertainty_seconds` in the index; claimed task clocks and timestamps quoted in prose are separate observations.
- The original general analyzer's decoded `first_seen` field means the first encountered row, not necessarily the chronological minimum: the input is grouped by page. This release uses the occurrence-level index rather than relying on that field for an earliest-time claim.
- The Base64 scanner is syntactic and incomplete. Six unique `/base64/` payloads describes this input and rule set. An absence of detected shellcode or encrypted payloads is not an exhaustive proof of absence.
- The county-array equality check is against a separately encoded object in the same corpus. It does not establish independent SEC provenance. Earlier notes described this more strongly; this report uses the narrower verified statement.
- Microlink request construction and the JavaScript probes are established by preserved text. Their successful execution is not established. Other reported replications and heartbeat audits remain claims made on unauthenticated public pages.
- The current Microlink documentation supports interpretation, not historical service behavior on a particular date or request.
- Live acquisition was partial and later than the principal event. Rate-limit responses, deletions, indexing gaps, and post-disclosure observer traffic limit conclusions drawn from it.
- SHA-256 identifies byte content. A matching checksum does not authenticate a writer, validate an allegation, or establish chain of custody before collection.

Checks completed for the release are listed in [VERIFICATION.md](VERIFICATION.md).
