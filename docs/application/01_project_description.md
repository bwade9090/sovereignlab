# SovereignLab application project description

- Status: application-ready wording for the current M2 entry point
- Last updated: 2026-07-18
- Disclosure level: verified implementation and compatibility results only; no model-quality claim

## Detailed version

**SovereignLab — K-VINTAGE on KOR-RTD**

*Creator | Independent Open-Source Project | In Progress*

SovereignLab is an evaluation-first data and AI project for answering a deceptively difficult
economic-research question: **what did the official data say at the time?** Korea's public ECOS and
KOSIS APIs expose current observations but do not provide a native point-in-time query path, making
it difficult to reproduce the information set available to an analyst, forecaster, or model on a
past date. SovereignLab addresses this with three connected artifacts: KOR-RTD, a
provenance-contracted real-time data layer; K-VINTAGE, a bilingual Korean/English evaluation
benchmark; and a reference briefing pipeline that combines temporal RAG with deterministic
statistical tools.

The implemented KOR-RTD foundation combines OECD revision histories with an append-only weekly
harvester for exact, rights-approved ECOS and KOSIS series. Every committed snapshot is bound to a
strict source manifest, SHA-256 checksum, capture timestamp, source-specific redistribution
decision, and attribution rule. The initial archive includes real ECOS GDP and current-account
captures, KOSIS national CPI, and a 75,060-row OECD Korea composite-leading-indicator archive across
239 editions. A fail-closed as-of resolver selects only editions whose availability at the requested
cutoff can be demonstrated; it abstains rather than inferring publication dates from monthly edition
labels or falling back to an unverified row. Exact Decimal-based unit conversion, Korean
large-number presentation, rounding, and grading tolerances are also frozen and tested.

The project has completed its first milestone gate. Its evidence, benchmark, availability-ledger,
and rights contracts are published as synchronized JSON Schemas; the offline resolver and GitHub
Actions harvester are operational; and 337 tests pass with 100% statement and branch coverage. A
pinned Ministral 3 3B QLoRA compatibility run also completed one optimizer step on a disposable
RunPod A40/CUDA 13 instance, verifying NF4 loading, language-model-only LoRA boundaries, finite
gradients, a changed adapter tensor, and adapter-only output. This is deliberately reported as a
training-path compatibility result, not as evidence of improved model quality.

The next phase will author a 40-question human-reviewed bilingual core benchmark and a separately
reported set of 200–300 deterministic revision probes, implement publication-date-filtered temporal
RAG, and connect retrieval to the vintage-resolving data tool. The resulting baseline suite will
compare closed-book generation, temporal RAG, RAG plus deterministic tools, and a QLoRA-tuned
evidence router. Temporal-leakage rate—whether a system uses information that did not exist at the
question's `as_of` date—is the headline metric, alongside routing accuracy, retrieval recall,
citation correctness, numerical provenance, abstention quality, latency, and cost. The final plan
includes a reproducible grader, model and data cards, a compact API/trace interface, and public
benchmark artifacts; all performance claims will be derived only from committed evaluation traces.

## Brief version

**SovereignLab — K-VINTAGE on KOR-RTD (Creator, Open Source, In Progress)**

Building an evaluation-first Korean macroeconomic research stack that reconstructs what official
statistics said at a historical `as_of` date. I implemented KOR-RTD's append-only ECOS/KOSIS
harvester, OECD revision archive, strict provenance and source-rights contracts, fail-closed vintage
resolver, and exact number-normalization rules; the repository currently passes 337 tests with 100%
statement and branch coverage. I also verified the pinned Ministral 3 3B NF4/QLoRA training path on
a disposable A40/CUDA 13 GPU without claiming model-quality gains. Next, I am building K-VINTAGE—a
bilingual human-reviewed core benchmark plus separate deterministic revision probes—and a
four-variant baseline suite spanning closed-book generation, temporal RAG, RAG with deterministic
vintage tools, and a QLoRA-tuned evidence router, with temporal leakage as the headline metric.

## Usage guardrails

- Keep “In Progress” until a public end-to-end vertical slice is reproducible.
- Describe the A40 result as QLoRA *compatibility*, not fine-tuning or model improvement.
- Do not add benchmark counts, leakage rates, or quality improvements until committed evaluation
  artifacts reproduce them.
- If a novelty claim is needed, qualify it as “to our knowledge, for official statistics” and cite
  the prior art listed in the charter and future datasheet.
