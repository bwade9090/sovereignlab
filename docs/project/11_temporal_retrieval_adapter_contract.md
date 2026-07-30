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

The trusted historical registry and flat `resolve_stes_as_of` adapter are now complete under
`docs/project/12_stes_adapter_contract.md`. The frozen three-tool registry and explicit dispatcher
are complete under `docs/project/13_callable_dispatcher_contract.md`. Add only the planner
protocol with scripted and immutable recorded/replay implementations next. Packet assembly, the
offline executor, committed end-to-end traces, and live model integration remain later
reviewable slices.
