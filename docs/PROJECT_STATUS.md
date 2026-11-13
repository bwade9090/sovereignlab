# SovereignLab project status

This page states the present and is edited in place. Git history is the log of how it got here.

## Current state

- **Milestone:** M2 — benchmark and baselines (charter v2.5 §7). The M1b week-1 gate passed on
  2026-07-18.
- **Approved core:** 26 of 40 records (13 of 20 Korean/English pairs). No draft is pending.
- **Next step:** not selected. The owner chooses the next pair or slice; nothing is drafted or
  approved before that.
- **Last structural change:** on 2026-11-13 the process, documents, code, and tests were reduced
  to fit the project's size (ADR 0012). Data, schemas, and benchmark records were not changed.

## Benchmark core

Each pair is one Korean and one English record. Approved records live in
`data/benchmark/core/`; the allocation is `data/benchmark/core-authoring-matrix-v1.json`, which
the owner approved on 2026-07-25.

| Pair | Route | Split | Status | Batch file | Approved |
| --- | --- | --- | --- | --- | --- |
| `kv-core-doc-01` | documents | train | approved | `core-batch-002.jsonl` | 2026-07-29; re-approved 2026-11-02 (ADR 0011) |
| `kv-core-doc-02` | documents | train | approved | `core-batch-011.jsonl` | 2026-11-02 |
| `kv-core-doc-03` | documents | train | unauthored | — | — |
| `kv-core-doc-04` | documents | dev | unauthored | — | — |
| `kv-core-doc-05` | documents | test | unauthored | — | — |
| `kv-core-data-01` | data | train | approved | `core-batch-001.jsonl` | 2026-07-25 |
| `kv-core-data-02` | data | train | approved | `core-batch-003.jsonl` | 2026-08-20 |
| `kv-core-data-03` | data | train | approved | `core-batch-004.jsonl` | 2026-08-21 |
| `kv-core-data-04` | data | dev | approved | `core-batch-005.jsonl` | 2026-08-25 |
| `kv-core-data-05` | data | test | reserved | — | — |
| `kv-core-both-01` | documents and data | train | approved | `core-batch-010.jsonl` | 2026-11-02 |
| `kv-core-both-02` | documents and data | train | approved | `core-batch-012.jsonl` | 2026-11-02 |
| `kv-core-both-03` | documents and data | train | unauthored | — | — |
| `kv-core-both-04` | documents and data | dev | unauthored | — | — |
| `kv-core-both-05` | documents and data | test | reserved | — | — |
| `kv-core-abstain-01` | abstain | train | approved | `core-batch-001.jsonl` | 2026-07-25 |
| `kv-core-abstain-02` | abstain | train | approved | `core-batch-006.jsonl` | 2026-08-26 |
| `kv-core-abstain-03` | abstain | train | approved | `core-batch-007.jsonl` | 2026-08-26 |
| `kv-core-abstain-04` | abstain | dev | approved | `core-batch-008.jsonl` | 2026-08-27 |
| `kv-core-abstain-05` | abstain | test | approved | `core-batch-009.jsonl` | 2026-08-27 |

What the remaining slots need before they can be authored:

- `kv-core-doc-03` and `kv-core-both-03` need the May 2025 Bank of Korea outlook;
  `kv-core-doc-04` and `kv-core-both-04` need the November 2024 outlook; `kv-core-doc-05` and
  `kv-core-both-05` need the May 2024 outlook. Each release first needs its official Korean and
  English manifests under ADR 0009, dated under ADR 0011, as its own reviewable unit.
- `kv-core-data-05` and `kv-core-both-05` also need the reserved future data release
  (`reserved-future-data-release-test-01`): an independently captured, owner-approved release
  with its manifest and availability evidence.

## What exists

- **Evidence contracts** — 13 JSON Schemas in `data/schemas/`, generated from
  `src/sovereignlab/schemas/`.
- **Rights catalogs** — `data/rights/` (2026-07-16 and 2026-07-17), with four `allowed` series:
  ECOS GDP, ECOS current account, KOSIS national CPI, and the OECD Korea amplitude-adjusted CLI.
- **Weekly harvester** — `sovereignlab.harvest.weekly`, run by GitHub Actions; append-only.
- **Availability ledger and fail-closed resolver** — `sovereignlab.vintage`, tool
  `resolve_stes_as_of`, over a 75,060-row OECD Korea CLI archive spanning 239 editions.
- **Snapshot reader** — `sovereignlab.snapshots`, tool `read_snapshot_as_of`, over the three
  2026-07-17 ECOS/KOSIS captures.
- **Temporal retrieval** — `sovereignlab.retrieval`, tool `retrieve_temporal_documents`, over a
  synthetic bilingual corpus. Real report text is not committed or searchable.
- **Document manifests** — the Bank of Korea May 2026 and November 2025 outlooks, Korean and
  English. The PDFs stay in the Git-ignored `data/raw/`.
- **Execution path** — `sovereignlab.execution`: typed function calling with five committed
  traces in `traces/replay/v1/`.
- **Number normalization** — `sovereignlab.normalization`, specified in
  `docs/project/06_number_normalization_spec.md`.
- **QLoRA compatibility spike** — `experiments/qlora/`: a one-step Ministral 3 3B run passed on
  2026-07-18. It shows the training path loads, updates, and saves an adapter; it is not a
  model-quality result, and it does not need to be repeated.

Not built: any provider or live-model integration, the four-variant baseline suite, the
machine-generated probes, and the bounded tool loop (deferred to v1.1 by ADR 0008).

## Weekly capture

- **Schedule:** `.github/workflows/weekly-harvest.yml`, Mondays 02:17 UTC, plus manual dispatch.
  GitHub often starts scheduled runs several hours late; manifests record the real capture time.
- **Gate:** a capture is committed when `tests/test_committed_data.py` and the harvester tests
  pass on the runner.
- **Captures so far:** `20261102t101403605391z` (commit `fe4f9a9`, an owner-authorized manual
  dispatch) and `20261109t094531475775z` (commit `807e713`, the first scheduled run to succeed).
- **Permanent gap:** none of the 16 scheduled runs from 2026-07-20 through 2026-11-02 committed a
  capture. Never backfill it, and disclose it wherever capture coverage is described.
- **Archive-only:** captures after the 2026-07-17 registries are not used by the tools or the
  benchmark until the owner admits them in a new registry version (ADR 0010).
- **If a scheduled run fails:** diagnose it before the following Monday. Do not dispatch manually
  without the owner's authorization.

## Blockers and environment notes

- **GPU:** no development machine has a training GPU. The RunPod A40/CUDA 13 path is verified and
  no Pod is active. Any new paid Pod or training run needs owner authorization and an estimate.
- **Machine-local, never in Git:** `.venv`, `.env`, the GitHub CLI login (Mac only), the RunPod
  CLI and its SSH key (Mac only), and the outlook PDFs under `data/raw/` (check their size and
  SHA-256 against the manifests before use).
- **Actions secrets:** `ECOS_API_KEY` and `KOSIS_API_KEY` are configured. Their plaintext cannot
  be read back, so a local `.env` needs its own keys.
- **Windows:** the user-level Python launcher has been unreliable; find a working Python 3.12 with
  `where.exe python` and never commit its path. A stale repository-root `.pytest_tmp` directory
  can keep an access-denying ACL that fails every pytest run with `WinError 5`; leave it alone and
  pass `--basetemp` pointing at a fresh OS temporary directory. `requirements.txt` pins `tzdata`
  for `win32` only, because a standard Windows Python has no IANA timezone database; keep it.
  Give large parametrized tests short explicit IDs, or Windows hits its environment-variable limit.
- **Vintage coverage:** OECD edition codes do not encode release dates. The 2026-07-17 ledger used
  by the tools resolves only edition `202607`; the 329 older editions are unresolved and abstain.
  The archive-only ledgers additionally resolve `202608`–`202610` with `available_by` 2026-10-08
  and `last_absent_at` at the 2026-07-17 capture, so if they are admitted, cutoffs between those
  two dates will still abstain for those editions. That is the lasting cost of the capture gap.

## Spend ledger

Approved ceiling: USD 100. Only paid operations are listed; all other work to date used free
public APIs or ran offline.

| Date | Operation | Cost |
| --- | --- | ---: |
| 2026-07-18 | RunPod A40/CUDA 13 Ministral 3 QLoRA compatibility run: 1,832,105 ms across five provisioning/success Pods, all deleted | $0.23584524099715054 |

**Cumulative external spend: $0.23584524099715054 of $100.00.**

## Verified facts

The 2026-07-15 verification record (request URLs, byte and edition counts, the EO114–EO119 claim
boundary, and the use-guide findings) is in
[`docs/discovery/03_week1_verification_log.md`](discovery/03_week1_verification_log.md). Two facts
that the log does not carry:

- `DF_MEI_ARCHIVE` uses `OECD:DSD_MEI_ARCHIVE(1.0)` with `isFinal=true`, and the STES dimension
  order is `REF_AREA.FREQ.MEASURE.UNIT_MEASURE.ACTIVITY.EDITION`.
- OECD content published before 2024-07-01 falls under the OECD Terms and Conditions rather than
  the later default CC BY 4.0. `DF_MEI_ARCHIVE` exposed no licence or rights field and stays
  metadata-only.

## Owner decisions closed

Approvals of individual benchmark pairs are in the table above. The other closed decisions:

- 2026-07-16 — ADR 0005 approved in full: the edition-availability ledger, the fail-closed
  resolver, and the Asia/Seoul end-of-day cutoff. ADR 0004's source-specific rights policy and the
  first two ECOS rulings were approved the same day.
- 2026-07-16 — OECD observations stay metadata-only pending dataset-specific and third-party
  rights confirmation. ADR 0007 later lifted this only for the exact CLI series
  `KOR.M.LI_AA.IX._T`.
- 2026-07-17 — the employer-risk review required by charter §7, recorded verbatim in ADR 0006.
- 2026-07-17 — KOSIS national CPI and the OECD Korea CLI approved as exact scopes (ADR 0007).
- 2026-07-28 — the typed function-calling execution contract (ADR 0008) and the Bank of Korea
  Economic Outlook public-data ruling (ADR 0009).
- 2026-11-02 — weekly captures are archive-only until admitted (ADR 0010), and document manifests
  are dated from their exact bytes (ADR 0011).
- 2026-11-13 — the engineering process, documents, code, and tests were reduced (ADR 0012).
