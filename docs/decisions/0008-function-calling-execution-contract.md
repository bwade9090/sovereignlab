# ADR 0008: typed function-calling execution contract and deferred bounded tool loop

- Status: accepted
- Date: 2026-07-28
- Supplements: ADR 0003 decision 2 (the preserved four-route/four-variant technical spine) and
  ADR 0005 (fail-closed vintage contract). It reopens neither; no prior decision is superseded.
- Charter synchronization: v2.4 (substantive changes limited to §§3, 7, and the decision index
  in §12)

## Context

The owner asked whether the remaining plan can also build demonstrable agent-orchestration
experience (LLM tool/function calling and multi-step loops). The role-gap analysis scores
"Advanced RAG / agentic use cases / vector DB" at 1/5 and names "agentic tool use" in the central
diagnosis, so the question targets a documented gap, not checklist anxiety. A four-lens review
(governance, technical design, schedule, portfolio value) with two adversarial verification passes
was run against the repository on 2026-07-28. Verified findings:

1. Charter §9's non-goal excludes only "Autonomous multi-agent research over the open web", and
   the role-gap rule prohibits only un-ablated multi-agent choreography. A bounded single-agent
   loop over the project's own offline fail-closed tools is prohibited by neither — but charter
   §3 is the approved system contract (a typed four-route plan, executed deterministically), so
   any execution-mechanism change requires an ADR and a section-precise charter amendment.
2. The question's two halves have very different costs. Typed tool/function calling (the model
   emits the typed plan and typed tool invocations against schemas derived from the frozen
   pydantic contracts) is the natural implementation of the already-planned minimal
   question-to-evidence-packet path — near-zero added scope. A model-driven multi-step loop is
   new scope with almost nothing measurable in-window, as the arithmetic below shows.
3. Frozen-matrix arithmetic: only `kv-core-data-01` and `kv-core-both-01` (both `train`) exercise
   the vintage resolver. The dev/test `data` and `documents_and_data` slices consume latest-only
   ECOS/KOSIS snapshot units or the reserved test release. `BenchmarkRecord` 2.0.0 forbids
   `tool_expectations` on `abstain` records, so the loop's flagship behavior — probe the
   resolver, observe the structured fail-closed abstention, finalize — cannot carry gold
   per-step expectations under the frozen contract. A pre-registered "loop beats single-shot"
   hypothesis would be decided on roughly four records with the interesting slice at zero.
4. Trajectory-level temporal leakage is structurally zero over the existing tools: the fail-closed
   resolver and filter-before-scoring retriever cannot return post-cutoff evidence for their
   `as_of` argument by construction. The residual channel — a rewritten or bumped `as_of`
   argument — is already graded by the frozen "tool-selection and typed-argument exact match"
   metric. Per-step ledger auditing would mostly re-verify what the substrate mechanically
   guarantees.
5. The MVP tool surface is three tools, not two: six of the ten data-bearing matrix pairs consume
   latest-only ECOS/KOSIS snapshot units, and no deterministic snapshot-read tool exists yet in
   `src/sovereignlab/`. No router, no external model-call surface, and no record/replay harness
   exist either; charter §6's replayable-interface mandate is unbuilt future cost, not a credit.
6. The week-2 gate content (minimal end-to-end path, no known leakage) is still open at the
   calendar week-3 boundary with 36/40 core records unauthored. The charter's binding response to
   overrun is the pre-committed cut ladder — cutting, not adding scope.
7. Grading constraints that shape any implementation: `BenchmarkBundle` 2.0.0 restricts
   `ToolExpectation` sources to API/dataset kinds (document sources are rejected), so retrieval
   calls are graded through `DocumentEvidence`/citation metrics, never as tool expectations; and
   the approved gold convention is a flat composite call
   (`resolve_stes_as_of` with `normalization_rule_id` among its arguments) that does not match
   the resolver's internal signature, so the harness needs an adapter layer and must inject
   manifests, ledgers, and bytes itself.

## Decision

1. **The minimal question-to-evidence-packet path is implemented as a typed function-calling
   artifact.** The model emits the §3 typed route plan and typed tool invocations as native
   function calls validated against JSON schemas derived from the frozen pydantic contracts. The
   pipeline validates and executes them deterministically and records every call and result in a
   committed machine-readable trace. The single-shot §3 contract is unchanged: one typed plan,
   deterministic execution, no model-driven iteration in-window.
2. **The MVP tool surface is exactly three deterministic offline tools:** (a) temporal document
   retrieval; (b) the fail-closed as-of resolver, exposed behind the frozen flat gold-argument
   convention through an adapter; (c) a new deterministic latest-only snapshot-read tool for the
   approved ECOS/KOSIS snapshot units. Tools never accept model-chosen file paths, manifests,
   ledgers, or bytes; the harness injects committed artifacts. The frozen flat gold-argument
   convention is the `ToolExpectation` shape committed in
   `data/benchmark/core/core-batch-001.jsonl`: a single flat `resolve_stes_as_of` call whose
   arguments are the five SDMX dimensions (`ref_area`, `freq`, `measure`, `unit_measure`,
   `activity`) plus `period`, `as_of`, and `normalization_rule_id`. The snapshot-read tool's gold
   argument convention must be frozen the same way before the matrix records that depend on it
   are authored.
3. **External model calls are wrapped behind the charter §6 recorded/replayable interface.** All
   tests run offline with scripted or recorded planners; live model calls are paid operations
   under the existing smoke-test and spend-ledger rules.
4. **The bounded multi-step tool loop is deferred to post-window v1.1** as an execution-mode
   ablation (single-shot plan vs bounded loop, same tools, same frozen records, hard step budget)
   — deferred because the frozen matrix gives it no measurable dev/test slice, its flagship
   abstention-recovery behavior is inexpressible as gold expectations under contract 2.0.0, and
   adding scope at a missed-gate boundary inverts the owner-approved cut-ladder rule. The v1.1
   design must resolve, in order: conditional-argument `documents_and_data` records (a new owner
   matrix decision), a trajectory-grading convention, and a recorded verification spike for the
   pinned checkpoint's native tool-call template (or adoption of the existing
   compact-JSON-in-content convention instead — the fixture format in
   `experiments/qlora/fixtures/compatibility.jsonl`).
5. **The LoRA target remains the single-shot router/tool planner** under the frozen promotion
   rule. No trajectory training data is authored in-window.
6. **The evaluation contract is unchanged.** `BenchmarkRecord`/`BenchmarkBundle` stay 2.0.0; no
   trajectory metric is added to charter §5; the four-variant baseline suite is unchanged.
7. **Claim discipline:** in-window artifacts are described as "typed function calling with
   committed traces" only, and only after the minimal path ships. The words "agent", "agentic",
   "multi-step", "orchestration", and "autonomous" are reserved for the evaluated v1.1 loop.

## Alternatives considered

- **In-window bounded loop under a ~6 h timebox, reported as an ablation.** Rejected: the honest
  pre-declared expectation is a null result on ~4 records (interesting slice N=0), the schedule
  already stands at a missed-gate boundary where the binding rule is cutting, and effort
  estimates across four independent lenses spanned 4–18 h — the floor is not robust.
- **Silently implementing the loop as an "implementation detail" of the join unit.** Rejected:
  charter §3 is the scope authority and the project's protocol requires consequential technical
  choices to be recorded; AGENTS.md also forbids expanding agents before the milestone gate.
- **Doing nothing (hardcoded dispatch of the router's plan).** Rejected: it fails to close the
  typed function-calling half of the documented gap at equal implementation cost, and would
  likely be rewritten for v1.1 anyway.

## Approval record

Hyungbae Cho reviewed the four-lens findings, the adversarial verification results, and the
matrix/schema arithmetic in the active session on 2026-07-28 and approved: all recommendations
accepted (option A — typed function-calling implementation now, bounded loop deferred to v1.1),
and all contract/document amendments required by this decision. The owner also directed that this
round close with the plan adjustment only; implementation starts in a new session onboarding
through `AGENTS.md`.

## Consequences

- The tools-bearing baseline variants (`rag_tools`, `lora_router`) expose the full three-tool
  MVP surface of decision 2. Charter §5's variant-3 shorthand ("retrieval plus the deterministic
  vintage-resolving as-of tool") names the flagship tool; it does not restrict the surface, and
  §5 itself is deliberately untouched by v2.4.
- The join work unit's true size includes the project's first external model-call surface, the
  record/replay harness, the snapshot-read tool, and the resolver adapter — it is larger than
  "gluing three existing components" under any mechanism, and its hour budget must reflect that.
- The typed traces committed by the minimal path double as the substrate for v1.1 trajectory
  work and the week-4 trace UI, so nothing built in-window is thrown away by the deferral.
- The wording banks gain a guard rule (docs/application/00_cv_bullets.md) mirroring decision 7.
- The M2 continuation order is unchanged: work unit A (BOK May-2026 outlook manifests) first,
  the `kv-core-doc-01` draft pair second, the join unit third under this contract.

## Revisit triggers

- The four-week window closes and v1.1 planning begins.
- The owner reopens the core matrix to add conditional-argument `documents_and_data` records.
- A recorded verification spike settles the pinned checkpoint's native tool-call template
  support, or the project adopts the compact-JSON-in-content convention for tool emission.
- Any proposal to grade retrieval calls as tool expectations or to add trajectory metrics —
  either requires a superseding schema/contract decision, not a silent change.
