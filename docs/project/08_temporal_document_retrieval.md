# Temporal document retrieval baseline

Status: implemented offline on 2026-07-28.

## Purpose

This baseline retrieves Korean or English document passages that were public by a question's
`as_of` date. It is the documentary counterpart to the fail-closed data-vintage resolver: a later
report must not affect the evidence packet for an earlier question.

The implementation lives in `src/sovereignlab/retrieval/temporal.py`. It reuses
`SourceManifest` 2.0.0 for document provenance and `EvidenceLocator` for page, section, or fragment
references. These are internal retrieval types, not an additional public JSON Schema contract.

## Safety order

For each query, the implementation performs these operations in this order:

1. Select only manifests whose language equals the query language and whose `published_on` is on or
   before `as_of`.
2. Select only chunks bound to those eligible manifest IDs.
3. Build corpus frequencies and average document length from those eligible chunks.
4. Compute deterministic BM25-style lexical scores.
5. Return positive-scoring passages in stable score/source/chunk order, limited by `top_k`.

Filtering before step 3 is mandatory. Filtering only the final results would still allow a future
document to change inverse-document-frequency values, length normalization, and ranking.

Corpus validation also fails closed when:

- a source or chunk ID is duplicated;
- a retrieval source is not a document;
- a chunk references an unknown source;
- a chunk language differs from its source manifest; or
- a chunk's recorded source hash differs from its manifest.

Queries require an explicit `ko` or `en` language, an `as_of` date, and `top_k` from 1 through 20.

## Offline fixture and regression boundary

`data/fixtures/retrieval/` contains four synthetic Korean/English manifests and six synthetic
passages. Each language has a pre-cutoff and post-cutoff release. The post-cutoff passage is
deliberately an unusually strong query match.

Tests compare retrieval from the full corpus with retrieval from a copy in which future documents
were physically removed. The complete result objects, including scores, must be equal. Tests also
cover inclusive publication dates, language isolation, empty/no-overlap queries, result limits, and
every corpus-binding rejection.

No official report, extracted provider text, network request, paid embedding, OCR, or model call was
used for this work unit.

## Deliberate limitations

This is a reproducible lexical baseline, not the final hybrid retriever. Korean contiguous
two-character features provide a small amount of particle tolerance, but there is no morphological
analysis, semantic embedding, reranker, OCR, or query expansion. Those additions must preserve the
same filter-before-index/statistics/scoring rule and require a separate smoke test before any paid
operation.

Before a real document body or extracted text is committed, the exact publication's redistribution
basis and attribution must be documented. The next work unit should verify that basis and commit
the first real metadata-only document manifest pair before authoring additional core drafts.
