# K-VINTAGE benchmark data

The human-reviewed core of K-VINTAGE: bilingual questions whose gold answers depend on the data
vintage and documents available at each question's `as_of` date. Progress by pair is tracked in
[`docs/PROJECT_STATUS.md`](../../docs/PROJECT_STATUS.md).

## Files

- `core-authoring-matrix-v1.json` — the frozen allocation of the 40-record core
  (`CoreAuthoringMatrix` 1.0.0). Each of its 20 pairs names a route, a split, an evidence group,
  the evidence units it may use, the Korean and English record IDs, and a one-line
  `question_intent`.
- `core/core-batch-NNN.jsonl` — approved records, one `BenchmarkRecord` 2.0.0 per line.
- `drafts/` — review candidates, when any exist. A draft is never counted as a core record.

## Allocation

| Route | Pairs | Train | Dev | Test | Records |
| --- | ---: | ---: | ---: | ---: | ---: |
| `documents` | 5 | 3 | 1 | 1 | 10 |
| `data` | 5 | 3 | 1 | 1 | 10 |
| `documents_and_data` | 5 | 3 | 1 | 1 | 10 |
| `abstain` | 5 | 3 | 1 | 1 | 10 |

An evidence unit (a document release or a data snapshot) belongs to exactly one split; the matrix
model rejects a unit reused across splits. The test-split data unit is reserved rather than
fabricated: `kv-core-data-05` and `kv-core-both-05` are not authored until an independently
captured, owner-approved release exists.

The five abstain pairs each exercise a different reason to decline: no edition provably available
at the cutoff, a neighbouring OECD measure with no approved rights decision, a false premise
(archive edition counts are not revisions), a missing `as_of`, and a cutoff beyond the ledger's
completeness frontier.

## A record

- `question`, `language`, and `as_of`.
- `expected_route`: `documents`, `data`, `documents_and_data`, or `abstain`.
- `document_evidence`: the source manifest ID, a page or section locator, and the claim it
  supports.
- `tool_expectations`: the tool name, its exact flat arguments, and the facts the result must
  contain, such as the selected edition, raw value, normalized value, and unit. A vintage
  expectation also names the ledger and edition.
- `reference_answer`, or `abstention_reason` for an abstain record. Answers attribute the source
  and disclose paraphrase or processing.
- `annotation`: who drafted the record, who reviewed it, and when.
- `split`, `evidence_group_id`, and `parallel_group_id` (the pair ID).

Document evidence is anchored to pages of the official Bank of Korea PDFs. Those PDFs are not
committed, so check a locator against a copy whose size and SHA-256 match the manifest.

## Adding a pair

1. The owner chooses the pair. Its evidence must already be committed: document manifests, or a
   data unit that an evidence registry admits.
2. Draft the Korean and English records in `drafts/core-draft-NNN.jsonl` with
   `annotation.status` set to `draft`.
3. The owner reviews both records against this checklist:
   - The Korean and English questions ask the same task, with no answer-bearing translation
     difference.
   - The route and evidence units match the matrix.
   - `as_of`, source scope, edition, period, unit, normalization rule, and display precision are
     exact.
   - The reference answer contains nothing the committed evidence cannot reproduce.
   - An abstention reason states the real fail-closed reason and exposes no post-cutoff value.
   - Tags, split, evidence group, and parallel group are correct.
4. On approval, set `annotation.status` to `approved` with the reviewer's name and timestamp, and
   move the file to `core/core-batch-NNN.jsonl`. Update the table in the status page.

Approved records are not edited afterwards except through another owner review.

## Checking the core

```bash
python -m pytest tests/benchmark
```

The tests are driven by the committed files, so a new batch is covered without writing a new
test. They check that every record fills its matrix slot and carries the owner's review, that the
core and its evidence form one valid `BenchmarkBundle` (no post-cutoff source, no unresolvable
vintage, no broken rights link, no evidence shared across splits), and that running the real tool
with each record's arguments reproduces its declared facts.

Never merge counts of the human-reviewed core with machine-generated probes.
