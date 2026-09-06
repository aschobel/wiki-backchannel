# Evidence provenance

## Sources

1. **Publisher reconstruction.** [collusion.wiki report](https://collusion.wiki/) and [download page](https://collusion.wiki/explorer/download), credited in [third-party notices](THIRD_PARTY_NOTICES.md). The export manifest says it was generated at `2026-09-03T03:42:36Z`, with a write-date cut starting May 1. The saved-revision timeline is a separate population from probe events and other dates discussed by the publisher.
2. **Investigator acquisition.** Public responses collected beginning `2026-09-05T04:58:24Z`. The broad WARC pass began at `05:01:26Z`, encountered rate-limit pages around `05:05:01Z`, and was stopped. A focused AgentOJUnit pivot capture began at `06:04:56Z`. The release includes selected response-body excerpts from that focused capture.
3. **Contemporary technical reference.** [Microlink function documentation](https://github.com/microlinkhq/www/blob/master/src/content/docs/api/parameters/function.md), consulted September 5 for the semantics of the function parameter. This is not incident-period telemetry.

## Pinned source hashes

| Source | SHA-256 |
| --- | --- |
| Publisher `full-wiki-logs.zip` | `eb68aa12d26bf189d8bfc4ce47f4d8af66ae5ba7ebbadd429738297a3cbb25ae` |
| Expanded `revisions.jsonl` | `60df4a515178230aa952d9f64f6215aea4bd95ab2f05e31e484cf9b887e3f793` |
| Expanded `pages.jsonl` | `92b296170b496b836cdf5ef783bed9465d2d75db7e1a0becec1c36c8b7c42cfd` |
| Expanded `events.jsonl` | `588584295f1c4a7c3d90b04075ab151504f165ff069534d935cda08853ec28b1` |
| Expanded `labels.jsonl` | `d94aecd84baecda46344f5b8726a95a9c81e7e41a1c0969fc89a90c8906f0388` |
| Expanded `manifest.json` | `b6d53e16b5d9a6a0a98d4577238835ee7a574d7d10a8f1312330b4e626c6ba2b` |
| Original case `ALL-SHA256SUMS` inventory | `91c152708b3013318ef97074a3893c41605502674ae480ccb42dfa7c6fb7f515` |

The case inventory hash commits to the retained inventory bytes. It is not a digital signature, a hash of a single archive, or a claim that every acquisition file was reacquired or rehashed for publication. The original inventory includes local paths and is not distributed. The public package has its own relative-path [SHA256SUMS](SHA256SUMS).

## Artifact chain

For a revision excerpt:

```text
publisher ZIP → expanded revisions.jsonl → rev_id + body_sha256
             → byte range in that body → optional declared redaction
             → published excerpt SHA-256
```

For a decoded payload:

```text
revision body → encoded spelling retained in the index
              → percent decoding → Base64 decoding → decoded-byte SHA-256
```

For a captured-page excerpt:

```text
focused WARC acquisition → retained response-body mirror
                         → source-body hash + byte range → excerpt hash
```

The [revision index](evidence/index.json) records source revision IDs, timestamp grades, uncertainties, body encodings, hashes, byte offsets, redactions, and publisher explorer URLs. Offsets are zero-based, start-inclusive and end-exclusive. Excerpts that are complete small bodies are identified explicitly; otherwise they are exact selections rather than complete original pages.

The [capture index](evidence/captures/index.json) records the source response-body path, source hash, offsets, and published hash. [Capture-source metadata](evidence/captures/sources.json) identifies the retained WARC and its response timestamps. WARCs and HTTP headers are not bundled because the selected response text is sufficient for the narrow statistics claims and avoids unrelated capture contents.

Publisher-provided hashes are retained as provenance; selected source bodies and excerpts were reverified for this release. See [verification](VERIFICATION.md) for the exact scope of checks performed.
