# M1a evidence schema contract

- Status: implemented; ready for review
- Date: 2026-07-14
- Schema version: `1.0.0`
- Scope: provenance snapshots, benchmark records, and cross-record integrity only

## 1. Why this contract exists

SovereignLab must distinguish a fluent answer from an answer supported by evidence that was actually available at the requested point in time. The first code milestone therefore freezes evidence and benchmark structure before source collection, retrieval experiments, prompting, or fine-tuning can bias the evaluation design.

The canonical models are strict Pydantic models. Unknown fields are rejected, instances are immutable, and public JSON Schema files are generated from the same source models.

## 2. SourceManifest

`SourceManifest` represents one release-specific, byte-identical evidence snapshot. A URL by itself is not sufficient because its content can change.

| Concern | Required fields | Contract |
|---|---|---|
| Stable identity | `schema_version`, `source_id`, `source_kind` | IDs are lowercase slugs; kind is `document`, `dataset`, or `api`. |
| Human provenance | `publisher`, `title`, `document_family`, `language`, `release_label` | The first release supports Korean, English, and `und` for non-linguistic/API material. |
| Temporal provenance | `published_on`, `publication_date_basis`, `publication_date_notes`, `retrieved_at` | Retrieval timestamps must be timezone-aware and cannot precede publication. A retrieval-date fallback must explain why no stronger publication evidence exists. |
| Canonical origin | `canonical_url`, `media_type` | Only HTTP(S) publisher/source URLs are accepted; local paths do not belong in public manifests. |
| Byte integrity | `content_sha256`, `byte_size` | SHA-256 is exactly 64 lowercase hexadecimal characters and size must be positive. |
| Rights | `redistribution` | Status is `allowed`, `metadata_only`, `restricted`, or `unknown`; allowed content requires a named license, while restricted/unknown decisions require notes. |

`published_on` is treated as the earliest defensible availability date for the exact snapshot. If an API does not expose historical vintages, a current snapshot cannot support an earlier `as_of` request merely because it contains old observation periods.

## 3. BenchmarkRecord

`BenchmarkRecord` represents one auditable routing and evidence task.

| Concern | Required fields | Contract |
|---|---|---|
| Stable identity | `schema_version`, `record_id` | Every item has a versioned lowercase slug. |
| Leakage-safe partitioning | `split`, `evidence_group_id`, `parallel_group_id` | Evidence-related questions and Korean/English parallel items cannot cross train/dev/test splits. |
| Request | `language`, `question`, `as_of`, `tags` | A `temporal` tag requires an explicit cutoff date. |
| Routing gold label | `expected_route` | Exactly one of `documents`, `data`, `documents_and_data`, or `abstain`. |
| Documentary gold evidence | `document_evidence` | Each expected claim points to a source and at least one page, section, or fragment locator. |
| Tool gold evidence | `tool_expectations` | Each expected call records the data/API source, typed JSON arguments, and facts expected from deterministic output. |
| Answer contract | `reference_answer`, `abstention_reason` | Answerable routes require a reference answer; abstention requires a reason and cannot contain a reference answer. |
| Human audit | `annotation` | Draft, reviewed, and approved states retain author/reviewer and timezone-aware timestamps. |

### Route truth table

| Expected route | Documents required | Tool call required | Reference answer | Abstention reason |
|---|---:|---:|---:|---:|
| `documents` | Yes | No | Yes | No |
| `data` | No | Yes | Yes | No |
| `documents_and_data` | Yes | Yes | Yes | No |
| `abstain` | No | No | No | Yes |

## 4. BenchmarkBundle cross-record checks

JSON Schema validates individual file shape but cannot enforce dataset-wide invariants. `BenchmarkBundle` additionally rejects:

- duplicate source or record IDs;
- references to unknown sources;
- documentary evidence that points to a dataset/API source;
- tool expectations that point to a document source;
- any referenced document, dataset, or API snapshot published after the record's `as_of` cutoff;
- an `evidence_group_id` appearing in more than one split;
- a Korean/English `parallel_group_id` appearing in more than one split.

These checks make temporal and split leakage build failures instead of post-hoc caveats.

## 5. Public artifacts

- Pydantic source models: `src/sovereignlab/schemas/`
- Generated contracts: `data/schemas/`
- Synthetic, non-institutional examples: `data/fixtures/`
- Export command: `python scripts/export_json_schemas.py`
- Validation tests: `tests/schemas/`

The examples use `example.org` and invented content. They are not benchmark observations and do not count toward the 40-item gold-set target.

## 6. Reproduction

```powershell
python scripts/export_json_schemas.py
python -m pytest tests/schemas
python -m pytest --cov=sovereignlab --cov-report=term-missing
```

A test compares every committed JSON Schema document with the current Pydantic output. Changing a model without regenerating its public contract fails the suite.

## 7. Versioning rule

Adding or changing a required field, enum meaning, route invariant, or temporal/split rule is a breaking contract change. It requires a new schema version, migration notes, regenerated JSON Schema, updated fixtures/tests, and a superseding ADR. Existing approved benchmark records must never be silently reinterpreted.
