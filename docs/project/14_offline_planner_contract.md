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

Add only the deterministic evidence-packet assembler over an already validated request, route plan,
and ordered typed results. Keep dispatcher coordination, the offline executor, committed
end-to-end traces, and live model integration in later reviewable slices.
