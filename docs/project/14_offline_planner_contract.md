# Offline one-shot planner boundary

Status: work-unit-C planner slice implemented offline on 2026-08-02.

## Purpose and boundary

This specification records the sixth independently reviewable ADR 0008 implementation slice: a
one-shot planner protocol plus scripted and immutable recorded/replay implementations. The planner
consumes one already validated `ExecutionRequest` and returns the existing `RoutePlan` 1.0.0.

The slice does not change `BenchmarkRecord`, `BenchmarkBundle`, execution contract 1.0.0, or the
13 public JSON Schemas. It adds no public planner-result/provider-envelope/recording schema,
dispatcher call, packet assembler, route executor, end-to-end trace, source capture, benchmark
record, provider request, live model call, or paid operation.

## Protocol and provenance

`sovereignlab.execution.planner.Planner` exposes only:

- `plan(request) -> RoutePlan`; and
- a separate `PlannerProvenance` property.

There is no new result wrapper. `ScriptedPlanner` freezes exact canonical bytes from one validated
plan template and records a script ID plus candidate SHA-256 without a model ID. `RecordedPlanner`
and `ReplayPlanner` resolve an opaque recording ID through a harness-owned private immutable
registry and require the complete recording ID, exact output SHA-256, and model ID mandated by
`PlannerProvenance`.

The internal recording entry and registry are deliberately private. This slice freezes neither a
repository recording-file format nor a public recording-registry ID. A later live-model or
committed-recording unit must record those choices if they become consequential.

## Exact-byte candidate validation

Every invocation reparses fresh exact built-in `bytes` rather than returning a stored model. The
recording registry revalidates its immutable tuple shape, unique IDs, exact byte type, bounded
size, metadata, and SHA-256 before resolution. Recorded/replay planners then independently compare
the resolved ID, digest, and model ID with the metadata frozen at construction and hash the exact
candidate bytes again.

Candidate parsing rejects invalid UTF-8/JSON, non-object roots, duplicate JSON keys, non-finite
constants, extra fields, unknown or mismatched tool discriminators, invalid arguments, duplicate
call IDs, and route/call inconsistency. The candidate is validated directly as the already public
`RoutePlan` with strict JSON semantics; no provider-native envelope enters the canonical boundary.

Missing or corrupt recordings fail before plan validation. Invalid but digest-valid candidate
bytes raise a sanitized `PlannerError` carrying their complete `PlannerProvenance`, so the later
executor can construct the digest-linked `plan_validation` failure required by `ExecutionTrace`.
No raw candidate bytes or parser exception text are copied into the error.

## Request binding before dispatch

The planner round-trips the exact `ExecutionRequest` model and enforces, before any later
dispatcher can run:

1. every call's `as_of` equals `ExecutionRequest.effective_as_of`; and
2. every document call preserves the request's question and language exactly.

This supplements `RoutePlan`'s existing four-route, typed-call, and unique-call-ID invariants.
Each successful call returns a freshly parsed plan, so caller mutation of a returned plan or
provenance object cannot change later replay.

## Validation evidence

Focused tests cover all four routes, Korean/English requests, explicit and implicit cutoffs,
scripted/recorded/replay provenance, deterministic repeated replay, exact-byte and metadata
mutation, missing recordings, malformed candidates, extra fields, unknown/mismatched tools,
duplicate call IDs and JSON keys, inconsistent routes, and request-binding drift. The focused
planner suite passes 31 tests with 100% statement/branch coverage (172 statements, 44 branches).

The full repository baseline is recorded in `docs/PROJECT_STATUS.md` after the implementation
slice's final validation.

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
`data/benchmark/core/core-batch-004.jsonl`; the approved core is now 10/40. This was a
lifecycle-only transition: questions, answers, cutoff, tool expectations, the frozen matrix,
execution contracts and runtime, source bytes and manifests, rights decisions, normalization,
the 13 public schemas, and the five committed replay traces remain unchanged.

The next bounded authoring slice completed on 2026-08-21 at feature commit `5e0da06`. It added
exactly the two draft-only `kv-core-data-04` Korean/English records in
`data/benchmark/drafts/core-draft-005.jsonl`, using only
`kosis-cpi-snapshot-20260717`, whose use in KOR-RTD is owner-approved (ADR 0007). At that
checkpoint, neither record had named review metadata or entered `core/`, so the approved core
remained 10/40: two draft records were pending review and 28 matrix slots remained unauthored and
unapproved.

That review gate completed on 2026-08-25 at approval feature commit `95c5e61`. Hyungbae Cho
approved exactly the two `kv-core-data-04` records, which now live in
`data/benchmark/core/core-batch-005.jsonl`; the approved core is now 12/40. This was a
lifecycle-only transition: questions, answers, cutoff, tool expectations, the frozen matrix,
execution contracts and runtime, source bytes and manifests, rights decisions, normalization,
the 13 public schemas, and the five committed replay traces remain unchanged. This approval
completes the data route's four authorable pairs (`kv-core-data-01`..`kv-core-data-04`); the
fifth data pair `kv-core-data-05` stays reserved on the deliberately unauthored test-split unit.

The next bounded authoring slice completed on 2026-08-25 at feature commit `c20619d`. It added
exactly the two draft-only `kv-core-abstain-02` Korean/English records in
`data/benchmark/drafts/core-draft-006.jsonl`: an abstention pair on the train split whose
questions ask for Korea's OECD normalised CLI value for May 2026 using only the vintage available
as of 2026-07-09. That neighboring measure sits outside the sole owner-approved OECD raw-data
scope (Korea's monthly amplitude-adjusted CLI, `KOR.M.LI_AA.IX._T`, ADR 0007), so the drafted
gold behavior is abstention on the missing rights basis: the pair binds no document or data units
and uses no new evidence, only the committed rights catalog as the fail-closed basis, and its
language-matched abstention reasons name the approved scope, forbid substituting the approved
series or exposing an unapproved observation, and leak no observation value. The cutoff is
deliberately one where the approved scope does resolve, so the abstention is rights-driven, not
availability-driven. This is the second abstain pair, after `kv-core-abstain-01`, and the first
authored pair whose fail-closed basis is a rights boundary rather than the availability ledger.
Neither record has named review metadata or enters `core/`, so the approved core remains 12/40:
two draft records are pending review and 26 matrix slots remain unauthored and unapproved.

The frozen matrix, execution contracts and runtime, source bytes and manifests, rights decisions,
normalization rules, approved core, 13 public schemas, and five committed traces are unchanged.
The exact next independent slice is only named human review of those two drafts. Do not pre-approve
or move them into `core/`, increase the approved count, or select or author a later pair before
that decision. Provider or live-model integration remains absent, and the bounded tool loop
deferred by ADR 0008 remains outside this authoring slice.
