# M1b source-rights catalog contract

- Status: implemented
- Date: 2026-07-16
- Schema version: `1.0.0`
- Decision basis: charter v2.2 and ADR 0004
- Compatibility: independent contract; `SourceManifest` and benchmark schemas remain `1.0.0`

## 1. Purpose and boundary

The rights catalog turns publisher use guides and producer/category mappings into machine-checked
metadata before KOR-RTD captures observations. It distinguishes permission to use a portal from
permission to process and publicly redistribute one exact series.

The catalog contains no observations. Since 2026-07-17, `SourceManifest` 2.0.0 carries the typed
`rights_decision` link to one catalog decision, and `BenchmarkBundle` 2.0.0 cross-validates that
link (see `docs/project/05_evidence_contract_2_0_migration.md`): an `allowed` data manifest must
name a matching-scope `allowed`, unexpired decision in a bundled catalog. Raw ECOS/KOSIS capture
remains blocked operationally until the harvester produces real manifests that pass this
validation.

## 2. Public models

| Model | Purpose | Key invariants |
|---|---|---|
| `RightsEvidence` / `EvidenceObservation` | State what one official URL proves | Typed claims plus observed system, scope, title/frequency, producer, or KOSIS category |
| `RightsInstrument` | One official licence/use-guide record | Official URL/date, exact terms evidence, applicable systems/classes, optional immutable capture hash |
| `SeriesRightsDecision` | Apply an instrument to one table/item scope | Exact classification and evidence joins, operation policy, rendered attribution, owner approval record |
| `RightsCatalog` | Append-only collection and cross-record validator | Unique IDs/scopes, instrument applicability, non-commercial profile, expiry and provenance ordering |

`OperationStatus` distinguishes `permitted`, `prohibited`, `requires_additional_approval`, and
`not_expressly_granted`. The last value is important for other-producer ECOS statistics: the common
guide permits non-commercial use but does not expressly grant raw redistribution.

## 3. Accepted policy mapping

| Content class | Raw public decision under the current policy |
|---|---|
| Bank of Korea-produced ECOS | `allowed` with attribution and no distortion |
| Other-producer ECOS | `metadata_only` unless producer-specific terms expressly permit redistribution |
| KOSIS domestic/easy-view macro statistics | eligible for `allowed` with required KOSIS attribution and restrictions |
| KOSIS international/North Korea statistics | raw redistribution rejected |
| KOSIS publication | individual KOGL decision required |

The project use profile is fixed to `noncommercial_public_research`. A commercial-use path requires
a new owner review, decision record, and superseding catalog.

## 4. Mechanical checks

The canonical Pydantic models and tests reject:

- duplicate instrument IDs, decision IDs, series scopes, operations, attribution fields, or
  evidence kind/URL pairs;
- a source-system, content-class, KOSIS-category, or rights-instrument applicability mismatch;
- direct producer mappings without exact source scope/title/frequency/producer observations, and
  cross-source mappings whose normalized titles, frequency, producer, or source systems do not
  form the approved join;
- an `allowed` decision without an original producer, a complete ADR-backed approval record,
  required non-commercial use/process/redistribution operations, permitted rules for every intended
  operation, prohibited distortion, or exact attribution-template placeholders;
- Bank of Korea-authored ECOS classification without `original_producer=한국은행` and first-party
  status, and any first/third-party label inconsistent with publisher and producer identity;
- raw-allowed KOSIS international/North Korea data, domestic/easy-view rulings missing their
  no-sale/no-reidentification rules or detailed attribution, and publications without licensed
  dataset-specific terms;
- raw-allowed other-producer ECOS data without a producer-specific instrument, or any OECD
  `allowed` record under this contract;
- commercial intended use under the fixed non-commercial profile, expired rulings, unknown or
  mismatched instruments, approval before instrument access, evidence/capture after catalog
  recording, and a catalog that supersedes itself.

## 5. Committed artifacts

- Canonical models: `src/sovereignlab/schemas/rights.py`
- Generated schemas: `data/schemas/rights-*.schema.json` and
  `data/schemas/series-rights-decision-v1.schema.json`
- Synthetic examples: `data/fixtures/rights_instrument.example.json` and
  `data/fixtures/series_rights_decision.example.json`
- First owner-approved metadata catalog: `data/rights/kor-rtd-rights-2026-07-16.json`
- Tests: `tests/schemas/test_rights.py` and `tests/schemas/test_export.py`

The first catalog records `allowed` decisions for `200Y108/10601` and `301Y017/SA000`. The GDP
decision preserves the normalized title/frequency join and both official sides of that mapping; the
current-account decision records exact ECOS scope and producer observations. Their
`approval_recorded_at` values mean when the accepted decision was written into the catalog, while
`approval_record_reference` points to ADR 0004's version-controlled approval record.

## 6. Reproduction and versioning

```powershell
python scripts/export_json_schemas.py
python -m pytest tests/schemas/test_rights.py tests/schemas/test_export.py
python -m pytest --cov=sovereignlab --cov-report=term-missing
```

Generated schemas must match the canonical models byte-for-byte after JSON parsing. Published
catalogs are append-only: changed terms or rulings create a new `catalog_id` with
`supersedes_catalog_id`; do not rewrite an earlier catalog.
