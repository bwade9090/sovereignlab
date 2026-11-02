# ADR 0010: keep weekly captures archive-only until a trusted registry admits them

- Status: accepted — owner-approved repair on 2026-11-02
- Date: 2026-11-02
- Related: ADR 0005; ADR 0008; `docs/project/10_snapshot_reader_contract.md`;
  `docs/project/12_stes_adapter_contract.md`; `.github/workflows/weekly-harvest.yml`
- Amends: only the explicit-location completeness rule in contracts 10 and 12; no accepted ADR is
  superseded

## Context

The weekly harvester shipped on 2026-07-17. Its workflow captures the OECD STES constraints and
the approved ECOS/KOSIS scopes, runs the full offline suite, and commits `data/archive`,
`data/availability`, and `data/manifests` only when that suite passes. On 2026-07-29 and
2026-07-30 the trusted latest-only snapshot registry and the historical STES registry added
explicit-location completeness tests. They required every approved latest-only manifest, and every
OECD STES manifest, archive, and ledger, on disk to equal the frozen v1 registries' explicit
locations exactly.

Each design worked as written, and together they made a successful scheduled run impossible: a
fresh capture is, by construction, absent from the frozen v1 registries, so validation failed and
the commit step never ran. GitHub Actions records 16 scheduled runs from 2026-07-20 through
2026-11-02, none successful and no capture commit:

- 10 runs (2026-08-10 and every week from 2026-08-31 through 2026-11-02) failed only those two
  completeness tests; the latest runs reported `2 failed, 1176 passed`. The 2026-11-02 capture
  itself succeeded, and its artifacts were discarded with the runner.
- 3 runs (2026-08-17, 2026-08-24, and 2026-09-07) hit `httpcore.ConnectTimeout` while connecting
  to KOSIS twice and ECOS once, with a 60-second client timeout and no retry.
- 3 runs (2026-07-20, 2026-07-27, and 2026-08-03) have expired logs under GitHub's 90-day
  retention. The capture step failed in the first two and validation failed in the third.

No commit landed after 2026-08-27, so GitHub disabled the public repository's scheduled workflow
after 60 days without repository activity (`disabled_inactivity`, notified 2026-11-02).

The append-only rules forbid backfilling the missed weeks. The ECOS/KOSIS latest-only states
between 2026-07-17 and the next successful capture cannot be recovered. The next availability
ledger records any newly observed OECD edition with `last_absent_at` at the 2026-07-17 capture, so
cutoffs inside that interval stay unresolved for those editions and resolve by fail-closed
abstention rather than a guessed date.

The executor descriptor binds every `.py` file under `src/sovereignlab`, and the five committed
replay traces pin its digest. Editing any source module, including the harvester, would therefore
invalidate the committed public traces.

## Decision

1. Separate archival from admission. The weekly harvester keeps appending checksummed manifests,
   archives, and availability ledgers to `data/`. A trusted registry reads only the inputs it
   enumerates, and a capture reaches execution only through a superseding registry version with a
   new ID and descriptor, as contracts 10 and 12 already require.
2. Each frozen registry's admission frontier is the newest `retrieved_at` among the manifests it
   admits: 2026-07-17T11:52:43.896254Z for snapshot registry v1 and
   2026-07-17T11:53:02.688498Z for STES registry v1.
3. Completeness keeps its tripwire inside the frontier. Every approved latest-only manifest, and
   every STES manifest, archive, and ledger, captured at or before the relevant frontier must be
   registered, and every committed rights catalog must be registered. After the frontier only
   harvester output is archive-only: approved ECOS/KOSIS latest-only captures for the snapshot
   registry; for the STES registry, `oecd-stes-constraint` captures, their `{source_id}.xml`
   archives, and the ledgers whose capture token matches a later availability capture. Any other
   unregistered input still fails, including a backdated capture, a later STES data archive, an
   orphan archive, or a new rights catalog.
4. The trusted registries and their descriptors, the source package and executor digest, the 13
   public schemas, the five replay traces, the frozen matrix, and every benchmark record stay
   unchanged.
5. Make the operational repairs outside `src/`:
   - `scripts/harvest_weekly.py` retries connection establishment twice through
     `httpx.HTTPTransport(retries=2)`, which never resends a request a provider already received;
   - the workflow pins `ubuntu-24.04`, sets a 30-minute job timeout, and moves to the Node 24
     majors `actions/checkout@v5` and `actions/setup-python@v6`.
6. Re-enable the workflow and confirm one manually dispatched run commits a capture through the
   unchanged validation step before relying on the schedule.

## Alternatives considered

- **Re-enable the workflow unchanged:** rejected because every capture fails validation.
- **Deselect the completeness tests only inside the workflow:** rejected because the first capture
  commit would then break the local full baseline on every machine.
- **Generate a new registry version for each capture:** rejected because admission changes
  descriptors and benchmark replay inputs and therefore needs an owner decision, not a cron job.
- **Push captures to a side branch or pull request for weekly human admission:** rejected because
  it restores a weekly manual gate and leaves the default branch inactive.
- **Retry inside `sovereignlab.harvest.weekly._fetch`:** rejected because any source-package edit
  changes the executor digest pinned by the committed traces.
- **Backfill the missed weeks:** prohibited by the append-only capture rules.

## Consequences

- Weekly captures again accumulate as public, timestamped archive evidence, and their commits
  should keep the scheduled workflow active.
- The v1 registries, approved benchmark records, replay traces, and executor digest are unchanged.
  `kv-core-abstain-05` keeps its `cutoff_beyond_complete_through` gold against the active
  2026-07-17 ledger.
- The gap from 2026-07-20 to the first successful capture is permanent and must be disclosed
  wherever capture coverage is described.
- Admitting any later capture remains a separate, owner-reviewed registry-version decision.

## Revisit triggers

- A superseding registry version admits a later capture; its frontier then moves with it.
- The harvester adds a source family, archive format, or capture role.
- A scheduled run fails again, or GitHub changes its inactivity rule.
