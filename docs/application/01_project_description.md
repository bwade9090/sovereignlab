# SovereignLab application project description

- Status: application-ready wording for the current M2 midpoint
- Last updated: 2026-08-11
- Disclosure level: verified implementation and compatibility results only; no model-quality or
  end-to-end execution claim

## Detailed version

**SovereignLab — K-VINTAGE on KOR-RTD**

*Creator | Independent Open-Source Project | In Progress*

SovereignLab is an evaluation-first data and AI project for answering a deceptively difficult
economic-research question: **what did the official data say at the time?** Korea's public ECOS and
KOSIS APIs expose current observations but do not provide a native point-in-time query path, making
it difficult to reproduce the information set available to an analyst, forecaster, or model on a
past date. SovereignLab is building three connected artifacts to address this: KOR-RTD, a
provenance-contracted real-time data layer; K-VINTAGE, a bilingual Korean/English evaluation
benchmark; and a reference briefing pipeline that will combine temporal RAG with deterministic
statistical tools.

The implemented KOR-RTD foundation combines OECD revision histories with an append-only weekly
harvester for exact, rights-approved ECOS and KOSIS series (first captures committed 2026-07-17;
the weekly GitHub Actions schedule is active). Every committed snapshot is bound to a
strict source manifest, SHA-256 checksum, capture timestamp, source-specific redistribution
decision, and attribution rule. The initial archive includes real ECOS GDP and current-account
captures, KOSIS national CPI, and a 75,060-row OECD Korea composite-leading-indicator archive across
239 editions. A fail-closed as-of resolver selects only editions whose availability at the requested
cutoff can be demonstrated; it abstains rather than inferring publication dates from monthly edition
labels or falling back to an unverified row. Exact Decimal-based unit conversion, Korean
large-number presentation, rounding, and grading tolerances are also frozen and tested.

The project passed its first milestone gate and is midway through the benchmark-and-baselines
milestone. Its evidence, benchmark, core-authoring-matrix, availability-ledger, rights, and
execution contracts are published as 13 synchronized deterministic JSON Schemas; the offline
  resolver and GitHub Actions harvester are operational; and 1,115 tests pass with 100% statement
  and branch coverage (4,679 statements, 1,568 branches) across 69 formatted Python files. The
40-question human-reviewed bilingual
core is frozen as an allocation, and 6 of 40 records — initially AI-authored, then approved under
named human review —
are complete: a Korean/English data pair resolving the OECD CLI vintage available on 2026-07-09, an
abstention pair for an earlier cutoff where no edition is provably available, and a documentary
pair grounded in the Bank of Korea's May 2026 Economic Outlook and its independently dated official
English translation. Offline bilingual temporal document retrieval is implemented over a committed
synthetic Korean/English corpus — the real Bank of Korea report bodies are manifest-bound but not
yet committed as searchable text — with publication-date filtering before scoring; regression
tests on that corpus prove documents published after a question's cutoff cannot change eligible
results or scores.

On the execution side, a strict typed execution-and-trace contract freezes the bilingual request,
the four-route plan, exactly three flat-argument tool calls and results, evidence packets, and
digest-linked replay provenance. All three deterministic evidence tools are implemented behind
trusted, digest-linked registries — cutoff-filtered temporal document retrieval over the frozen
synthetic bilingual corpus, the fail-closed as-of vintage resolver over the approved OECD CLI
revision archive, and latest-only snapshot reads over the owner-approved ECOS/KOSIS captures —
and an explicit dispatcher independently replays and revalidates every call before returning a
result. The offline one-shot planner boundary is implemented with scripted and immutable
recorded/replay modes, exact candidate-byte verification, digest-linked provenance, and request
cutoff/question/language binding before dispatch. An internal deterministic evidence-packet
  assembler now preserves ordered typed payloads, exact planned/tool abstention reasons, repeated
  cross-call evidence, and no-partial-evidence behavior without adding a public schema or wrapper.
  A private offline executor now plans exactly once, dispatches validated calls in order, stops at
  the first terminal result, and binds the real registry, corpus, planner, and canonical source-tree
  provenance into the existing trace model. Committed end-to-end replay traces remain in the
  current work unit, so no end-to-end execution result is claimed yet. A
pinned Ministral 3 3B QLoRA compatibility run also completed one optimizer step on a disposable
RunPod A40/CUDA 13 instance, verifying NF4 loading,
language-model-only LoRA boundaries, finite gradients, a changed adapter tensor, and adapter-only
output. This is deliberately reported as a training-path compatibility result, not as evidence of
improved model quality.

The exact next implementation slice adds only committed machine-readable end-to-end replay traces
over the completed offline executor and real digest-linked registries. Later M2 work authors the
remaining 34 core records plus a separately
reported set of 200–300 deterministic revision probes and runs the four-variant baseline suite
comparing closed-book generation, temporal RAG, RAG plus deterministic tools, and a QLoRA-tuned
evidence router. Temporal-leakage rate—whether a system uses information that did not exist at the
question's `as_of` date—is the headline metric; all performance claims will be derived only from
committed evaluation artifacts.

## Brief version

**SovereignLab — K-VINTAGE on KOR-RTD (Creator, Open Source, In Progress)**

Building an evaluation-first Korean macroeconomic research stack that reconstructs what official
statistics said at a historical `as_of` date. I implemented KOR-RTD's append-only ECOS/KOSIS
harvester, OECD revision archive, strict provenance and source-rights contracts, fail-closed vintage
resolver, and exact number-normalization rules, then froze a typed execution-and-trace contract —
completing the project's 13 public JSON Schemas — and implemented cutoff-filtered bilingual
temporal document retrieval over a committed synthetic corpus, all three deterministic evidence
tools behind a replay-checked dispatcher, an offline scripted/immutable recorded-replay planner
  boundary, an internal deterministic evidence-packet assembler, and a private provenance-bound
  offline executor. The repository passes 1,115 tests with 100% statement and branch coverage
  (4,679 statements, 1,568 branches). The frozen
40-record bilingual K-VINTAGE core has its first 6 records reviewed and approved, including a
Korean/English documentary pair over the Bank of Korea's May 2026 Economic Outlook and its later
official English translation. I also verified the pinned Ministral 3 3B NF4/QLoRA training path on
  a disposable A40/CUDA 13 GPU without claiming model-quality gains. Next: committed machine-readable
  end-to-end replay traces, then the remaining core,
separately reported deterministic revision probes, and the four-variant baseline suite, with
temporal leakage as the headline metric.

## Usage guardrails

- Keep “In Progress” until a public end-to-end vertical slice is reproducible.
- Describe the A40 result as QLoRA *compatibility*, not fine-tuning or model improvement.
- Do not cite core-benchmark progress beyond the approved 6/40 records, and always report the
  human-reviewed core separately from the machine-generated probes.
- Do not add leakage rates, quality improvements, or cost/latency figures until committed
  evaluation artifacts reproduce them.
- Disclose that the committed searchable retrieval corpus is synthetic-only whenever retrieval is
  described; the real report bodies are manifest-bound and not committed as searchable text.
- Do not use “agent”, “agentic”, “multi-step”, “orchestration”, or “autonomous” wording; the
  bounded tool loop is deferred to v1.1 (ADR 0008). Do not claim the minimal typed
  function-calling path has shipped until committed end-to-end replay traces exist.
- If a novelty claim is needed, qualify it as “to our knowledge, for official statistics” and cite
  the prior art listed in the charter and future datasheet.
