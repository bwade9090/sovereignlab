# K-VINTAGE human-reviewed core authoring matrix 1.0.0

- Status: structural allocation and first six records owner-approved
- Date: 2026-07-29
- Scope authority: charter v2.5 §5 and M2 continuation order
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

## 2. First approved batch

`data/benchmark/core/core-batch-001.jsonl` contains four owner-approved records initially authored
by AI:

1. one Korean/English `data` pair asking for Korea's May 2026 amplitude-adjusted CLI as of
   2026-07-09; and
2. one Korean/English `abstain` pair asking the same value as of 2026-06-30, when the committed
   ledger has no definitely available edition.

The data pair is grounded in the committed OECD Korea CLI archive, its typed rights decision, and
the active edition-availability ledger. Offline validation reproduces edition `202607`, raw and
normalized value `102.66`, canonical unit `oecd_amplitude_adjusted_index`, and two-decimal display.
For the earlier cutoff, the ledger mechanically returns `no_edition_definitely_available`; the
record therefore never substitutes the later edition or invents an older publication date.

All four annotations record `status=approved`, reviewer `Hyungbae Cho`, and the aware review
timestamp. They count as four human-reviewed core records.

## 3. First approved documentary pair

`data/benchmark/core/core-batch-002.jsonl` contains the frozen `kv-core-doc-01` Korean/English
pair. Both records use the `documents` route, `train` split,
`eg-doc-bok-outlook-2026-05` evidence group, and `kv-core-doc-01` parallel group. The Korean record
is bounded to the Korean report's 2026-05-28 publication date and cites PDF page 10; the English
record is independently bounded to the full translation's 2026-06-30 publication date and cites
PDF page 9.

Both answers paraphrase one stated driver: stronger-than-expected IT exports contributed `+0.7%p`
to the `0.6%p` upward revision of the 2026 GDP growth forecast. They attribute the Bank of Korea
and disclose summarization/paraphrase. On 2026-07-29, Hyungbae Cho approved both records without a
question, answer, route, evidence, `as_of`, or frozen-allocation change. Their annotations preserve
the AI author and record the named human reviewer and aware review timestamp. The lifecycle tag
changed from `draft-002` to `batch-002` when the file moved into `core/`.

The approved human-reviewed core is now 6/40 records; the other 34 are not authored.

## 4. Approval records

On 2026-07-25, Hyungbae Cho explicitly approved:

1. the unchanged 40-record structural allocation in
   `data/benchmark/core-authoring-matrix-v1.json`; and
2. all four records in `core-batch-001.jsonl` without question, answer, route, or evidence changes.

The filenames and existing matrix field names remain unchanged. The approved record file keeps its
filename and moves from `drafts/` to `core/` so the directory reflects its review state.

On 2026-07-29, Hyungbae Cho explicitly approved both records in the `kv-core-doc-01` documentary
pair. The substantive record fields and frozen matrix remain unchanged; the second batch moved
from `drafts/core-draft-002.jsonl` to `core/core-batch-002.jsonl` with approval metadata and the
corresponding lifecycle tag.

## 5. Human-review checklist

For each bilingual pair, the reviewer must verify:

1. Korean and English questions ask the same task without answer-bearing translation differences.
2. The route and source-unit allocation match the frozen matrix.
3. `as_of`, source scope, edition, period, unit, normalization rule, and display precision are
   exact.
4. The reference answer contains no fact that the committed evidence packet cannot reproduce.
5. Abstention wording states the actual fail-closed reason and does not expose post-cutoff values.
6. Tags, split, evidence group, and parallel group are correct.

Future corrections remain in their draft batch until review is complete. An approval records the
reviewer and review timestamp in each `BenchmarkRecord`; it does not rewrite the frozen matrix
allocation.

## 6. Reproduction

```bash
python scripts/export_json_schemas.py
python -m pytest tests/benchmark/test_core_batch.py
python -m pytest tests/benchmark/test_bok_outlook_core.py
python -m ruff check .
python -m ruff format --check .
```

The batch test validates the matrix, constructs a real `BenchmarkBundle` from committed manifests,
ledger, and rights catalog, reruns the fail-closed resolver over the committed CLI bytes, applies
normalization 1.0.0, and checks the earlier-cutoff abstention.

The documentary-core test validates both records against their strict manifests and the frozen
matrix, enforces language-specific publication cutoffs and split-group integrity, verifies the
named reviewer metadata, and confirms the approved count is six.
