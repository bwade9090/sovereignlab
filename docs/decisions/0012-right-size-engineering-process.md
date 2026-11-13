# ADR 0012: right-size the engineering process, documents, code, and tests

- Status: accepted — requested by the owner on 2026-11-13. The owner asked for the reduction; the
  specific cuts listed below were chosen during implementation and remain open to owner revision.
- Date: 2026-11-13
- Related: ADR 0008; ADR 0010; `docs/architecture.md`; `AGENTS.md`
- Amends: ADR 0010 decisions 3, 4, and 6 (see "Decision", items 5 and 6). No rights, evidence,
  vintage, or evaluation rule changes, and no accepted ADR is superseded.

## Context

By 2026-11-13 the repository held about 11,000 lines of source, 21,000 lines of tests (1,199
tests, 100% statement and branch coverage as a gate), and 12,500 lines of Markdown, for a project
whose function is a weekly capture of five resources, three offline evidence tools, a one-shot
executor that writes five traces, and a 40-record benchmark of which 26 records were approved.
The owner judged the engineering excessive for that function and purpose. Three patterns produced
most of the weight:

1. **Defence against the program itself.** The registries, adapters, dispatcher, and executor
   re-validated every input on every call: exact-type checks against subclassing, strict JSON
   round trips of every model, re-hashing every archive, running each tool twice and comparing
   the results, and checks that module-level tables had not been mutated mid-call. None of this
   guards against a real threat to an offline, single-process, deterministic tool, and the schema
   models already reject an inconsistent trace or packet.
2. **Process that multiplied itself.** Every checkpoint appended its narrative, test counts, and
   digests to about sixteen documents (the status page alone reached 2,600 lines and the README's
   "current milestone" section 180). A rule that the source package must stay unchanged, so that
   trace digests would not move, forced even the harvester's connection retry out of `src/`
   (ADR 0010).
3. **Tests that pinned data instead of behaviour.** Each approved pair had its own test file
   restating the record's text and metadata, and completeness tripwires compared the files on
   disk with the frozen registries. Those tripwires made every scheduled capture fail validation
   from 2026-07-20 to 2026-11-02, and that gap can never be backfilled.

## Decision

1. **Keep every public data contract and every committed data artifact unchanged**: the 13 JSON
   Schemas and their models, benchmark records, the matrix, manifests, archives, ledgers, rights
   catalogs, the harvester, the fail-closed resolver, retrieval, and number normalization.
2. **Rewrite the registries, adapters, dispatcher, planner, assembler, and executor without
   runtime self-defence.** A registry is an explicit list of committed files; loading it verifies
   checksums, rights links, and series bindings once and compares one pinned digest. A tool runs
   once. The executor relies on the schema models to validate the trace. The three registry
   digests, the tool-registry digest, and the artifact-registry digest are unchanged, and the five
   committed traces regenerate byte-for-byte except for `executor_sha256`, which by definition
   follows the source tree.
3. **The recording registry is replaced by `RecordedPlanner`**, which takes the recorded response
   bytes directly. Charter §6's recorded/replayable model interface is preserved.
4. **Conditions that a correctly loaded registry cannot produce are no longer runtime outcomes.**
   - The snapshot reader drops `source_not_api`, `source_not_latest_only`,
     `unsupported_media_type`, `source_content_mismatch`, and `rights_validation_failed`: the
     registry rejects those manifests when it loads. It also drops `ambiguous_snapshot_frontier`:
     two captures of one series at the same instant are now rejected at load time instead.
   - The adapters' `*_misconfigured` and `*_failed` error codes, the dispatcher's
     `tool_result_invalid` and pre-execution rejection codes, every planner code except
     `plan_validation_failed`, and the packet-assembly codes are removed. An unexpected tool
     failure is reported as `tool_dispatch_failed`; an unexpected planner exception propagates.
     The `packet_assembly` phase remains in the public trace schema but the executor no longer
     produces it.
   - Loaders no longer reject duplicate JSON keys or non-finite JSON constants, enforce size and
     row bounds, or confine paths; the STES registry no longer re-derives each ledger from its
     constraint XML or re-validates ledger and catalog chains on every call. The pinned digest
     freezes the exact v1 bytes those checks were run against, and
     `tests/test_committed_data.py` checks every committed ledger against its constraint capture.
   - Every abstention that real evidence can produce is kept, as are the per-row scope and unit
     checks of the snapshot parser and the neighbouring-series check on the STES archive.
5. **Tests assert behaviour through public entry points.** One data-driven module reproduces every
   approved gold through the real tools and validates the whole core as one bundle; one module
   checks the integrity of all committed captures. The per-pair files, the completeness tripwires
   of ADR 0010 decision 3, and the tests of removed machinery are deleted. There is no coverage
   target. ADR 0010's separation of archival from admission stands: weekly captures remain
   archive-only until a new registry version admits them.
6. **The weekly workflow validates what it captured** (`tests/test_committed_data.py` and the
   harvester tests) instead of the whole suite, so an unrelated failure can no longer cost a
   capture. A separate `ci.yml` runs lint and the full suite on every push to `main` and every
   pull request. The source package may change; after a change the replay traces are regenerated
   with one command.
7. **Documents state the present, once.** `AGENTS.md` keeps the evidence, rights, claims, security,
   and owner-decision rules and drops the onboarding ritual, validation tiers, and checkpoint log.
   `docs/PROJECT_STATUS.md` is edited in place. `docs/architecture.md` replaces the cross-machine
   handoff and the contract documents 02, 03, 05, and 08–16. Git history is the log: the removed
   documents and tests remain readable at commit `807e713`.

## Alternatives considered

- **Trim documents and rules only.** Rejected: the owner named code and tests explicitly, and the
  process rules existed largely to protect the defensive code's digests.
- **Also simplify the schema validators and the rights model.** Rejected for now: they are the
  public contract and the fail-closed rights gate, and their tests are one rule each.
- **Delete the execution path until a live model integration exists.** Rejected: ADR 0008 makes it
  the reference implementation, and the five traces are a published artifact.
- **Keep the full suite as the weekly gate.** Rejected: capture loss is irreversible, and the gate
  should depend only on what the capture produced.

## Consequences

- At this decision the repository holds about 7,100 lines of source, 8,200 lines of tests (559
  tests, about five seconds), and 3,700 lines of Markdown. Such counts are not kept up to date in
  documents any more; a claim that needs one must be re-derived from the repository.
- `executor_sha256` in the five traces changed. Any earlier citation of the previous digest
  refers to commit `883815b`..`807e713`.
- A malformed or tampered registry input now fails loudly at load time instead of producing a
  typed abstention. Tools still abstain on every evidence condition described in
  `docs/architecture.md`.
- References inside older ADRs to `docs/project/10_*`, `12_*`, and similar files point at
  documents that now exist only in Git history.
- The application wording in `docs/application/` was shortened and no longer quotes test counts.

## Revisit triggers

- A provider or live-model integration lands and needs a recording store.
- A new registry version is prepared; cross-artifact checks may be worth a one-off script.
- A scheduled capture fails, or a defect is traced to a check this decision removed.
