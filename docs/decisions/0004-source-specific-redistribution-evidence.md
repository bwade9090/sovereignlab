# ADR 0004: replace the KOGL-only harvester gate with source-specific rights evidence

- Status: accepted — approved by the owner on 2026-07-16
- Date: 2026-07-15
- Last revised: 2026-07-16 (owner approval, non-commercial boundary, and OECD interim ruling)
- Related: charter v2.2 §§4 and 7; ADR 0002; partially supersedes ADR 0003 decision 6

## Context

The original charter v2 correctly requires an owner-approved, per-series redistribution ruling
before the forward-capture harvester commits raw ECOS/KOSIS values. It assumes that each candidate series
exposes a KOGL type in its metadata. The week-1 verification spike confirmed that the APIs do not
expose such a field, but the official use guides provide the applicable rights instruments:

- The [ECOS Statistics Information Use Guide](https://ecos.bok.or.kr/) is source-wide and branches
  on the **original statistical producer**. Bank of Korea-produced statistics may be used,
  processed, and redistributed free of charge for commercial and non-commercial purposes when
  ECOS and the source are identified. Statistics produced by another institution may be used
  non-commercially with attribution; commercial use requires that producer's prior approval. The
  third-party branch does not expressly grant processing or redistribution, so public raw commits
  fail closed until a more specific instrument supplies those rights. ECOS `StatisticMeta` and
  `StatisticItemList` not having a licence field therefore does not itself mean that permission is
  missing.
- `301Y017/SA000` names Bank of Korea directly in ECOS table metadata. For `200Y108/10601`, ECOS
  item metadata links the exact code to “domestic expenditure on GDP (seasonally adjusted, real,
  quarterly)”, while the
  [KOSIS official recent-data record](https://kosis.kr/serviceInfo/newContrainDataDetail.do?boardIdx=1976017&boardOrgId=301)
  identifies Bank of Korea for the same title and frequency; an official
  [Bank of Korea GDP release](https://www.bok.or.kr/portal/bbs/B0000501/view.do?menuNo=200690&nttId=10097644)
  corroborates the producer. This supported the owner-approved Bank of Korea-produced
  classification recorded below, but the exact ECOS code-to-producer join is title/frequency-based
  rather than a direct identifier field and must be preserved as an owner-approved mapping.
- KOSIS API schemas likewise expose no per-series KOGL field, but the
  [KOSIS Statistics Information Use Guide](https://kosis.kr/nsistN/kosisUseGuide.do) governs the
  macro data in its listed menus. In-scope domestic statistics may be used, reused, and
  redistributed for commercial and non-commercial purposes with detailed attribution; distortion
  and paid sale of unchanged raw information are prohibited. International and North Korea
  statistics are non-commercial-only and may not be redistributed. Publications follow their
  individual KOGL notices.
- OECD archive data are governed by the
  [OECD Terms & Conditions](https://www.oecd.org/en/about/terms-conditions.html) rather than being
  retroactively CC BY 4.0. The Data section generally permits extraction, adaptation, and
  redistribution, including commercial use, but requires attribution and a dataset-level check for
  additional restrictions or third-party ownership. `DF_MEI_ARCHIVE` metadata did not expose such
  a rights field during the spike.

Treating the ECOS use guide, KOSIS use-guide permission, and OECD terms as if each were a KOGL type
would fabricate provenance. The correct control is to map the applicable source-wide instrument to
the exact producer/content category and series. The current `RedistributionPolicy` cannot preserve
that mapping, third-party status, permitted operations, attribution, approver, or approval date as
typed fields; its `allowed` state also requires a named `license_name`, which is not equivalent to
every publisher-specific rights notice.

The owner confirmed that SovereignLab and its public artifacts are non-commercial and have no
planned commercial mode. This removes ECOS third-party **commercial approval** as a current concern,
but it does not turn the third-party branch's general non-commercial-use wording into an explicit
raw-redistribution grant. Source attribution, no-distortion duties, KOSIS content-category
exceptions, and exact producer/category mapping therefore remain operative controls.

## Decision

1. Preserve the owner-approved **per-series redistribution ruling**, but rename its required
   evidence from `KOGL type` to **source-specific rights basis**. An explicit KOGL type remains one
   valid basis when a publisher actually supplies it.
2. Add an independent, strict `RightsCatalog` contract at version `1.0.0`, containing reusable
   `RightsInstrument` and per-series `SeriesRightsDecision` records. Each decision types at least:
   publisher and original producer or KOSIS content category; exact table and item identifiers;
   rights-instrument ID, official URL, and access date; explicit KOGL/licence identifier when one
   exists; producer-evidence method and URLs; permitted and prohibited operations; required
   attribution fields; decision state; approver; approval-record timestamp; and an ADR-backed
   approval reference. JSON Schema, synthetic
   fixtures, export checks, and tests ship with the models under ADR 0002's rules.
3. Do not treat the absence of a per-series licence field as either permission or prohibition.
   Apply an official source-wide use guide only after the exact series is classified by original
   producer or KOSIS content category, and preserve that mapping and attribution in the decision.
   Do not translate publisher-specific terms into a fabricated KOGL type.
4. Apply these reusable policy branches:
   - Bank of Korea-produced ECOS statistics: `allowed` for attributed use, processing, and
     redistribution.
   - Other-producer ECOS statistics: non-commercial analysis may proceed with attribution, but raw
     public redistribution remains `metadata_only` unless a producer-specific instrument expressly
     permits it.
   - In-scope KOSIS domestic macro statistics: `allowed` for attributed use, reuse, processing, and
     redistribution; no distortion, re-identification, or paid standalone sale of unchanged raw
     information.
   - KOSIS international and North Korea statistics: excluded from redistributed observations;
     publications follow their individual KOGL notices.
5. Treat the per-series gate as an auditable **classification and attribution mapping**, not a fresh
   licence investigation for every snapshot. The owner approves a complete decision once per exact
   scope; later captures may reuse it only while producer/category, instrument, intended operations,
   and attribution remain unchanged. Missing or mismatched evidence keeps the scope
   `metadata_only`, `restricted`, or `unknown`.
6. Start with no more than two ECOS candidates: quarterly seasonally adjusted real GDP
   (`200Y108/10601`) and seasonally adjusted current account (`301Y017/SA000`). The current-account
   producer classification is direct; the GDP classification uses the recorded official
   title/frequency mapping above. The owner accepts that mapping and approves `allowed` for both
   series under the ECOS use guide, with processing and redistribution permitted and
   attribution/no-distortion obligations recorded. Both decisions now exist as validated catalog
   records; raw capture remains blocked until the manifest integration gate below closes.
7. Record OECD archive observations as owner-approved `metadata_only pending dataset-specific and
   third-party-rights confirmation`. Seek the relevant source record or written confirmation, and
   cite OECD Terms & Conditions as the investigated basis rather than CC BY 4.0. This ruling does
   not approve raw OECD redistribution.
8. Keep current `SourceManifest` and benchmark contracts at `1.0.0` in this work unit. Accepted
   ADR 0005 and charter v2.2 authorize the coordinated provenance/benchmark `2.0.0` migration, but
   it is not implemented here. Raw observations stay blocked until that later implementation
   provides a typed manifest link and cross-record validator. Do not overload current free-text
   notes as a substitute.

## Approval record

On 2026-07-16 the owner:

1. confirmed that the project has no commercial-use path;
2. accepted the source-specific, classification-and-attribution rights policy;
3. approved the direct Bank of Korea classification and `allowed` ruling for `301Y017/SA000`;
4. accepted the official title/frequency-based producer mapping and `allowed` ruling for
   `200Y108/10601`; and
5. authorized continued implementation of the standalone rights records and validation; and
6. later approved the OECD `metadata_only` interim ruling in decision 7.

This approval does not authorize raw publication by itself. ADR 0005 and contract `2.0.0` were
approved separately later on 2026-07-16, but raw manifest linkage remains unimplemented.

## Alternatives considered

- **Keep the KOGL-only field and leave it null:** rejected as the proposed default because it cannot
  express the official ECOS, KOSIS, or OECD evidence and would turn a useful gate into permanent
  ambiguity.
- **Treat every Public Data Portal record as KOGL Type 1:** rejected because the portal uses
  materially different labels (`no restriction`, KOGL types, and third-party-rights notices).
- **Store the entire decision in free-text notes:** rejected because approval, producer, and
  third-party-rights invariants would not be machine-checkable.
- **Rely only on API accessibility:** rejected because technical access is not redistribution
  permission.
- **Commit all values and remove them if challenged:** rejected because append-only provenance and
  public commit history make retroactive removal an invalid control.

## Consequences

- The charter's safety outcome remains unchanged: no raw ECOS/KOSIS value is published without an
  owner-approved series ruling.
- Rights provenance becomes accurate across publishers instead of forcing unrelated terms into a
  KOGL field.
- The first harvester can be deliberately small while exact producer/category mappings and
  attribution are verified.
- Repository Apache-2.0 terms apply to original project code and documentation unless noted, not to
  source observations; redistributed data retains the recorded publisher terms and attribution
  requirements.
- This ADR supersedes **only ADR 0003 decision 6's KOGL-only wording**. ADR 0003 remains otherwise
  valid and carries a cross-link rather than being rewritten.
- Charter v2.2, `AGENTS.md`, and contributor-facing policy language synchronize this decision.
- The strict rights catalog and both approved ECOS records are complete. Raw publication remains
  blocked until the employer-risk review is complete and an accepted manifest-link contract can
  enforce the gate.

## Revisit triggers

- ECOS or KOSIS changes its use guide or adds an authoritative per-series rights notice.
- A publisher changes a candidate dataset's producer/category or rights notice.
- OECD supplies dataset-specific source/rights metadata or written confirmation for the archive.
- The project gains any commercial-use path.
- The owner revises the candidate basket or public-harvester boundary.
