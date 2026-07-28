# ADR 0009: classify official Bank of Korea Economic Outlook publications as reusable public data

- Status: accepted — approved by the owner on 2026-07-28
- Date: 2026-07-28
- Related: charter v2.5 §4; ADR 0004; source manifests
  `bok-outlook-2026-05-ko` and `bok-outlook-2026-05-en`
- Supersedes: only the provisional `metadata_only` conclusion for this publication family in
  commit `6db81e8` and `docs/discovery/04_bok_outlook_2026_05_manifest_log.md`

## Context

The first May 2026 bilingual document-manifest unit independently verified the official Korean and
English publication dates, attachment URLs, byte sizes, and SHA-256 values. Neither individual
landing page displayed a KOGL mark or publication-specific open-license label, so the initial
manifest commit conservatively recorded both documents as `metadata_only`.

That conclusion was incomplete because it treated the absence of a page-level KOGL label as the
end of the rights inquiry. The Bank of Korea's official
[copyright policy](https://www.bok.or.kr/portal/main/contents.do?menuNo=200228) establishes a
separate public-data branch: information published as public data under Article 19 of the Public
Data Act may be used freely without a separate procedure. It also requires Bank of Korea
attribution and disclosure when information is modified, processed, or transformed. The Bank of
Korea's
[public-data provision page](https://www.bok.or.kr/portal/main/contents.do?menuNo=200668) identifies
the Article 19 publication process and links to the provider's public-data listing.

The public portal's organization-filtered web view did not expose an individual Economic Outlook
publication-family row during the 2026-07-28 verification. That interface result is retained as a
negative finding rather than misrepresented as affirmative licence evidence. On the same date, the
owner supplied the missing source-specific classification: official Bank of Korea Economic Outlook
reports are public data covered by the Bank of Korea copyright policy and may be used without a
separate procedure. As in ADR 0004's exact producer mappings, the owner-approved classification is
recorded explicitly instead of fabricating a KOGL identifier that the publication pages do not
display.

## Decision

1. Classify the official Bank of Korea-produced `bok-economic-outlook` publication family as
   `allowed` for SovereignLab's non-commercial public-research use.
2. The approved family includes official Korean `경제전망보고서` editions and their official English
   full translations published on Bank of Korea pages. It does not authorize adjacent Bank of
   Korea publication families, unofficial translations, or material carrying a separate
   third-party copyright/source notice.
3. Permitted operations include access, local processing, extraction, transformation, attributed
   reuse, and redistribution. Every use must identify the Bank of Korea as the source and disclose
   modification, processing, or transformation when applicable.
4. Record the applicable instrument in document manifests as
   `Bank of Korea Copyright Policy (Public Data Act Article 19 public-data branch)` with the
   official copyright-policy URL. Do not label it as KOGL or another standardized licence that the
   publisher did not state.
5. Keep `rights_decision` null for these document manifests. Contract 2.0.0 reserves the typed
   series-rights reference for data/API snapshots and rejects it on document sources.
6. Correct the two May 2026 manifests from `metadata_only` to `allowed` without changing their
   capture identity, URL, publication date, retrieval timestamp, byte size, or checksum. Public Git
   history retains the provisional conclusion and this superseding correction; no history is
   rewritten.
7. Permission does not force automatic ingestion. Full PDFs and extracted full text remain outside
   Git in this work unit as a repository-scope choice. Any later committed source body or derived
   retrieval corpus must preserve attribution, transformation disclosure, provenance, and the
   separately marked third-party-material boundary.
8. The project's standing non-commercial profile remains unchanged. Any future commercial-use
   path still requires owner review before source collection or publication.

## Approval record

On 2026-07-28 the owner stated that the Bank of Korea Economic Outlook is public data that may be
used freely without a separate procedure under the Public Data Act and the Bank of Korea copyright
policy. The owner approved applying that source-family classification to the verified May 2026
Korean report and official English full translation.

## Alternatives considered

- **Retain `metadata_only` because the landing pages lack KOGL labels:** rejected because it ignores
  the Bank of Korea's separate Article 19 public-data branch and the owner's exact publication-
  family classification.
- **Invent a KOGL type:** rejected because neither landing page nor the governing policy supplies
  one.
- **Treat every Bank of Korea publication as `allowed`:** rejected because the approval is limited
  to the official Economic Outlook family and does not override separate third-party notices.
- **Commit the full PDFs in the correction unit:** rejected as unnecessary scope expansion. Rights
  classification and corpus-ingestion policy are distinct decisions.

## Consequences

- The two real May 2026 document manifests accurately record `allowed` use with attribution and
  transformation-disclosure duties.
- Benchmark drafts may rely on language-matched report content without a rights blocker, while
  publication dates remain independently enforced.
- The earlier absence-of-KOGL finding remains auditable, but it no longer drives the final rights
  state.
- Future Economic Outlook editions may reuse this family ruling only while publisher, publication
  family, governing policy, intended use, attribution duties, and third-party boundaries remain
  unchanged.

## Revisit triggers

- The Bank of Korea changes its copyright policy or public-data classification.
- An edition carries a separate licence, copyright notice, or third-party restriction.
- The project adds a commercial-use path.
- The owner narrows or withdraws the publication-family classification.
