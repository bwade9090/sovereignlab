# SovereignLab application project description

- Status: application-ready wording for the current M2 midpoint
- Last updated: 2026-11-13 (shortened; engineering counts removed after ADR 0012)
- Disclosure level: verified implementation, compatibility, and deterministic offline replay
  results only; no provider/live, model-quality, or briefing-performance claim
- Before use, check the approved-record count against `docs/PROJECT_STATUS.md`

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
harvester for exact, rights-approved ECOS and KOSIS series. The first captures were committed on
2026-07-17, and the weekly GitHub Actions capture has committed since 2026-11-02, after a repair
that left a disclosed gap from 2026-07-20. Every committed snapshot is bound to a strict source
manifest, SHA-256 checksum, capture timestamp, source-specific redistribution decision, and
attribution rule. The archive includes real ECOS GDP and current-account captures, KOSIS national
CPI, and a 75,060-row OECD Korea composite-leading-indicator archive across 239 editions. A
fail-closed as-of resolver selects only editions whose availability at the requested cutoff can be
demonstrated; it abstains rather than inferring publication dates from monthly edition labels or
falling back to an unverified row. Exact Decimal-based unit conversion, Korean large-number
presentation, rounding, and grading tolerances are also frozen and tested.

The project passed its first milestone gate and is midway through the benchmark-and-baselines
milestone. Its evidence, benchmark, authoring-matrix, availability-ledger, rights, and execution
contracts are published as 13 JSON Schemas. The 40-question human-reviewed bilingual core is frozen
as an allocation, and 26 of 40 records — initially AI-authored, then approved under named human
review — are complete. They cover documentary questions over the Bank of Korea's May 2026 and
November 2025 Economic Outlooks and their independently dated official English translations; data
questions over the OECD Korea CLI revision archive and the 2026-07-17 ECOS GDP, ECOS
current-account, and KOSIS CPI snapshots; two combined document-plus-data pairs; and five
abstention pairs, each for a different reason to decline: no provably available edition, an
unapproved neighbouring OECD series, a false premise about revisions, a missing as-of date, and a
cutoff beyond the availability ledger's completeness frontier. The offline test suite reproduces
every approved gold answer by running the real tools against the committed evidence.

On the execution side, the project has shipped `typed function calling with committed traces`. A
typed contract fixes the bilingual request, a four-route plan, three flat-argument tool calls and
results, the evidence packet, and replay provenance. Bilingual document retrieval filters by
publication date before scoring, over a committed synthetic Korean/English corpus; the real Bank of
Korea report bodies are manifest-bound but not committed as searchable text. Five machine-readable
traces cover all four routes, all three tools, Korean and English, explicit and implicit cutoffs,
complete execution, planned abstention, and a tool abstention that stops later calls and exposes no
partial evidence. These are deterministic offline replays rather than provider or live outputs, so
they do not establish briefing quality or model performance. A pinned Ministral 3 3B QLoRA
compatibility run also completed one optimizer step on a disposable RunPod A40/CUDA 13 instance,
verifying NF4 loading, language-model-only LoRA boundaries, finite gradients, a changed adapter
tensor, and adapter-only output. This is deliberately reported as a training-path compatibility
result, not as evidence of improved model quality.

Later M2 work authors the remaining core records and a separately reported set of 200–300
deterministic revision probes, and runs the four-variant baseline suite comparing closed-book
generation, temporal RAG, RAG plus deterministic tools, and a QLoRA-tuned evidence router.
Temporal-leakage rate — whether a system uses information that did not exist at the question's
`as_of` date — is the headline metric; all performance claims will be derived only from committed
evaluation artifacts.

## Brief version

**SovereignLab — K-VINTAGE on KOR-RTD (Creator, Open Source, In Progress)**

Building an evaluation-first Korean macroeconomic research stack that reconstructs what official
statistics said at a historical `as_of` date. I implemented KOR-RTD's append-only ECOS/KOSIS
harvester, OECD revision archive, strict provenance and source-rights contracts, fail-closed vintage
resolver, and exact number-normalization rules; a typed execution-and-trace contract within the
project's 13 public JSON Schemas; cutoff-filtered bilingual document retrieval over a committed
synthetic corpus; and three deterministic evidence tools with an offline executor. Five offline
replays provide `typed function calling with committed traces`, covering all routes and tools,
Korean and English, explicit and implicit cutoffs, complete execution, and planned and tool
abstention without partial evidence. The frozen 40-record bilingual K-VINTAGE core has 26 records
reviewed and approved, spanning documentary, data, combined, and abstention questions, each
reproduced by the offline tests through the real tools. I also verified the pinned Ministral 3 3B
NF4/QLoRA training path on a disposable A40/CUDA 13 GPU without claiming model-quality gains. Later
work covers the remaining core, separately reported deterministic revision probes, and the
four-variant baseline suite, with temporal leakage as the headline metric.

## Usage guardrails

- Keep "In Progress" while the M2 benchmark and baseline work remains incomplete; deterministic
  offline replay does not imply benchmark completion.
- Describe the A40 result as QLoRA *compatibility*, not fine-tuning or model improvement.
- Do not cite core-benchmark progress beyond the approved 26/40 records, and always report the
  human-reviewed core separately from the machine-generated probes.
- Do not add leakage rates, quality improvements, or cost/latency figures until committed
  evaluation artifacts reproduce them.
- Disclose that the committed searchable retrieval corpus is synthetic-only whenever retrieval is
  described; the real report bodies are manifest-bound and not committed as searchable text.
- Describe the shipped minimal path only as `typed function calling with committed traces`. The
  bounded tool loop remains deferred to v1.1 (ADR 0008), and the committed replay artifacts do not
  support provider/live, model-quality, or briefing-performance claims.
- If a novelty claim is needed, qualify it as "to our knowledge, for official statistics" and cite
  the prior art listed in the charter and future datasheet.
