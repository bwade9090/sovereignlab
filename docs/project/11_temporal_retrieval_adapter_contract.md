# Trusted temporal-document adapter

Status: work-unit-C temporal retrieval adapter slice implemented offline on 2026-07-29.

## Purpose and boundary

This specification records the third independently reviewable ADR 0008 implementation slice: a
trusted synthetic-corpus registry and the typed `retrieve_temporal_documents` execution adapter.
It connects the existing publication-date-safe lexical retriever to the execution/result contract
without changing `BenchmarkRecord`, `BenchmarkBundle`, or the 13 public JSON Schemas.

The slice adds no source capture, official report body, benchmark record, live model call, paid
operation, planner, dispatcher, packet assembler, or end-to-end executor.

## Frozen synthetic corpus

The committed reference registry admits exactly these two files:

| Role | Records | Bytes | SHA-256 |
| --- | ---: | ---: | --- |
| `source_manifests.jsonl` | 4 | 2,944 | `cc25ae9085518af89032b9b3bd29aeb56f1d0b15051c51e4d7070a9088b4d8a6` |
| `document_chunks.jsonl` | 6 | 2,037 | `c22018874c54fb2b6c98df4c816375fbc610102fbbd629542a57734c9ad5b7ee` |

The corpus contains only synthetic Korean and English pre-cutoff/post-cutoff document pairs. The
two real Bank of Korea Outlook manifests have no committed searchable chunks and are not silently
included.

The reference corpus ID is `synthetic-temporal-retrieval-corpus-v1`. Its canonical descriptor
binds the corpus ID, schema version, exact JSONL hashes and byte sizes, record counts, and every
source/chunk ID. Its frozen descriptor SHA-256 is
`823117ee29a191bc306843e44ccd9d37e063db79cc87e15dcb7f2a11f5b5bf7e`.
Changing either input requires a new corpus ID and descriptor; v1 must remain reproducible.

## Trusted registry boundary

`sovereignlab.retrieval.registry` loads two explicit repository-relative paths under
`data/fixtures/retrieval/`. It does not discover candidate inputs. Construction rejects absolute
paths, traversal, role reuse, missing files, non-JSONL inputs, empty or larger-than-1-MB payloads,
more than 100 sources or 1,000 chunks, invalid UTF-8/JSON, blank records, duplicate JSON keys,
non-finite constants, and non-object records.

The registry stores exact built-in immutable `bytes` and the validated corpus model. It reparses
those bytes and compares the complete model at construction, descriptor calculation, and every
adapter call. This closes both verify-then-mutate gaps and alternate `bytes.decode()` behavior.
The adapter executes against the newly reparsed local corpus rather than a later mutable field.

The descriptor contains neither local paths nor raw passage text. Nevertheless, the two exact file
hashes bind returned and non-returned chunks, including future and other-language inputs that could
otherwise affect corpus statistics.

## Typed execution behavior

`execute_temporal_document_call` accepts only a validated `TemporalDocumentCall` and a
harness-supplied `TemporalCorpusRegistry`. It copies `question`, `language`, `as_of`, and `top_k`
unchanged into `TemporalDocumentQuery`.

The underlying retriever continues to:

1. remove other-language and post-cutoff manifests;
2. remove chunks not bound to the eligible manifests;
3. compute corpus statistics and deterministic lexical scores only over eligible chunks; and
4. return positive matches in `(-score, source_id, chunk_id)` order up to `top_k`.

Query features are sorted before floating-point accumulation, and scores are rounded to 12
significant digits before ranking and serialization. This keeps committed traces stable across
Python hash seeds while preserving the existing lexical baseline.

Before returning success, the adapter checks query identity, `top_k`, duplicate IDs, language,
cutoff, ordering, exact source/chunk membership and fields, and exact equality with a fresh
reference retrieval. A fabricated subset, score, source/hash/date, locator, text, or unregistered
chunk therefore fails closed.

Success emits only `DocumentMatchEvidence`: source/chunk IDs, source hash, language, publication
date, locator, selected text, and deterministic score. It does not expose query internals, paths,
URLs, full manifests, retrieval timestamps, future inputs, other-language inputs, or unselected
passages.

An empty valid retrieval returns `abstained` with
`no_temporal_document_match`. Registry corruption returns
`temporal_corpus_misconfigured`; an unexpected retrieval or mapping failure returns
`temporal_retrieval_failed`. All messages are stable, call-bound, and omit internal exception text
and corpus inventory.

## Validation evidence

Validated on Windows with Python 3.12.13:

- all 70 retrieval tests pass with 100% retrieval statement/branch coverage
  (314 statements, 94 branches);
- all 646 repository tests pass with 100% SovereignLab statement/branch coverage
  (2,881 statements, 948 branches);
- Ruff check and format check pass across 55 Python files; and
- all 13 public schemas regenerate deterministically.

Regression coverage includes Korean/English mapping, inclusive cutoffs, filter-before-scoring
equivalence, stable tie order, `top_k=1` and `top_k=20`, trace round-trip, empty-result abstention,
exact-byte/model mutation, decode-overriding byte subclasses, size/count/path/JSONL bounds,
fabricated evidence, field and score drift, error sanitization, and repeated byte-identical replay.

No network, provider read, secret, live model call, GPU operation, or paid operation occurred.

## Next independent slice

The ninth independently reviewable ADR 0008 work-unit-C slice shipped on 2026-08-11 at feature
commit `883815b`.
Five deterministic JSON traces under `traces/replay/v1/` were generated through the real private
executor, `ScriptedPlanner`, callable and artifact registries, and temporal retrieval corpus, then
checked by exact-byte replay. The first nine work-unit-C slices are complete, the public schema
count remains 13, and the minimal offline briefing path has shipped. Its public description is
exactly `typed function calling with committed traces`.

The draft-only Korean/English authoring slice for the frozen `kv-core-data-02` pair completed on
2026-08-19 at feature commit `f2d2523`, using only `ecos-200y108-snapshot-20260717`, whose use in
KOR-RTD is owner-approved. It added exactly two draft records. At that checkpoint, they remained
pending a separate named human review, so the approved core remained 6/40. The frozen 40-record matrix,
source set, rights decisions, 13 public schemas, and frozen execution runtime remain unchanged.

That review gate completed on 2026-08-20 at approval feature commit `473a733`. Hyungbae Cho
approved exactly the two `kv-core-data-02` records, which now live in
`data/benchmark/core/core-batch-003.jsonl`; the approved core is now 8/40. This was a
lifecycle-only transition: questions, answers, cutoff, tool expectations, the frozen matrix,
execution contracts and runtime, source bytes and manifests, rights decisions, normalization,
and the 13 public schemas remain unchanged.

The next bounded authoring slice completed on 2026-08-20 at feature commit `50c4d9c`. It added
exactly the two draft-only `kv-core-data-03` Korean/English records in
`data/benchmark/drafts/core-draft-004.jsonl`, using only
`ecos-301y017-snapshot-20260717`, whose use in KOR-RTD is owner-approved. At that checkpoint,
neither record had named review metadata or entered `core/`, so the approved core remained 8/40:
two draft records were pending review and 30 matrix slots remained unauthored and unapproved.

That review gate completed on 2026-08-21 at approval feature commit `db6700e`. Hyungbae Cho
approved exactly the two `kv-core-data-03` records, which now live in
`data/benchmark/core/core-batch-004.jsonl`; the approved core is now 10/40 and 30 matrix slots
remain unauthored and unapproved. This was a lifecycle-only transition: questions, answers,
cutoff, tool expectations, the frozen matrix, execution contracts and runtime, source bytes and
manifests, rights decisions, normalization, the 13 public schemas, and the five committed traces
remain unchanged.

The next bounded authoring slice completed on 2026-08-21 at feature commit `5e0da06`. It added
exactly the two draft-only `kv-core-data-04` Korean/English records in
`data/benchmark/drafts/core-draft-005.jsonl`, using only
`kosis-cpi-snapshot-20260717`, whose use in KOR-RTD is owner-approved under ADR 0007. At that
checkpoint, neither record had named review metadata or entered `core/`, so the approved core
remained 10/40: two draft records were pending review and 28 matrix slots remained unauthored and
unapproved.

That review gate completed on 2026-08-25 at approval feature commit `95c5e61`. Hyungbae Cho
approved exactly the two `kv-core-data-04` records, which now live in
`data/benchmark/core/core-batch-005.jsonl`; the approved core is now 12/40 and 28 matrix slots
remain unauthored and unapproved. This approval completes the data route's four authorable pairs
(`kv-core-data-01` through `kv-core-data-04`); the fifth data pair `kv-core-data-05` stays
reserved on the deliberately unauthored test-split unit. This was a lifecycle-only transition:
questions, answers, cutoff, tool expectations, the frozen matrix, execution contracts and
runtime, source bytes and manifests, rights decisions, normalization, the 13 public schemas, and
the five committed traces remain unchanged.

The next bounded authoring slice completed on 2026-08-25 at feature commit `c20619d`. It added
exactly the two draft-only `kv-core-abstain-02` Korean/English records in
`data/benchmark/drafts/core-draft-006.jsonl`. The abstain pair binds no document or data units and
carries no tool expectations or reference answer, only a language-matched abstention reason: both
questions ask for Korea's OECD normalised CLI value for May 2026 as of 2026-07-09, a neighboring
measure outside the sole owner-approved OECD raw-data scope (Korea's monthly amplitude-adjusted
CLI, `KOR.M.LI_AA.IX._T`, ADR 0007), so the gold behavior is abstention on the missing rights
basis even though the approved scope itself resolves at that cutoff. At that checkpoint, neither
record had named review metadata or entered `core/`, so the approved core remained 12/40: two
draft records were pending review and 26 matrix slots remained unauthored and unapproved.

That review gate completed on 2026-08-26 at approval feature commit `4c29b1d`. Hyungbae Cho
approved exactly the two `kv-core-abstain-02` records, which now live in
`data/benchmark/core/core-batch-006.jsonl`; the approved core is now 14/40, and at that
checkpoint 26 matrix slots remained unauthored and unapproved. This is the second approved abstain pair (after
`kv-core-abstain-01`) and the first approved pair whose fail-closed basis is a rights boundary
rather than the availability ledger. This was a lifecycle-only transition: questions, abstention
reasons, cutoff, the frozen matrix, execution contracts and runtime, source bytes and manifests,
rights decisions, normalization, the 13 public schemas, and the five committed traces remain
unchanged.

The next bounded authoring slice completed on 2026-08-26 at feature commit `77d247d`. It added
exactly the two draft-only `kv-core-abstain-03` Korean/English records in
`data/benchmark/drafts/core-draft-007.jsonl`. The abstain pair binds no document or data units and
carries no tool expectations or reference answer, only a language-matched abstention reason: both
questions rest on the false premise that the many archived OECD editions of Korea's consumer price
index prove the Korean CPI was revised just as many times, and ask for before-and-after November
2019 CPI values using only the vintage available as of 2026-07-17. The gold behavior is to reject
that premise and abstain: archived edition counts measure archive coverage, not actual revisions,
and KOR-RTD holds no owner-approved raw-data decision for the OECD Korea CPI revision series;
raw OECD observations outside the sole approved scope (Korea's monthly amplitude-adjusted CLI,
`KOR.M.LI_AA.IX._T`, ADR 0007) remain metadata-only, so no before-and-after CPI observation can
be served and the system must not fabricate revision values or expose an unapproved observation.
Neither record has named review metadata or enters `core/`, so the approved core remains 14/40:
two draft records are pending review and 24 matrix slots remain unauthored and unapproved.

The frozen matrix, execution contracts and runtime, source bytes and manifests, rights decisions,
normalization rules, approved core, 13 public schemas, and five committed traces are unchanged.
The exact next independent slice is only named human review of those two drafts. Do not pre-approve
or move them into `core/`, increase the approved count, or select or author a later pair before
that decision. Provider or live-model integration remains absent, and the bounded tool loop
deferred by ADR 0008 remains outside this authoring slice.
