# K-VINTAGE human-reviewed core authoring matrix 1.0.0

- Status: structural allocation frozen; human review in progress
- Date: 2026-07-24
- Scope authority: charter v2.3 §5 and M2 continuation order
- Canonical matrix: `data/benchmark/core-authoring-matrix-v1.json`
- Public schema: `data/schemas/core-authoring-matrix-v1.schema.json`

## 1. Frozen allocation

The tier-1 core contains exactly 40 records represented as 20 Korean/English pairs. The matrix
freezes structure before further question authoring:

| Route | Korean | English | Train | Dev | Test | Total |
|---|---:|---:|---:|---:|---:|---:|
| `documents` | 5 | 5 | 6 | 2 | 2 | 10 |
| `data` | 5 | 5 | 6 | 2 | 2 | 10 |
| `documents_and_data` | 5 | 5 | 6 | 2 | 2 | 10 |
| `abstain` | 5 | 5 | 6 | 2 | 2 | 10 |
| **Total** | **20** | **20** | **24** | **8** | **8** | **40** |

Every pair has one route, split, evidence group, Korean record ID, English record ID, and question
intent. Documentary and data source units are assigned to one split globally. Reusing a planned
source unit across train/dev/test makes `CoreAuthoringMatrix` validation fail, while reuse inside
one split is permitted. This supplements the record-level `BenchmarkBundle` checks by freezing the
source-release allocation before all manifests and questions exist.

The test-held data unit is deliberately reserved rather than fabricated. Its two data records and
the combined pair that depends on it must not be authored until an independently captured,
owner-approved release has a committed manifest and, where required, availability evidence.

## 2. First reviewable batch

`data/benchmark/drafts/core-batch-001.jsonl` contains four AI-authored draft records:

1. one Korean/English `data` pair asking for Korea's May 2026 amplitude-adjusted CLI as of
   2026-07-09; and
2. one Korean/English `abstain` pair asking the same value as of 2026-06-30, when the committed
   ledger has no definitely available edition.

The data pair is grounded in the committed OECD Korea CLI archive, its typed rights decision, and
the active edition-availability ledger. Offline validation reproduces edition `202607`, raw and
normalized value `102.66`, canonical unit `oecd_amplitude_adjusted_index`, and two-decimal display.
For the earlier cutoff, the ledger mechanically returns `no_edition_definitely_available`; the
draft therefore never substitutes the later edition or invents an older publication date.

All four annotations remain `draft`. They are not counted as human-reviewed core records and may
not be promoted to `reviewed` or `approved` without a named human reviewer and timestamp.

## 3. Human-review checklist

For each bilingual pair, the reviewer must verify:

1. Korean and English questions ask the same task without answer-bearing translation differences.
2. The route and source-unit allocation match the frozen matrix.
3. `as_of`, source scope, edition, period, unit, normalization rule, and display precision are
   exact.
4. The reference answer contains no fact that the committed evidence packet cannot reproduce.
5. Abstention wording states the actual fail-closed reason and does not expose post-cutoff values.
6. Tags, split, evidence group, and parallel group are correct.

Corrections remain in the draft batch until review is complete. An approval records the reviewer
and review timestamp in each `BenchmarkRecord`; it does not rewrite the frozen matrix allocation.

## 4. Reproduction

```bash
python scripts/export_json_schemas.py
python -m pytest tests/benchmark/test_core_batch.py
python -m ruff check .
python -m ruff format --check .
```

The batch test validates the matrix, constructs a real `BenchmarkBundle` from committed manifests,
ledger, and rights catalog, reruns the fail-closed resolver over the committed CLI bytes, applies
normalization 1.0.0, and checks the earlier-cutoff abstention.
