# SovereignLab application project description

- Status: application-ready wording for the current M2 midpoint
- Last updated: 2026-08-27
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
resolver and GitHub Actions harvester are operational; and 1,165 tests pass with 100% statement
and branch coverage (4,679 statements, 1,568 branches) across 77 formatted Python files. The
40-question human-reviewed bilingual core is frozen as an allocation, and 18 of 40 records —
initially AI-authored, then approved under
named human review —
are complete: a Korean/English data pair resolving the OECD CLI vintage available on 2026-07-09, an
abstention pair for an earlier cutoff where no edition is provably available, and a documentary
pair grounded in the Bank of Korea's May 2026 Economic Outlook and its independently dated official
English translation, plus Korean/English data pairs over the 2026-07-17 ECOS GDP and
current-account snapshots, a Korean/English data pair over the 2026-07-17 KOSIS national CPI
snapshot, a Korean/English rights-based abstention pair for Korea's OECD normalised CLI, a
neighboring measure outside the sole owner-approved OECD raw-data scope, a Korean/English
false-premise abstention pair that rejects the premise that archived OECD edition counts prove
the Korean CPI was revised, and a Korean/English missing-as-of clarification abstention pair
that asks for Korea's OECD amplitude-adjusted CLI for May 2026 while omitting the as-of date
the vintage request depends on. Offline
bilingual temporal document retrieval is implemented over a committed
synthetic Korean/English corpus — the real Bank of Korea report bodies are manifest-bound but not
yet committed as searchable text — with publication-date filtering before scoring; regression
tests on that corpus prove documents published after a question's cutoff cannot change eligible
results or scores.

The `kv-core-data-02` pair was completed as two drafts on 2026-08-19 and approved without a
substantive change by Hyungbae Cho on 2026-08-20. It reads the 2026 Q1 seasonally adjusted real GDP
value of 596,692.8 billion won from the 2026-07-17 ECOS snapshot whose use in KOR-RTD is
owner-approved. The records now live in
`data/benchmark/core/core-batch-003.jsonl`; the frozen matrix, source bundle, rights decisions,
source package,
public schemas, and execution runtime are unchanged. At that approval checkpoint, the focused
benchmark suite passed 27 tests and the full baseline passed 1,135 tests across 72 formatted
Python files.

The `kv-core-data-03` pair was completed as two AI-authored drafts in feature commit `50c4d9c`
and approved without a substantive change by Hyungbae Cho on 2026-08-21. It reads the May 2026
seasonally adjusted current-account value of 38,121.1 million US dollars from the existing
2026-07-17 ECOS snapshot whose use in KOR-RTD is owner-approved. The records now live in
`data/benchmark/core/core-batch-004.jsonl`, with only the annotation status, reviewer fields, and
lifecycle tag changed; the frozen matrix, source bundle, rights decisions, 13 public schemas, five
committed traces, source package, and execution runtime are unchanged. That approval brought the
approved core to 10 of 40 records. At that approval checkpoint the focused benchmark suite passed
33 tests across four files and the full baseline passed 1,141 tests across 73 formatted Python
files.

The `kv-core-data-04` pair was completed as two AI-authored drafts in feature commit `5e0da06`
and approved without a substantive change by Hyungbae Cho on 2026-08-25. It reads the June 2026
national all-items consumer price index of 119.99 (2020=100) from the existing committed
2026-07-17 KOSIS snapshot whose use in KOR-RTD is owner-approved under ADR 0007. The records now
live in `data/benchmark/core/core-batch-005.jsonl`, with only the annotation status, reviewer
fields, and lifecycle tag changed; the frozen matrix, source bundle, rights decisions, 13 public
schemas, five committed traces, source package, and execution runtime are unchanged. That
approval brought the approved core to 12 of 40 records and completed the data route's four
authorable pairs (`kv-core-data-01` through `kv-core-data-04`); the fifth data pair
`kv-core-data-05` stays reserved on the deliberately unauthored test-split unit. At that approval
checkpoint the focused benchmark suite passed 39 tests across five files and the full baseline
passed 1,147 tests across 74 formatted Python files.

The `kv-core-abstain-02` pair was completed as two AI-authored drafts in feature commit `c20619d`
and approved without a substantive change by Hyungbae Cho on 2026-08-26. Both questions ask for
Korea's OECD normalised composite leading indicator value for May 2026 using only the vintage
available as of 2026-07-09 — a neighboring measure outside the sole owner-approved OECD raw-data
scope, Korea's monthly amplitude-adjusted CLI (`KOR.M.LI_AA.IX._T`, ADR 0007) — so the approved
gold behavior is abstention on the missing rights basis. The pair binds no document or data units
and carries no tool expectations and no reference answer, only a language-matched abstention
reason that names the approved scope, forbids substituting the approved series or exposing an
unapproved observation, and leaks no observation value. The cutoff is deliberately one where the
approved amplitude-adjusted scope does resolve (edition 202607, value 102.66), and a focused
contrast test proves the approved abstention is rights-driven, not availability-driven — this is
the second approved abstention pair after `kv-core-abstain-01` and the first approved pair whose
fail-closed basis is a rights boundary rather than the availability ledger. The records now live
in `data/benchmark/core/core-batch-006.jsonl`, with only the annotation status, reviewer fields,
and lifecycle tag changed; the frozen matrix, source bundle, rights decisions, 13 public schemas,
five committed traces, source package, and execution runtime are unchanged. That approval
brought the approved core to 14 of 40 records. At that approval checkpoint the focused
benchmark suite passed 45 tests across six files and the full baseline passed 1,153 tests
across 75 formatted Python files.

The `kv-core-abstain-03` pair was completed as two AI-authored drafts in feature commit `77d247d`
and approved without a substantive change by Hyungbae Cho on 2026-08-26. Both questions rest on
the false premise that the many archived OECD editions of Korea's consumer price index prove the
Korean CPI was revised just as many times, and ask for before-and-after November 2019 CPI values
using only the vintage available as of 2026-07-17 — so the approved gold behavior is to reject
the premise and abstain: archived edition counts measure archive coverage, not actual revisions,
and KOR-RTD holds no owner-approved raw-data decision for the OECD Korea CPI revision series —
raw OECD observations outside the sole approved Korea monthly amplitude-adjusted CLI scope
(`KOR.M.LI_AA.IX._T`) remain metadata-only — so no before-and-after CPI observation can be
served and the system must not fabricate revision values or expose an unapproved observation.
The pair binds no document or data units and carries no tool expectations and no reference
answer, only a language-matched abstention reason. Focused tests additionally prove that the
rights catalog's only OECD decision is the approved CLI scope, that the serialized records leak
no observation value and no snapshot identifier, and that the only approved CPI evidence in
KOR-RTD — the KOSIS latest-only snapshot — carries `vintage_semantics=latest_only`, so committed
evidence cannot serve any CPI revision by construction. This is the third approved abstention
pair after the availability-frontier `kv-core-abstain-01` and neighboring-scope
`kv-core-abstain-02` pairs, and the first approved false-premise rejection pair. The records now
live in `data/benchmark/core/core-batch-007.jsonl`, with only the annotation status, reviewer
fields, and lifecycle tag changed; the frozen matrix, source bundle, rights decisions, 13 public
schemas, five committed traces, source package, and execution runtime are unchanged. That
approval brought the approved core to 16 of 40 records. At that approval checkpoint the focused
benchmark suite passed 51 tests across seven files and the full baseline passed 1,159 tests
across 76 formatted Python files.

The `kv-core-abstain-04` pair was completed as two AI-authored drafts in feature commit `fd7640b`
and approved without a substantive change by Hyungbae Cho on 2026-08-27 — a dev-split abstention
pair, the second dev-split pair after `kv-core-data-04`. Both questions ask for Korea's OECD
amplitude-adjusted CLI value for May 2026 using the vintage available at the time, while
omitting the as-of date the vintage request depends on — so the approved gold behavior is to ask
for the missing as-of and abstain: a vintage answer depends on its as-of cutoff, and KOR-RTD's
fail-closed contract never executes without an explicit `effective_as_of` and never guesses or
defaults the cutoff, because an assumed cutoff can expose the wrong vintage and create temporal
leakage. The pair binds no document or data units and carries no tool expectations and no
reference answer, only a language-matched abstention reason. Focused tests additionally prove
that the questions contain no as-of phrase while both abstention reasons demand an explicit
`effective_as_of`, that the serialized records leak no observation value and no snapshot or
ledger identifier, and that the same request resolves once an explicit cutoff of 2026-07-09 is
supplied — edition 202607, value 102.66 from the owner-approved CLI scope — so the approved
abstention is missing-cutoff driven, not availability- or rights-driven. This is the fourth
approved abstention pair after the availability-frontier `kv-core-abstain-01`, neighboring-scope
`kv-core-abstain-02`, and false-premise `kv-core-abstain-03` pairs, and the first approved
missing-as-of clarification pair and first approved dev-split abstention pair. The records now
live in `data/benchmark/core/core-batch-008.jsonl`, with only the annotation status, reviewer
fields, and lifecycle tag changed; the frozen matrix, source bundle, rights decisions, 13 public
schemas, five committed traces, source package, and execution runtime are unchanged. The
approved core is now 18 of 40 records, no benchmark draft is pending, and the other 22 matrix
slots remain unauthored and unapproved. At this approval checkpoint the focused benchmark suite
passes 57 tests across eight files and the full baseline passes 1,165 tests across 77 formatted
Python files.

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

The exact next action, directed by the owner, is a bounded draft-only authoring slice for the
frozen `kv-core-abstain-05` pair — the test-split abstention pair whose question asks for
Korea's OECD amplitude-adjusted CLI for May 2026 as of August 15, 2026, a cutoff later than the
committed edition-availability ledger's completeness frontier (`complete_through`, the
2026-07-17 capture instant); the gold behavior is abstention with
`cutoff_beyond_complete_through`, because past the frontier the ledger cannot certify which
editions had become available. The pair binds no source units and is fully offline; it is the
last matrix slot authorable without a new capture or an owner decision. The new drafts must stay
`annotation.status=draft` pending a separate named human review. Later M2 work authors the
remaining core records plus a separately reported set of 200–300 deterministic revision probes
and runs the four-variant baseline suite comparing
closed-book generation, temporal RAG, RAG plus deterministic tools, and a QLoRA-tuned evidence
router. Temporal-leakage rate—whether a system uses information that did not exist at the
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
passes 1,165 tests with 100% statement and branch coverage (4,679 statements, 1,568 branches)
across 77 formatted Python files. The frozen 40-record bilingual K-VINTAGE core has its first 18
records reviewed and approved, including a
Korean/English documentary pair over the Bank of Korea's May 2026 Economic Outlook and its later
official English translation. A further Korean/English `kv-core-data-02` pair over the 2026-07-17
ECOS GDP snapshot was approved by Hyungbae Cho on 2026-08-20, with the focused benchmark suite at
27 passing tests at that checkpoint. The `kv-core-data-03` current-account pair, drafted over the
existing ECOS snapshot whose use in KOR-RTD is owner-approved, was approved by Hyungbae Cho on
2026-08-21, with the focused benchmark suite at 33 passing tests at that checkpoint, bringing the
approved count to 10/40. The `kv-core-data-04` KOSIS CPI pair, drafted in feature commit
`5e0da06` over the existing committed `kosis-cpi-snapshot-20260717` whose use in KOR-RTD is
owner-approved (ADR 0007), was approved by Hyungbae Cho on 2026-08-25, with the focused benchmark
suite at 39 passing tests at that checkpoint, bringing the approved count to 12/40. The
`kv-core-abstain-02` pair, drafted in feature commit `c20619d` as a train-split abstention pair
whose questions ask for Korea's OECD normalised CLI — a neighboring measure outside the sole
owner-approved raw-data scope (`KOR.M.LI_AA.IX._T`, ADR 0007), so the gold behavior is a
rights-based abstention that binds no source units and leaks no observation value — was approved
by Hyungbae Cho on 2026-08-26, with the focused benchmark suite at 45 passing tests at that
checkpoint, bringing the approved count to 14/40. The `kv-core-abstain-03` pair, drafted in
feature commit `77d247d` as a train-split abstention pair whose questions rest on the false
premise that the many archived OECD editions of Korea's consumer price index prove the Korean
CPI was revised just as many times — so the gold behavior is to reject that premise and abstain,
since edition counts measure archive coverage, not actual revisions, and no owner-approved
raw-data decision covers the OECD Korea CPI revision series, with the pair binding no source
units and its serialized records leaking no observation value and no snapshot identifier — was
approved by Hyungbae Cho on 2026-08-26, with the focused benchmark suite at 51 passing tests at
that checkpoint, bringing the approved count to 16/40. The `kv-core-abstain-04` pair, drafted
in feature commit `fd7640b` as a dev-split abstention pair whose questions ask for Korea's OECD
amplitude-adjusted CLI value for May 2026 using the vintage available at the time while
omitting the as-of date the vintage request depends on — so the gold behavior is to ask for the
missing as-of and abstain, since the fail-closed contract never executes without an explicit
`effective_as_of` and never guesses or defaults the cutoff, with the pair binding no source
units and its serialized records leaking no observation value and no snapshot or ledger
identifier — was approved by Hyungbae Cho on 2026-08-27, with the focused benchmark suite at 57
passing tests; the approved count is now 18/40, no benchmark draft is pending, and the other 22
slots remain unauthored and unapproved. I also
verified the pinned Ministral 3 3B NF4/QLoRA training path on a disposable A40/CUDA 13 GPU without
claiming model-quality gains. Next, under owner direction, is a bounded draft-only authoring
slice for the frozen `kv-core-abstain-05` test-split abstention pair, whose question asks for
Korea's OECD amplitude-adjusted CLI for May 2026 as of August 15, 2026 — a cutoff past the
committed availability ledger's `complete_through` frontier, the 2026-07-17 capture instant, so
the gold behavior is abstention with `cutoff_beyond_complete_through`, since past that frontier
the ledger cannot certify which editions had become available — with the pair binding no source
units, fully offline, the last matrix slot authorable without a new capture or an owner
decision, and its records held at draft status pending separate named human review; later work
covers the remaining core, separately reported deterministic revision probes, and the
four-variant baseline suite, with temporal leakage as the headline metric.

## Usage guardrails

- Keep “In Progress” while the M2 benchmark and baseline work remains incomplete; deterministic
  offline replay does not imply benchmark completion.
- Describe the A40 result as QLoRA *compatibility*, not fine-tuning or model improvement.
- Do not cite core-benchmark progress beyond the approved 18/40 records, and always report the
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
