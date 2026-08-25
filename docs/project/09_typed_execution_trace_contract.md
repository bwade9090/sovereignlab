# Typed execution and trace contract

Status: execution-contract slice 1.0.0 implemented offline on 2026-07-29.

## Purpose and boundary

This specification freezes the first reviewable slice of ADR 0008 work unit C: the strict
question, route-plan, typed-call/result, evidence-packet, and trace surface, together with the
flat gold arguments for the latest-only snapshot reader.

This contract slice did not itself implement the runtime adapters, trusted registries, planner
protocol, or end-to-end executor. The trusted snapshot registry and `read_snapshot_as_of` adapter
have since shipped under `docs/project/10_snapshot_reader_contract.md`, followed by the trusted
synthetic retrieval registry and typed `retrieve_temporal_documents` adapter under
`docs/project/11_temporal_retrieval_adapter_contract.md`. The trusted historical registry and flat
`resolve_stes_as_of` adapter have now shipped under
`docs/project/12_stes_adapter_contract.md`. The frozen three-tool callable registry and explicit
dispatcher have also shipped under `docs/project/13_callable_dispatcher_contract.md`, the
offline planner boundary has shipped under `docs/project/14_offline_planner_contract.md`, and the
deterministic evidence-packet assembler has shipped under
`docs/project/15_evidence_packet_assembler_contract.md`, and the private offline executor has
shipped under `docs/project/16_offline_executor_contract.md`. Five machine-readable, real-digest
end-to-end replay traces have since shipped under `traces/replay/v1/` at feature commit `883815b`.
This contract does not change `BenchmarkRecord` or `BenchmarkBundle` 2.0.0.

The independent execution contract is version 1.0.0. Its Pydantic source is
`src/sovereignlab/schemas/execution.py`.

## Request and single-shot route plan

`ExecutionRequest` records:

- a stable request ID;
- the Korean or English question and explicit language;
- the optional cutoff supplied by the requester; and
- an always-present `effective_as_of`.

When the requester supplies `as_of`, it must equal `effective_as_of`. When it is omitted, the
harness must choose and record `effective_as_of` before planning. No adapter may read an implicit
current date during replay.

`RoutePlan` preserves the four frozen routes:

- `documents`: at least one document call and no data call;
- `data`: at least one data call and no document call;
- `documents_and_data`: at least one of each;
- `abstain`: no calls and a required structured reason code/message.

Call IDs must be unique. The entire plan is fixed before deterministic execution; the schema has
no feedback, iteration, step-budget, or model-driven call-addition field.

## Exact callable surface

The callable registry contains exactly three names:

| Tool name | Flat argument fields |
| --- | --- |
| `retrieve_temporal_documents` | `question`, `language`, `as_of`, `top_k` |
| `resolve_stes_as_of` | `ref_area`, `freq`, `measure`, `unit_measure`, `activity`, `period`, `as_of`, `normalization_rule_id` |
| `read_snapshot_as_of` | `source_system`, `table_id`, `item_id`, `period`, `as_of`, `normalization_rule_id` |

The resolver arguments reproduce the committed `core-batch-001.jsonl` gold shape without
translation. In particular, the SDMX missing-code value `_T` remains valid.

The resolver contract cross-binds its dimensions, period frequency, and normalization rule for
the two frozen Korea normalization units: monthly CLI
`KOR.M.LI_AA.IX._T`/`YYYY-MM` and quarterly real GDP
`KOR.Q.B1GQ_Q.XDC._T`/`YYYY-Qn`. This is a normalization and call-validity rule, not a
redistribution authorization. The later trusted registry must return public raw evidence only for
the owner-approved OECD CLI scope; the GDP scope remains unavailable as public raw evidence under
the current rights catalog.

All models reject extra fields. A model cannot supply a source or capture ID, filesystem path,
URL, manifest, ledger, archive bytes, raw provider response, snapshot timestamp, KOSIS
organization/geography selectors, or credentials. Those values belong to the trusted harness.

## Latest-only snapshot gold convention

`read_snapshot_as_of` is deliberately named for its cutoff, not for an unconstrained notion of
"latest." Its six flat arguments are frozen to the currently approved latest-only units:

| Source | `table_id` | `item_id` | Provider-native period | Required normalization rule |
| --- | --- | --- | --- | --- |
| ECOS | `200Y108` | `10601` | quarterly `YYYYQn` | `ecos-200y108-10601-billion-krw-v1` |
| ECOS | `301Y017` | `SA000` | monthly `YYYYMM` | `ecos-301y017-sa000-million-usd-v1` |
| KOSIS | `DT_1J22003` | `T/T10` | monthly `YYYYMM` | `kosis-101-dt-1j22003-t-t10-index-v1` |

The KOSIS composite item is case-sensitive. The implemented adapter's trusted registry binds it
to `ORG_ID=101`, raw item `T`, geography `T10`, monthly frequency, the approved manifest family,
and the exact raw-unit mapping. None is model-selectable.

An unknown scope, neighboring item, mismatched normalization rule, wrong series frequency, or
extra artifact selector is an invalid call, not a scored abstention.

The runtime reader selects only a committed, owner-approved `latest_only` snapshot available
by the inclusive end of the call's `as_of` date in `Asia/Seoul`. Snapshot evidence already
enforces both `source_published_on <= as_of` and
`source_retrieved_at <= end-of-day(as_of, Asia/Seoul)`. The actual selection algorithm, content
parsers, registry digest, and safe-abstention taxonomy are frozen in
`docs/project/10_snapshot_reader_contract.md`.

## Results, normalization, and evidence packets

Each tool result is exactly one of:

- `success` with that tool's typed payload;
- `abstained` with a structured, sanitized reason; or
- `error` with a structured failure bound to the same call ID.

Document success is non-empty and records source ID/hash, language, publication date, locator,
text or excerpt, and deterministic score. Data success records only the selected observation and
its provenance. Latest-only snapshot evidence cannot carry an edition or availability ledger;
historical STES evidence requires both.

Normalization evidence preserves the raw string, rule ID, exact normalized string, canonical
unit, recommended display places, and display value. Contract validation replays the five frozen
normalization 1.0.0 multipliers and rejects an inconsistent normalized value, unit, precision, or
ROUND_HALF_UP display string.

`ExecutionEvidencePacket` separates `planned_route` from terminal packet status. A required tool
may safely abstain even after a non-abstain plan. Such a packet exposes no partial evidence;
ordered partial results remain available only in the trace. Packet abstention records whether it
came from the plan or a tool. A trace requires a planned abstention to equal the plan's reason and
a tool abstention to equal the terminal tool result's call ID, reason code, and message.

## Trace integrity and replay

`ExecutionTrace` stores the request, execution-environment provenance, planner provenance,
validated plan, ordered typed results, terminal packet or sanitized failure, and a UTC recording
instant.

The environment provenance digest-links the executor, callable registry, trusted artifact
registry, and complete retrieval corpus. The corpus digest covers eligible inputs that affect
scores even when their chunks are not returned. IDs are opaque stable registry keys; SHA-256
values are over the exact canonical bytes resolved by the harness. This avoids defining replay as
"whatever files happen to be present now."

Validation enforces:

- every call cutoff equals `effective_as_of`;
- a document call cannot rewrite the request question or language;
- results are an exact ordered prefix of the planned calls, with matching IDs and tool names;
- document results cannot exceed `top_k`, repeat a chunk ID, or violate the retriever's
  score/source/chunk ordering;
- complete traces contain every successful result and a byte-equivalent assembled evidence
  payload at the model level;
- tool abstention and tool failure terminate an otherwise successful prefix;
- planner/plan-validation failures contain no execution data;
- packet-assembly failure follows a complete successful result sequence; and
- post-cutoff documentary or latest-only evidence is rejected.

Planner provenance supports `scripted`, immutable `recorded`, and `replay` modes. A recording ID
and output SHA-256 must appear together. Recorded and replay entries also require a model ID;
scripted entries forbid one but may digest-link an invalid or valid candidate fixture. A
`plan_validation` failure must carry this digest link so the rejected bytes can be independently
replayed. The recording ID is resolved through a trusted recording registry, and `output_sha256`
hashes its exact recorded candidate bytes. Provider-native response envelopes are not embedded in
the canonical trace.

`data/fixtures/execution_trace.example.json` is the committed round-trip example. Its document
passage and document hash are explicitly synthetic; no Bank of Korea report body or extracted
provider text is committed. Its data observation points to the already committed, owner-approved
ECOS snapshot and preserves that snapshot's provenance. The environment IDs and repeated-letter
hashes remain deliberately illustrative synthetic values rather than the real registry values
that later slices have now frozen; this file validates the contract and is not claimed as an
end-to-end replay artifact.

## Public JSON Schemas

The deterministic exporter now produces thirteen schemas: the original seven plus:

- `route-plan-v1.schema.json`;
- `execution-evidence-packet-v1.schema.json`;
- `execution-trace-v1.schema.json`;
- `retrieve-temporal-documents-arguments-v1.schema.json`;
- `resolve-stes-as-of-arguments-v1.schema.json`; and
- `read-snapshot-as-of-arguments-v1.schema.json`.

The callable schemas describe only canonical arguments. Provider request/response envelopes and
tool-call ID formats remain behind the future planner boundary. JSON Schema validates the
provider-facing structure, enums, required discriminators, and closed property sets. Cross-field
rules such as route/call consistency and scope/rule pairing are Pydantic validators, so the
harness must always perform Pydantic validation after JSON Schema validation and before executing
any call.

## Next independent slice

The ninth independently reviewable ADR 0008 work-unit-C slice shipped on 2026-08-11 at feature
commit `883815b`.
Five deterministic JSON traces under `traces/replay/v1/` were generated through the real private
executor, `ScriptedPlanner`, callable and artifact registries, and temporal retrieval corpus, then
checked by exact-byte replay. The first nine work-unit-C slices are complete, the public schema
count remains 13, and the minimal offline briefing path has shipped. Its public description is
exactly `typed function calling with committed traces`.

The healthy exact committed stack naturally reproduces complete, planned-abstention, and terminal
tool-abstention outcomes. Planner, tool, and packet-assembly fault semantics remain covered by the
strict schema and executor regressions; they were not misrepresented as monkeypatched end-to-end
artifacts. The illustrative `data/fixtures/execution_trace.example.json` remains a contract fixture,
not an end-to-end replay result.

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
basis even though the approved scope itself resolves at that cutoff. Neither record has named
review metadata or enters `core/`, so the approved core remains 12/40: two draft records are
pending review and 26 matrix slots remain unauthored and unapproved.

The frozen matrix, execution contracts and runtime, source bytes and manifests, rights decisions,
normalization rules, approved core, 13 public schemas, and five committed traces are unchanged.
The exact next independent slice is only named human review of those two drafts. Do not pre-approve
or move them into `core/`, increase the approved count, or select or author a later pair before
that decision. Provider or live-model integration remains absent, and the bounded tool loop
deferred by ADR 0008 remains outside this authoring slice.
