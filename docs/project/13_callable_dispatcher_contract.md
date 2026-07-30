# Frozen callable registry and dispatcher

Status: work-unit-C dispatcher slice implemented offline on 2026-07-30.

## Purpose and boundary

This specification records the fifth independently reviewable ADR 0008 implementation slice: the
frozen three-tool callable registry, the composite data-artifact registry descriptor, and the
explicit deterministic dispatcher over the three previously implemented adapters.

The slice does not change `BenchmarkRecord`, `BenchmarkBundle`, execution contract 1.0.0, or the 13
public JSON Schemas. It adds no planner implementation, packet assembler, route executor,
end-to-end trace, source capture, benchmark record, provider request, live model call, or paid
operation.

## Exact callable surface

Registry `sovereignlab-deterministic-tool-registry-v1` contains exactly:

| Tool | Typed adapter ID | Trusted dependency |
| --- | --- | --- |
| `retrieve_temporal_documents` | `sovereignlab-temporal-document-adapter-v1` | synthetic temporal corpus |
| `resolve_stes_as_of` | `sovereignlab-stes-as-of-adapter-v1` | historical STES registry |
| `read_snapshot_as_of` | `sovereignlab-snapshot-as-of-adapter-v1` | latest-only snapshot registry |

Each registration binds the exact argument, call, and result model identities plus the SHA-256 of
the canonical Pydantic argument schema. The frozen hashes are:

| Tool | Canonical argument-schema SHA-256 |
| --- | --- |
| `retrieve_temporal_documents` | `c6980e23bf3c2ca56fb7de25f9a09b8525b1504bca8380394d44a31632d28a78` |
| `resolve_stes_as_of` | `0190aaa35e6e90d120ebe5a6c1f58f109f109fde03f966b509eb9d113e39a969` |
| `read_snapshot_as_of` | `c9d062ab47e20907d4b5cfd2a996442ea1d6b8b920ce3eef6bbd84b03101fad9` |

The canonical callable descriptor is order-independent and has SHA-256
`cd00b5c543cffc53024f98b9fafa73ed3fecd519fde81a826d060c8af4d2ad91`.
It contains no function representation, local path, URL, manifest, ledger, raw bytes, source row,
or evidence value. Executable-code provenance remains the later executor digest's responsibility.

The registry returns a fresh argument schema for a validated `ToolName`; mutating the returned
dictionary cannot alter the frozen registration. A raw string, unknown name, or missing
registration fails before execution.

## Replay provenance

Execution contract 1.0.0 has one `artifact_registry_*` pair even though deterministic data is held
by two independently frozen registries. The dispatcher therefore defines composite registry
`kor-rtd-execution-artifact-registry-v1`, whose descriptor binds:

- snapshot registry `kor-rtd-latest-only-snapshot-registry-v1` and digest
  `67ebecf0aa15b5a2d53aff737cd28bd8779e3993abebca9e6c3d840f2006aa5b`; and
- STES registry `kor-rtd-stes-resolver-registry-v1` and digest
  `103eb3bea7beebadeb0a7e193ff76fc95b518a8a7bed6825d9eb1f25431fb420`.

Its canonical descriptor SHA-256 is
`7b42027c1034789bd46a881fd186f66ba1ba1250d94639ff5eed6c89a3cc2293`.

The temporal corpus remains separate, matching the dedicated `retrieval_corpus_*` trace fields:
ID `synthetic-temporal-retrieval-corpus-v1`, digest
`823117ee29a191bc306843e44ccd9d37e063db79cc87e15dcb7f2a11f5b5bf7e`.

`CallableToolRegistry.provenance()` exposes exactly those six real registry ID/digest values for
later `ExecutionEnvironmentProvenance` construction. A changed child registry cannot silently
reuse the v1 composite digest.

## Explicit dispatch boundary

`dispatch_tool_call` accepts only an exact already-validated
`TemporalDocumentCall`, `StesAsOfCall`, or `SnapshotAsOfCall` and a harness-owned
`CallableToolRegistry`. It never performs name-based attribute lookup. This is important because
the retrieval and vintage packages also contain lower-level functions that do not implement the
typed execution boundary.

Before execution, the dispatcher:

1. rejects subclasses, raw mappings, non-string or unknown discriminators, and
   class/discriminator mismatches;
2. round-trips the call through its exact Pydantic model;
3. creates separate reference and adapter call copies;
4. validates the selected committed dependency's exact ID and current descriptor digest; and
5. independently runs the frozen reference adapter against the original call copy before passing
   only that dependency to the explicitly bound candidate adapter.

After execution, it revalidates that the same selected dependency object still has its committed
identity and digest. It then requires the exact result class, a lossless Pydantic round-trip, the
original call ID and tool name, and success facts consistent with the original call. Document
success also rechecks `top_k`, unique chunk IDs, deterministic ordering, language, and cutoff.
Data success rechecks every flat scope, period, cutoff, and normalization-rule field.

For all three tools, the complete candidate result must equal the independent frozen-reference
result. This closes fields that do not repeat every input and protects both success and
non-success outcomes. A candidate cannot substitute evidence by temporarily changing its private
call or selected registry and then restoring it. The dispatcher performs the same selected
dependency identity/digest check again after all candidate/reference result validation and
comparison, immediately before return. A changed private call, dependency, identity, result, or
success fact returns a sanitized typed error bound to the original call.

## Failure taxonomy

An unknown or invalid call has no valid `ToolResult` discriminator. These pre-execution conditions
therefore raise a sanitized `ToolDispatchError`:

- `unknown_tool`;
- `tool_call_type_mismatch`;
- `invalid_tool_call`; and
- `tool_registry_misconfigured`.

For a valid typed call, the dispatcher adds only:

- `tool_dispatch_failed` when an adapter raises unexpectedly; and
- `tool_result_invalid` when an adapter returns a wrong or inconsistent typed result.

Existing adapter success, abstention, and error results pass through only when the frozen reference
replay produces the exact same typed result. No exception text, path, raw row, registry inventory,
or future evidence is copied into a failure.

## Snapshot call-time hardening

Adversarial review before dispatcher integration reproduced two verify-then-mutate paths in the
older snapshot adapter:

- mutating the already-parsed manifest timestamps could make a post-cutoff capture appear eligible
  without changing the exact-byte descriptor hash; and
- a `bytes` subclass could preserve its hashed buffer while overriding `decode()` to substitute a
  selected observation.

The snapshot registry and reader now match the newer corpus/STES trust boundary. Every call
requires exact built-in `bytes`, rebuilds manifest and rights-catalog models from those bytes,
revalidates binding and immutable-container structure, executes against the fresh state, and
copies the original call ID and six flat arguments before downstream work. Descriptor calculation
uses the same fresh validation. Timestamp, catalog, binding, structure, byte-subclass, and call-ID
mutation regressions all fail closed.

## Validation evidence

Validated on Windows with Python 3.12.13:

- 127 focused snapshot tests pass with 100% snapshot registry/reader statement and branch coverage
  (437 statements, 162 branches);
- 69 focused dispatcher tests pass with 100% dispatcher statement and branch coverage
  (326 statements, 98 branches);
- all 976 repository tests pass with 100% SovereignLab statement and branch coverage
  (4,065 statements, 1,370 branches);
- the three real dispatch smokes reproduce the synthetic English document match, OECD CLI edition
  `202607` / value `102.66`, and ECOS GDP `2026Q1` raw value `596692.8`;
- independent contract and data-integrity reviews found no remaining reproducible P1 after
  call/digest/result mutation and restore cases were closed; and
- all 13 public schemas regenerate deterministically, and Ruff check/format passes across 63
  Python files.

No network, provider read, secret, live model call, GPU operation, or paid operation occurred.

## Next independent slice

Add only the planner protocol with scripted and immutable recorded/replay implementations next.
Keep packet assembly, route execution, committed end-to-end traces, and live model integration in
later reviewable slices.
