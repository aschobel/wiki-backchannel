# Redactions and release boundaries

This release is a curated derivative of a larger local acquisition. The original case directory was not modified to prepare it.

## Included unchanged

- Selected byte ranges from the publisher-redacted revision corpus, including full bodies of the small Microlink and renderer probes.
- Six decoded payload byte strings. Decoding changes representation; it does not make them original HTTP response bodies.
- Short, relevant byte ranges from two later captured pages.
- Fifteen original researcher-written scripts, copied byte for byte.

## Explicit transformations

- Three Power BI excerpt files replace backend IPv4 addresses with `[REDACTED: IPv4 endpoint]`. These are infrastructure-address omissions, not a claim that those addresses identify victims. Each affected file records original and published excerpt hashes in the evidence index.
- Long cumulative pages are excerpted using source line hunks. Selection is recorded as byte ranges; omitted surrounding text is not silently represented as a complete page.
- Actor metrics omit the large copied URL inventory, and general corpus metrics omit the original decoded-preview sections. Source paths in these outputs are normalized. The original analyzer scripts remain unchanged.
- HTML and JavaScript artifacts use `.txt` or JSON containers. Renaming does not sanitize their contents; consumers must continue treating them as untrusted evidence.

## Not distributed

The full 2.8 GB acquisition, raw application logs containing full visitor IP addresses, acquisition request headers, cookies or session material, the local credential file, unreviewed mirror pages, and unrelated human traffic are excluded. The `.env` file was not read or copied during publication preparation. No live acquisition queue was resumed.

We also do not republish the publisher's complete archive or article. The report links to the original source and includes limited evidence selections necessary to substantiate the analysis. This package does not grant permission to redistribute third-party material under a new license.

Review included text inspection, searches for secret-like values and full addresses, decoding the bundled encoded strings, and verifying every published artifact against its declared transformation. This is a scoped review, not a guarantee that arbitrary future additions will be safe to publish.
