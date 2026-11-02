# ADR 0011: date document manifests no earlier than their exact attachment bytes

- Status: accepted — owner-approved option A on 2026-11-02
- Date: 2026-11-02
- Related: ADR 0002; ADR 0009; manifests `bok-outlook-2026-05-ko`, `bok-outlook-2026-05-en`,
  `bok-outlook-2025-11-ko`, and `bok-outlook-2025-11-en`; benchmark pairs `kv-core-doc-01` and
  `kv-core-both-01`
- Amends: only how Bank of Korea document manifests establish `published_on`; ADR 0009's rights
  ruling is unchanged and no accepted ADR is superseded

## Context

A `SourceManifest` binds one exact byte sequence through `content_sha256`, and its
`published_on` records when that source became available. The two May 2026 outlook manifests
(2026-07-28) and the November 2025 Korean manifest (2026-11-02) took `published_on` from the
registration date on the official landing page.

While drafting `kv-core-doc-02` on 2026-11-02, the embedded PDF metadata showed that the hashed
bytes were created after those registration dates:

| Manifest | Landing registration | PDF created / modified (KST) | Publisher-stated date |
| --- | --- | --- | --- |
| `bok-outlook-2026-05-ko` | 2026-05-28 | 2026-06-09 / 2026-06-09 | Korean report "published on June 12, 2026" (English edition, page 3) |
| `bok-outlook-2026-05-en` | 2026-06-30 | 2026-07-06 / 2026-07-06 | "Published on June 30, 2026" (last page) |
| `bok-outlook-2025-11-ko` | 2025-11-27 | 2025-12-08 / 2026-03-31 | Korean report "published on December 12, 2025" (English edition, page 3) |
| `bok-outlook-2025-11-en` | 2026-01-22 | 2026-01-22 / 2026-01-22 | — |

The Bank of Korea evidently replaces attachments after a post is registered. The registration date
dates the post, not the bytes the manifest hashes. No public web-archive capture exists for these
attachment URLs. The project's own first captures, on 2026-07-28 for the May 2026 edition and
2026-11-02 for the November 2025 edition, are the only provable upper bounds.

The approved pair `kv-core-doc-01` used the registration dates as its cutoffs (2026-05-28 for
Korean, 2026-06-30 for English). Both precede the creation of the bytes its evidence cites, which
conflicts with the rule that an `as_of` evidence packet may not include a source published after
its cutoff. `kv-core-both-01` uses 2026-07-09, after both files were created, and is unaffected.

## Decision

1. A document manifest's `published_on` must be no earlier than the exact hashed bytes can have
   existed. It is the latest of the landing-page registration date, the PDF's embedded creation
   and modification dates, and any date the publisher states for that edition.
2. `publication_date_basis` is `publisher_metadata` when a publisher statement or registration
   date sets that latest date, and `content_date` when the PDF's embedded metadata sets it. The
   notes cite every input.
3. Correct three manifests in place; dates only move later, and bytes, hashes, URLs, and rights
   are unchanged:
   - `bok-outlook-2026-05-ko`: 2026-05-28 to 2026-06-12 (`publisher_metadata`);
   - `bok-outlook-2026-05-en`: 2026-06-30 to 2026-07-06 (`content_date`);
   - `bok-outlook-2025-11-ko`: 2025-11-27 to 2026-03-31 (`content_date`).
   `bok-outlook-2025-11-en` keeps 2026-01-22, which its embedded dates confirm. This follows ADR
   0009's precedent of correcting document manifests in place; no harvester snapshot is touched.
4. A benchmark record anchored to these bytes needs an `as_of` on or after the corrected date.
   `kv-core-doc-01` moves to 2026-06-12 (Korean) and 2026-07-06 (English), including the dates in
   its questions, and counts as approved again only after a new named review.
5. Embedded dates are lower bounds on byte existence, not proof of posting. This residual
   uncertainty is accepted and disclosed; the first captures remain the provable upper bounds.
6. Before recording `published_on` for any later document manifest, check the embedded PDF dates
   and publisher statements as well as the landing page.

## Alternatives considered

- **Use the project's first capture dates (option B):** rejected. It is the strictest bound, but it
  would move `kv-core-both-01` past the CLI ledger's completeness frontier and void its gold.
- **Keep the registration dates as content-availability dates (option C):** rejected because the
  manifests bind exact bytes and the evidence rule forbids post-cutoff sources.
- **Add a new `PublicationDateBasis` value:** rejected as an unnecessary public-schema change;
  the existing values cover both cases.

## Consequences

- Three manifests move later. The November 2025 Korean edition becomes eligible only from
  2026-03-31, after the February 2026 outlook, so questions over it must name the November 2025
  edition explicitly.
- `kv-core-doc-01` changes its cutoffs and question dates and is re-reviewed.
- `kv-core-both-01` is unchanged; its English pre-release negative test moves to 2026-07-05.
- Documentation that recorded the old dates is corrected or annotated.

## Revisit triggers

- A public archive or publisher record proves an earlier availability for the exact bytes.
- The Bank of Korea replaces an attachment again, which requires a new manifest.
- A document source without embedded dates is added.
