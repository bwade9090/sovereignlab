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
payloads, or parser text. The completed private executor maps the appropriate internal rejection
into the already frozen execution failure model without changing this assembler boundary.

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
At that checkpoint, neither record had named review metadata or entered `core/`, so the approved
core remained 12/40: two draft records were pending review and 26 matrix slots remained
unauthored and unapproved.

That review gate completed on 2026-08-26 at approval feature commit `4c29b1d`. Hyungbae Cho
approved exactly the two `kv-core-abstain-02` records, which now live in
`data/benchmark/core/core-batch-006.jsonl`; the approved core is now 14/40. This was a
lifecycle-only transition: questions, answers, cutoff, tool expectations, the frozen matrix,
execution contracts and runtime, source bytes and manifests, rights decisions, normalization,
the 13 public schemas, and the five committed replay traces remain unchanged. This approval makes
`kv-core-abstain-02` the second approved abstain pair, after `kv-core-abstain-01`, and the first
approved pair whose fail-closed basis is a rights boundary rather than the availability ledger.

The next bounded authoring slice completed on 2026-08-26 at feature commit `77d247d`. It added
exactly the two draft-only `kv-core-abstain-03` Korean/English records in
`data/benchmark/drafts/core-draft-007.jsonl` and six focused tests in
`tests/benchmark/test_cpi_revision_abstain_draft.py`: an abstention pair on the train split whose
questions rest on the false premise that the many archived OECD editions of Korea's consumer
price index prove the Korean CPI was revised just as many times, and ask for before-and-after
November 2019 CPI values using only the vintage available as of 2026-07-17. The drafted gold
behavior is to reject the premise and abstain: archived edition counts measure archive coverage,
not actual revisions, and KOR-RTD holds no owner-approved raw-data decision for the OECD Korea
CPI revision series. Raw OECD observations outside the sole approved Korea monthly
amplitude-adjusted CLI scope (`KOR.M.LI_AA.IX._T`, ADR 0007) remain metadata-only, so no
before-and-after CPI observation can be served and the system must not fabricate revision values
or expose an unapproved observation. The pair binds no document or data units, carries no tool
expectations and no reference answer, only a language-matched abstention reason. The focused
tests prove that the rights catalog's only OECD decision is the approved CLI scope, that the
serialized records leak no observation value and no snapshot identifier, and that the only
approved CPI evidence in KOR-RTD (the KOSIS latest-only snapshot) has
`vintage_semantics=latest_only`, so committed evidence cannot serve any CPI revision by
construction. This is the third authored abstain pair, after `kv-core-abstain-01` and
`kv-core-abstain-02`, and the first false-premise rejection pair. At that checkpoint, neither
record had named review metadata or entered `core/`, so the approved core remained 14/40: two
draft records were pending review and 24 matrix slots remained unauthored and unapproved.

That review gate completed on 2026-08-26 at approval feature commit `5e14119`. Hyungbae Cho
approved exactly the two `kv-core-abstain-03` records, which now live in
`data/benchmark/core/core-batch-007.jsonl`; the approved core is now 16/40. This was a
lifecycle-only transition: questions, answers, cutoff, tool expectations, the frozen matrix,
execution contracts and runtime, source bytes and manifests, rights decisions, normalization,
the 13 public schemas, and the five committed replay traces remain unchanged. This approval makes
`kv-core-abstain-03` the third approved abstain pair, after `kv-core-abstain-01` and
`kv-core-abstain-02`, and the first approved false-premise rejection pair.

The next bounded authoring slice completed on 2026-08-26 at feature commit `fd7640b`. It added
exactly the two draft-only `kv-core-abstain-04` Korean/English records in
`data/benchmark/drafts/core-draft-008.jsonl` and six focused tests in
`tests/benchmark/test_missing_as_of_abstain_draft.py`: an abstention pair on the dev split (the
second dev-split pair, after `kv-core-data-04`) whose questions ask for Korea's OECD
amplitude-adjusted CLI value for May 2026 using the vintage available at the time, while omitting
the as-of date the vintage request depends on. The drafted gold behavior is to ask for the
missing as-of and abstain: a vintage answer depends on its as-of cutoff, and KOR-RTD's
fail-closed contract never executes without an explicit `effective_as_of` and never guesses or
defaults the cutoff, because an assumed cutoff can expose the wrong vintage and create temporal
leakage. The pair binds no document or data units, carries no tool expectations and no reference
answer, only a language-matched abstention reason; the record-level `as_of` is 2026-07-17. The
focused tests prove that the questions contain no as-of phrase while both abstention reasons
demand an explicit `effective_as_of`, that the serialized records leak no observation value and
no snapshot or ledger identifier, and that the same request resolves once an explicit cutoff of
2026-07-09 is supplied (edition `202607`, value `102.66` from the owner-approved CLI scope), so
the drafted abstention is missing-cutoff driven, not availability- or rights-driven. This is the
fourth authored abstain pair, after `kv-core-abstain-01` through `kv-core-abstain-03`, and the
first missing-as-of clarification pair. Neither record has named review metadata or enters
`core/`, so the approved core remains 16/40: two draft records are pending review and 22 matrix
slots remain unauthored and unapproved.

The frozen matrix, execution contracts and runtime, source bytes and manifests, rights decisions,
normalization rules, approved core, 13 public schemas, and five committed traces are unchanged.
The exact next independent slice is only named human review of those two drafts. Do not pre-approve
or move them into `core/`, increase the approved count, or select or author a later pair before
that decision. Provider or live-model integration remains absent, and the bounded tool loop
deferred by ADR 0008 remains outside this authoring slice.
