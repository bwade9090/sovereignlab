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

No benchmark draft is pending and no later matrix pair has been selected. The current next step is
to await a separate explicit instruction before selecting or authoring another pair or opening a
new implementation slice. Provider or live-model integration remains absent, and the bounded tool
loop deferred by ADR 0008 remains outside the completed approval slice.
