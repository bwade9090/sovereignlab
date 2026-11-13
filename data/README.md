# Data policy

Only redistributable public benchmark records, schemas, source manifests, and small deterministic fixtures may be committed here.

## Licensing boundary

The repository's Apache-2.0 licence covers original project code and documentation unless noted
otherwise; it does not relicense third-party source data or redistributed observations. Every
source-data artifact remains subject to the originating provider's terms and attribution
requirements. A redistributed observation artifact additionally requires those terms to be
recorded in its source manifest and owner-approved series rights decision.

- Bank of Korea-produced ECOS statistics may be used, processed, and redistributed for commercial
  or non-commercial purposes with attribution under the ECOS Statistics Information Use Guide.
  Third-party-produced ECOS statistics remain metadata-only unless the intended processing and
  redistribution are supported by that producer's terms or approval.
- KOSIS domestic macro statistics in the use guide's listed menus may be used, reused, and
  redistributed commercially or non-commercially with attribution. Do not sell unchanged raw
  KOSIS information as a paid standalone product. KOSIS international and North Korea statistics
  may not be redistributed, and publications follow their individual KOGL notices.
- Official Bank of Korea-produced Economic Outlook reports and official English full translations
  are allowed under the owner-approved public-data family ruling in ADR 0009. Attribute the Bank
  of Korea, disclose modification, processing, or transformation, and preserve separately marked
  third-party rights. The governing instrument is the Bank of Korea copyright policy's Public Data
  Act Article 19 branch, not a fabricated KOGL type.
- Benchmark, model, and generated-data artifacts must state their own licences when published.

The operational gate accepted in ADR 0004 remains fail closed: no raw observation may be committed
until its exact producer or KOSIS content category, applicable rights instrument, attribution,
permitted operations, and owner approval are present in strict rights records. `SourceManifest`
2.0.0 carries the typed rights-decision link and `BenchmarkBundle` 2.0.0 cross-validates it
(see `docs/architecture.md`); an `allowed` data manifest without a matching owner-approved
decision fails validation.

Repository layout:

- `archive/oecd-stes/` — append-only OECD availability/content constraint XML; metadata only and
  never observation rows under the current ruling.
- `archive/ecos/` — append-only raw responses for only owner-approved exact ECOS series; files are
  created only when `ECOS_API_KEY` is configured and the linked rights decision validates.
- `archive/kosis/` — append-only raw responses for only owner-approved exact KOSIS domestic
  statistics scopes; files are created only when `KOSIS_API_KEY` is configured and the linked
  rights decision validates.
- `availability/` — immutable edition-availability ledgers whose inventories are derived from the
  same captured constraint bytes; historical ledgers are never rewritten.
- `benchmark/` — the frozen 40-record core authoring matrix, review drafts, and the
  human-reviewed core records; drafts are never reported as reviewed gold.
- `fixtures/` — synthetic examples, including the bilingual temporal-retrieval corpus, and later
  small redistributable recorded responses used by offline tests.
- `manifests/` — source URL, publisher, publication date, retrieval time, checksum, language, and license notes.
- `rights/` — append-only source-specific rights instruments and owner-approved series decisions;
  metadata only, never observation payloads.
- `schemas/` — generated public JSON Schema contracts; never edit these by hand.
- `raw/` — downloaded source material; ignored by Git.
- `interim/` — local extraction and transformation outputs; ignored by Git.

Run one capture with `python scripts/harvest_weekly.py --repository-root .`. The operation is
append-only: a reused capture path fails instead of overwriting bytes. The weekly GitHub Actions
workflow runs the same command, checks the captured artifacts with `tests/test_committed_data.py`
and the harvester tests, and commits only `archive/`, `availability/`, and `manifests/` outputs.
Captures taken after an evidence registry was frozen stay archive-only until a new registry
version admits them (ADR 0010). The weekly capture record has a permanent gap from 2026-07-20 to
2026-11-02, because every run in that period failed before committing. Files under `archive/` are
marked binary in `.gitattributes` so Git cannot change provider line endings and invalidate the
manifest hash.
Public Git history is the capture-date evidence.

Do not commit a PDF, extracted full text, or API response until its redistribution basis is documented. Never place confidential, applicant, or institutional internal data in this repository.

Regenerate schemas with `python scripts/export_json_schemas.py`; tests fail if generated contracts drift from their Pydantic models.
