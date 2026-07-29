# Temporal document retrieval fixtures

These JSONL files are entirely synthetic. They contain no downloaded report text, provider
observations, or confidential material.

- `source_manifests.jsonl` defines Korean and English document releases on both sides of a
  synthetic `as_of` cutoff.
- `document_chunks.jsonl` defines small passages bound to those manifests by `source_id`,
  `language`, and `source_sha256`.

The post-cutoff passages deliberately contain unusually strong query matches. Offline regression
tests verify that filtering happens before corpus statistics and scoring, so adding those future
passages cannot change either the eligible matches or their scores.

The typed execution baseline freezes these files as
`synthetic-temporal-retrieval-corpus-v1`, descriptor SHA-256
`823117ee29a191bc306843e44ccd9d37e063db79cc87e15dcb7f2a11f5b5bf7e`.
The descriptor binds both exact file hashes, byte sizes, record counts, and every source/chunk ID.
Do not edit the v1 inputs in place; create a new corpus ID and descriptor for a changed fixture.
