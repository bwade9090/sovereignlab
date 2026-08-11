# SovereignLab application project description

- Status: application-ready wording for the current M2 midpoint
- Last updated: 2026-08-11
- Disclosure level: verified implementation, compatibility, and deterministic offline replay
  results only; no provider/live, model-quality, or briefing-performance claim

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
resolver and GitHub Actions harvester are operational; and 1,129 tests pass with 100% statement
and branch coverage (4,679 statements, 1,568 branches) across 71 formatted Python files. The
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

On the execution side, the project has shipped `typed function calling with committed traces`.
A strict typed execution-and-trace contract freezes the bilingual request, four-route plan, exactly
three flat-argument tool calls and results, evidence packets, and digest-linked replay provenance.
Five machine-readable traces generated through the actual private executor, `ScriptedPlanner`, and
committed callable and artifact registries, synthetic retrieval corpus, and historical data cover
all four routes, all three tools, Korean and English, explicit and implicit cutoffs, complete
execution, planned abstention, and terminal tool abstention. Terminal results stop further calls,
and abstention exposes no partial evidence. The source package is unchanged; its 32-entry execution
descriptor retains digest
`08f45dab6a36a49cb7d0b588a69236942cd61534540bd4de0772010402dada64`, and the public surface remains
13 deterministic JSON Schemas. These are deterministic offline replays rather than provider or
live outputs, so they do not establish briefing quality or model performance. A
pinned Ministral 3 3B QLoRA compatibility run also completed one optimizer step on a disposable
RunPod A40/CUDA 13 instance, verifying NF4 loading,
language-model-only LoRA boundaries, finite gradients, a changed adapter tensor, and adapter-only
output. This is deliberately reported as a training-path compatibility result, not as evidence of
improved model quality.

The exact next implementation slice drafts only the Korean/English `kv-core-data-02` pair using the
existing approved `ecos-200y108-snapshot-20260717`; named human approval remains separate, so the
approved count stays 6/40. Later M2 work authors the remaining core records plus a separately
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
offline executor. Five real-digest offline replays now provide `typed function calling with
committed traces`, covering all routes and tools, Korean and English, explicit and implicit cutoffs,
complete execution, and terminal planned/tool abstention without partial evidence. The repository
passes 1,129 tests with 100% statement and branch coverage (4,679 statements, 1,568 branches). The
frozen
40-record bilingual K-VINTAGE core has its first 6 records reviewed and approved, including a
Korean/English documentary pair over the Bank of Korea's May 2026 Economic Outlook and its later
official English translation. I also verified the pinned Ministral 3 3B NF4/QLoRA training path on
  a disposable A40/CUDA 13 GPU without claiming model-quality gains. Next: draft only the
  Korean/English `kv-core-data-02` pair from the existing approved ECOS GDP snapshot, without
  changing the 6/40 approval count; later work covers the remaining core, separately reported
  deterministic revision probes, and the four-variant baseline suite, with temporal leakage as the
  headline metric.

## Usage guardrails

- Keep “In Progress” while the M2 benchmark and baseline work remains incomplete; deterministic
  offline replay does not imply benchmark completion.
- Describe the A40 result as QLoRA *compatibility*, not fine-tuning or model improvement.
- Do not cite core-benchmark progress beyond the approved 6/40 records, and always report the
  human-reviewed core separately from the machine-generated probes.
- Do not add leakage rates, quality improvements, or cost/latency figures until committed
  evaluation artifacts reproduce them.
- Disclose that the committed searchable retrieval corpus is synthetic-only whenever retrieval is
  described; the real report bodies are manifest-bound and not committed as searchable text.
- Describe the shipped minimal path only as `typed function calling with committed traces`. The
  bounded tool loop remains deferred to v1.1 (ADR 0008), and the committed replay artifacts do not
  support provider/live, model-quality, or briefing-performance claims.
- If a novelty claim is needed, qualify it as “to our knowledge, for official statistics” and cite
  the prior art listed in the charter and future datasheet.
