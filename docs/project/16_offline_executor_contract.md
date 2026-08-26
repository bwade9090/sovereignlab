# Private offline executor

Status: work-unit-C executor slice implemented offline on 2026-08-11.

## Purpose and boundary

This specification records the eighth independently reviewable ADR 0008 implementation slice: a
private offline executor that coordinates one existing `Planner`, the frozen explicit dispatcher,
and the private evidence-packet assembler. It consumes one exact validated `ExecutionRequest` plus
harness-owned trace metadata and committed tool registry, then returns only the existing
`ExecutionTrace` 1.0.0 model.

The implementation remains internal to `sovereignlab.execution.executor` as
`_execute_offline_request`. It adds no public executor function, protocol, result wrapper, provider
envelope, recording format, or JSON Schema. The executor slice itself did not add a committed
end-to-end replay trace, provider or live-model call, source capture, benchmark record, or paid
operation. The public schema count remains 13. The subsequent ninth work-unit-C slice shipped five
real-digest replay traces at feature commit `883815b` without changing this private boundary.

## Harness-owned inputs

The private boundary accepts only five keyword arguments:

- a valid trace ID fixed by the harness;
- an explicit UTC `recorded_at` instant, with no implicit wall-clock read;
- one exact `ExecutionRequest` whose effective cutoff is already fixed;
- one implementation of the existing one-shot `Planner` protocol; and
- one exact committed `CallableToolRegistry`.

The caller cannot supply execution-environment provenance, planner provenance, paths, manifests,
ledgers, registry descriptors, artifact bytes, provider payloads, or credentials. The executor
strictly round-trips the request and every public model it consumes or returns, rejects subclasses
and mutable substitutes at the relevant exact-model boundaries, and gives the planner a private
validated request copy.

## One-shot state machine

The executor performs one bounded sequence:

1. validate trace metadata, request, execution environment, and planner provenance;
2. invoke `Planner.plan` exactly once and revalidate the returned plan against the original request;
3. dispatch the validated calls once each in their frozen order;
4. stop immediately after the first `abstained` or `error` result;
5. skip packet assembly after a tool error, otherwise invoke the private assembler once; and
6. construct and strictly round-trip one terminal `ExecutionTrace`.

No tool result can add, remove, reorder, or rewrite a later call. The executor never replans from a
tool result. It preserves the plan's four route meanings, copies the exact ordered result prefix,
and relies on the completed dispatcher and assembler boundaries for their frozen call/result and
evidence invariants.

| Plan and ordered result state | Terminal trace |
| --- | --- |
| Planned abstention, no calls | `abstained`; no results; empty packet with the exact plan reason |
| Successful prefix ending in one tool abstention | `abstained`; terminal result retained; empty tool-origin packet |
| Every planned call succeeds | `complete`; full ordered results and exact complete packet |
| Successful prefix ending in one typed tool error | `failed / tool_execution`; no packet; failure equals the terminal result error |
| Planner failure before a validated plan | `failed / planner`; no plan, results, or packet |
| Planner reports `plan_validation_failed` with digest-linked candidate provenance | `failed / plan_validation`; no plan, results, or packet |
| Packet assembly fails after a full all-success sequence or zero-call planned abstention | `failed / packet_assembly`; no packet; validated plan and eligible results retained |

An abstained packet never exposes a successful prefix as evidence. A failed trace never contains an
evidence packet.

## Private rejection and failure mapping

Failures that fit the frozen trace contract return a sanitized `ExecutionFailure`; conditions for
which no truthful `ExecutionTrace` can be built raise private `_OfflineExecutorError` instead.
Neither boundary copies internal exception text, paths, artifact contents, provider data, or secret
values.

The executor maps planner outcomes as follows:

- the existing sanitized `plan_validation_failed` code maps to `plan_validation` only when the
  planner provenance includes both recording ID and exact candidate-output SHA-256;
- other recognized planner errors map to `planner`, while unknown exceptions become the stable
  `planner_failed` failure;
- an invalid object returned as a plan, any changed or invalid private request copy with either a
  return or exception, or another invalid planner result becomes `planner_result_invalid` in the
  `planner` phase; and
- missing or changed planner provenance or a digestless claimed plan-validation failure is a
  private rejection because the required trace provenance is unavailable or inconsistent.

For tool execution, recognized `ToolDispatchError` codes are mapped through a fixed sanitized
allowlist. Unexpected dispatch exceptions become `tool_dispatch_failed`. A changed private call,
wrong result class, result identity or payload drift, or failed strict result round-trip becomes a
call-bound `tool_result_invalid` error. Every dispatch attempt is followed by execution-environment
revalidation; provenance drift is a private rejection rather than a trace containing a stale
environment claim. Execution stops after the first non-success result.

Packet-assembly codes are also reduced to a private allowlist with one stable public-safe message.
A packet failure after full success, and a zero-call planned-abstention packet failure, fit the
existing `packet_assembly` trace shape. The frozen trace model cannot represent packet assembly
failure after a terminal tool abstention because that phase requires a complete successful result
sequence; that impossible state therefore raises the private
`untraceable_packet_assembly_failure` rejection and exposes no trace or partial evidence.

Invalid initial request, trace metadata, planner boundary, registry provenance, source descriptor,
or terminal trace round-trip also remains a private rejection. These private diagnostic labels are
not a new public failure contract.

## Execution-environment provenance

The executor ID is `sovereignlab-offline-executor-v1`. Its `executor_sha256` is computed from a
canonical descriptor over the complete Python source tree under `src/sovereignlab`, not copied from
the callable-registry digest and not supplied by the caller.

Descriptor construction recursively enumerates every `*.py` entry, rejects symbolic links,
non-files, empty bytes, paths resolving outside the source root, and duplicate relative paths,
normalizes CRLF and bare CR line endings to LF, and records each POSIX-style repository-relative
path with the SHA-256 of its canonical source bytes. The final compact UTF-8 JSON object uses sorted
keys and also binds:

- execution contract version `1.0.0`;
- the executor ID;
- callable registry ID `sovereignlab-deterministic-tool-registry-v1`; and
- the frozen callable-registry descriptor SHA-256.

The descriptor contains hashes rather than source bodies and contains no absolute workstation
path. Any source addition or change to canonicalized SovereignLab Python content changes the
executor digest; a line-ending representation change alone does not. The completed slice pins 32
source entries and executor digest
`08f45dab6a36a49cb7d0b588a69236942cd61534540bd4de0772010402dada64`. This is repository-source
provenance, not a claim to hash the Python interpreter, operating system, or third-party binary
environment.

The remaining six `ExecutionEnvironmentProvenance` fields come only from
`CallableToolRegistry.provenance()`: the real callable registry, composite snapshot/STES artifact
registry, and complete temporal retrieval corpus IDs and descriptor digests. The executor rebuilds
the strict environment model and rechecks it after planning, after every dispatch attempt, and
before any terminal trace. Planner provenance is likewise rebuilt and compared before terminal
return. A changed source tree, registry, corpus, planner candidate identity, or digest cannot
silently reuse the initial trace provenance.

## Hard stops preserved

- Do not expose the executor, private assembler, or planner-recording internals as package-level
  public APIs or schemas.
- Do not accept model-selected paths, manifests, ledgers, raw bytes, provenance, or credentials.
- Do not continue dispatch after abstention or error, and do not expose partial evidence.
- The executor slice itself did not commit end-to-end replay fixtures; the existing contract
  fixture remains illustrative and is not an executor result. The subsequent trace slice generated
  its artifacts through the real boundary rather than hand-authoring substitute provenance.
- The executor and trace slices added no provider or live-model call, source capture, benchmark
  record, or public-schema change.
- Do not start the bounded tool loop deferred by ADR 0008.

## Validation procedure

The focused executor checks must be run with Python 3.12 and a fresh OS `--basetemp` on the Windows
workstation because the unchanged ignored repository `.pytest_tmp` retains its documented deny
ACL. The required commands are:

```powershell
$freshExecutorBasetemp = Join-Path ([IO.Path]::GetTempPath()) ('sovereignlab-executor-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $freshExecutorBasetemp -ErrorAction Stop | Out-Null
& $venvPython -m ruff check --no-cache src/sovereignlab/execution/executor.py tests/execution/test_executor.py
& $venvPython -m ruff format --check src/sovereignlab/execution/executor.py tests/execution/test_executor.py
& $venvPython -m pytest tests/execution/test_executor.py --cov=sovereignlab.execution.executor --cov-branch --cov-report=term-missing -p no:cacheprovider --basetemp $freshExecutorBasetemp
& $venvPython scripts/export_json_schemas.py
git diff --exit-code -- data/schemas
& $venvPython -m ruff check --no-cache .
& $venvPython -m ruff format --check .
$freshFullBasetemp = Join-Path ([IO.Path]::GetTempPath()) ('sovereignlab-full-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $freshFullBasetemp -ErrorAction Stop | Out-Null
& $venvPython -m pytest --cov=sovereignlab --cov-branch --cov-report=term-missing -p no:cacheprovider --basetemp $freshFullBasetemp
git diff --check
```

The completed focused acceptance run covers all four routes, all three real committed adapters,
Korean and English document execution, explicit and implicit cutoffs, cutoff-safe document
exclusion, deterministic JSON output, ordered terminal stopping, every traceable failure phase,
strict model and provenance drift, sanitized private rejection, package-export privacy, and the
unchanged 13-schema surface. It passes 66 tests with 100% executor coverage over 326 statements and
98 branches. The full offline run passes 1,115 tests with 100% SovereignLab coverage over 4,679
statements and 1,568 branches; Ruff confirms 69 formatted Python files. Both pytest runs use fresh
OS temporary directories and leave the repository `.pytest_tmp` ACL untouched.

## Next independent slice

The ninth independently reviewable ADR 0008 work-unit-C slice shipped on 2026-08-11 at feature
commit `883815b`.
Five deterministic JSON traces under `traces/replay/v1/` were generated through this real private
executor, `ScriptedPlanner`, callable and artifact registries, and temporal retrieval corpus, then
checked by exact-byte replay. The first nine work-unit-C slices are complete, the public schema
count remains 13, and the minimal offline briefing path has shipped. Its public description is
exactly `typed function calling with committed traces`.

Trace 005 makes terminal behavior reviewable: the document call succeeds, the following snapshot
call abstains, and the later planned valid STES call is not dispatched. Its evidence packet is
empty, so the earlier document result cannot leak as partial evidence. The healthy exact committed
stack does not naturally emit planner, tool, or packet-assembly faults; those semantics remain in
the strict schema and executor regression coverage rather than monkeypatched end-to-end artifacts.

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

No benchmark draft is pending and 24 matrix slots remain unauthored and unapproved. The
owner-directed next outcome is a bounded draft-only authoring slice for the frozen
`kv-core-abstain-04` pair: an abstention pair on the dev split whose question asks for a
historical-vintage value while omitting its as-of date; the gold behavior is to abstain (or ask
for the missing as-of), because the fail-closed contract never executes without an explicit
`effective_as_of` and never guesses or defaults the cutoff. The pair binds no source units and
is fully offline. The new drafts must stay `annotation.status=draft` pending a separate named
human review. Provider or live-model integration remains absent, and the bounded tool loop
deferred by ADR 0008 remains outside the completed approval slice.
