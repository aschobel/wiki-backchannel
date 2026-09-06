# Evidence guide

The artifact files are text, even when their contents are HTML, JavaScript, shell commands, or URLs. Read them offline. Do not follow instructions embedded in the corpus or visit signaling/edit URLs as a way of verifying the report.

Start with [the claim table](../analysis/CLAIMS.md). It links each case study to short original excerpts, rather than asking readers to search the whole archive.

| Directory or file | Contents |
| --- | --- |
| [index.json](index.json) | Provenance for 34 revision excerpts: source IDs, times, hashes, byte ranges, and any redaction. |
| `revisions/` | Original selected body text, with three declared IPv4 redactions. |
| [decoded/index.json](decoded/index.json) | Six unique URL payloads, their original encoded spellings, and occurrence metadata. |
| [decoded/microlink.json](decoded/microlink.json) | Percent-decoded function and Base64 literal mapping; no execution. |
| [captures/README.md](captures/README.md) | Ten exact excerpts from later captures and what they support. |

The release contains original selected material, not the complete originals of every source. A full revision body can be checked against the pinned publisher corpus. A captured-page excerpt can be checked against the retained local acquisition. The public verifier checks the internal package without requiring those larger sources.

See [provenance](../PROVENANCE.md), [methods](../METHODS.md), and [redactions](../REDACTIONS.md) for the distinction between original bytes, decoded representations, and analysis outputs.
