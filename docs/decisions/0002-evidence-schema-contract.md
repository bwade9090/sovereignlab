# ADR 0002: freeze strict evidence and benchmark contracts before collection

- Status: accepted
- Date: 2026-07-14
- Related: ADR 0005 partially supersedes decision 5 only for its typed historical-archive
  exception; all other cutoff and provenance rules remain in force.

## Context

The project will compare closed-book, temporal RAG, tool-using, and LoRA-routed systems. If source dates, rights, route labels, or dataset splits remain informal until after experiments, it becomes easy to leak future evidence, place near-duplicates across splits, or publish unsupported metrics.

JSON Schema can describe individual records but cannot verify relationships across source and benchmark files.

## Decision

1. Use immutable Pydantic v2 models with `extra="forbid"` as the canonical contracts.
2. Give every source snapshot a stable release-specific ID, aware retrieval time, defensible publication date and basis, SHA-256, byte size, canonical URL, media type, language, and redistribution decision.
3. Give every benchmark item one of four exclusive route labels with route-consistent documentary evidence, tool expectations, answer/abstention fields, and human-review provenance.
4. Keep evidence groups and Korean/English parallel groups in a single train/dev/test split.
5. Reject every referenced document or data snapshot published after the benchmark item's `as_of` cutoff.
6. Generate and commit public JSON Schema files from the Pydantic models, with synchronized synthetic fixtures and tests.
7. Treat schema `1.0.0` as frozen once real source manifests or benchmark records are approved; breaking changes require versioning and migration notes.

## Alternatives considered

- **Loose JSONL dictionaries:** rejected because typos and missing provenance would surface late and inconsistently.
- **JSON Schema only:** rejected because it cannot enforce cross-file references, temporal cutoffs, or group-level split isolation.
- **Random question-level splits:** rejected because paraphrases and bilingual pairs would inflate measured generalization.
- **URL-only provenance:** rejected because publisher content and API responses can change at the same URL.
- **Observation date as proof of historical availability:** rejected because a current API response may contain revised historical observations.

## Consequences

- Initial annotation takes longer because provenance and review state are explicit.
- Dataset construction errors fail before retrieval or model evaluation begins.
- Source material can remain uncommitted while its metadata, rights decision, and checksum remain reproducible.
- Future tooling must read schema version `1.0.0` explicitly rather than assume unversioned dictionaries.

## Revisit triggers

- The first real BOK/OECD source cannot be represented without ambiguous or fabricated metadata.
- The SDMX tool contract needs source-vintage semantics not expressible by the current manifest.
- Human annotation shows that the four exclusive routes cannot represent an important task class.
