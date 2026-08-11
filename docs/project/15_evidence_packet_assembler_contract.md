# Deterministic evidence-packet assembler

Status: work-unit-C assembler slice implemented offline on 2026-08-07.

## Purpose and boundary

This specification records the seventh independently reviewable ADR 0008 implementation slice:
an entirely offline deterministic boundary that consumes one already validated
`ExecutionRequest`, its validated `RoutePlan` 1.0.0, and the ordered typed tool results produced
elsewhere. It returns only the existing `ExecutionEvidencePacket` 1.0.0.

The implementation is internal to `sovereignlab.execution.assembler`. It does not add a public
assembler function, protocol, result wrapper, error model, or JSON Schema. It does not invoke the
planner or dispatcher, coordinate tool calls, construct an `ExecutionTrace`, read a provider,
create a source capture or benchmark record, make a live model call, or perform a paid operation.

## Strict input revalidation

The boundary accepts exact built-in model instances and an exact tuple of results. Before evidence
use it strictly round-trips the request, plan, and each registered result through canonical JSON.
It rejects subclasses, raw dictionaries, mutable sequence substitutes, post-construction model
mutation, changed round-trip results, and unregistered result types. Every successful call returns
a freshly rebuilt packet rather than retaining caller-owned input models.

The validated plan is bound back to the request before result assembly:

1. every call cutoff must equal `ExecutionRequest.effective_as_of`;
2. every documentary call must preserve the request question and language exactly; and
3. every result must match the corresponding call ID and tool in an ordered plan prefix.

The shared strict call/result validator in `sovereignlab.schemas.execution` remains authoritative
for documentary `top_k`, per-result chunk uniqueness and deterministic order, documentary language
and publication cutoff, and the exact STES or snapshot argument-to-payload bindings.

## Outcome semantics

The four frozen route meanings are preserved without adding another route or intermediate model.

| Plan and ordered results | Packet outcome |
|---|---|
| Planned abstention and no results | Empty `abstained` packet with the exact plan reason |
| Non-abstain route ending in one abstention after a successful prefix | Empty `abstained` packet bound to the terminal call and exact tool reason |
| Full planned sequence with every result successful | `complete` packet containing the exact successful payloads |
| Missing, extra, reordered, mismatched, erroneous, or otherwise incomplete results | Fail-closed rejection; no packet |

A tool abstention never exposes earlier successful payloads. Complete packets flatten documentary
matches in result order and then preserve each result's internal match order. Data observations are
preserved in result order. The assembler does not filter, deduplicate, sort, normalize, or augment
typed evidence. Consequently, equal evidence returned by distinct valid calls remains repeated in
the packet.

## Strict output validation

Every candidate packet is strictly round-tripped through the existing
`ExecutionEvidencePacket` model before return. This final check reuses the frozen route-shape,
abstention-origin, no-partial-evidence, documentary cutoff, observation cutoff, and typed payload
invariants. An output that changes during round-trip or cannot satisfy that model is rejected.

## Private failure taxonomy

The internal boundary distinguishes invalid requests, plans, result sequences, typed results,
request/plan drift, incomplete success, tool errors presented as evidence, output validation
failure, and unexpected internal failure. These labels are private diagnostics, not a new public
failure contract. Unexpected validation details are sanitized rather than exposing raw paths,
payloads, or parser text. A later executor may map the appropriate internal rejection into the
already frozen execution failure model without changing this assembler boundary.

## Validation evidence

Focused tests cover all four routes, Korean/English requests, explicit and implicit cutoffs,
planned and tool abstention reason binding, no partial-evidence leakage, complete documentary and
data assembly, ordering and cross-call duplicate preservation, strict `top_k` and per-result
duplicate rejection, request/plan/result drift, post-cutoff evidence, incomplete success, tool
errors, exact-model and tuple enforcement, sanitized failures, deterministic fresh output, strict
packet round-trip, private exports, and forbidden execution dependencies. The focused assembler
suite passes 42 tests with 100% statement/branch coverage (115 statements, 56 branches).

The full repository baseline is recorded in `docs/PROJECT_STATUS.md` after the implementation
slice's final validation.

## Next independent slice

The private offline executor is complete at functional commit `550b591` and is specified in
`docs/project/16_offline_executor_contract.md`. It coordinates the completed planner, frozen
dispatcher, and private assembler once and in order while preserving the existing `ExecutionTrace`
1.0.0 surface; the 13 public schemas remain unchanged.

The exact next reviewable slice is only the committed machine-readable end-to-end replay traces.
Those traces must use the real executor and bind the real registry, corpus, planner, and executor
provenance identifiers and digests. The existing contract fixture is not an end-to-end replay
result, and the minimal typed function-calling path is not shipped until these traces are committed.

Keep provider or live-model integration in a later independent slice, and do not start the bounded
tool loop deferred by ADR 0008.
