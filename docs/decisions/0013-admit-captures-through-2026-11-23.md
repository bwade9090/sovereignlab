# ADR 0013: admit captures through 2026-11-23 as evidence version 2

- Status: accepted — owner-approved on 2026-11-24
- Date: 2026-11-24
- Related: ADR 0005; ADR 0007; ADR 0010; ADR 0012; `docs/architecture.md`
- Amends: nothing. This is the separate admission decision that ADR 0010 requires; ADR 0007
  decision 6 is applied, not changed.

## Context

The evidence the tools could see was frozen at the 2026-07-17 captures (ADR 0010). Weekly
captures resumed on 2026-11-02 and have committed every Monday since, but they stayed
archive-only. Two things made admission worth deciding:

- The 2026-11-16 capture observed OECD edition `202611` for the first time. It was absent from
  the 2026-11-09 capture (09:45:31 UTC) and the content constraint dates it at
  2026-11-10T12:57:37Z, so its availability is bracketed to about one day. This is the "next
  observed OECD edition rollover" that charter §7 names as the primary live event. Its 48-hour
  cited-note target passed unnoticed.
- The tools answered OECD vintage questions only for cutoffs from 2026-07-08 through 2026-07-16,
  all from one edition, so no revision could be shown through ledger-proven availability.

The weekly harvester captures OECD availability metadata, not CLI observations. The values of
editions after `202607` therefore needed a fresh capture of the consolidated archive.

## Decision

1. **Capture the consolidated Korea CLI archive a second time, by hand.** The owner approved this
   on 2026-11-24. It stays within the exact scope `KOR.M.LI_AA.IX._T` and rights decision of
   ADR 0007, and it is a manual capture, not a weekly download, as ADR 0007 decision 6 requires.
   The capture `oecd-stes-cli-kor-li-aa-20261124t010648941132z` (commit `6259fab`) holds 242
   editions (`200604`–`202611`). Every row of the 2026-07-17 archive is present with the same
   value. Edition `202608` is listed by the dataflow but has no Korea CLI rows.
2. **Admit evidence version 2.**
   - Snapshot registry `kor-rtd-latest-only-snapshot-registry-v2`: the ECOS GDP, ECOS current
     account, and KOSIS CPI snapshots of the 2026-07-17, 2026-11-02, 2026-11-09, 2026-11-16, and
     2026-11-23 captures.
   - STES registry `kor-rtd-stes-resolver-registry-v2`: the 2026-11-24 archive, every OECD
     constraint capture and ledger through 2026-11-23, and that day's ledger as the active one.
   - Both are pinned by digest, as v1 is. The execution layer names the pair
     `kor-rtd-execution-artifact-registry-v2`.
3. **Version 1 stays, unchanged, beside version 2.** Its digests and contents do not move, and
   the five committed traces keep replaying it.
4. **A record is checked against one evidence version.** A record whose tool expectation names an
   availability ledger belongs to the version whose active ledger it names, because the gold was
   computed against that ledger. Every other record is checked against the latest version, which
   must still reproduce it. Approved records are not migrated, so `kv-core-data-01` and
   `kv-core-both-01` stay on version 1. New records cite version 2.
5. **Designating the reserved test-split data release is still open.** Edition `202611` and the
   November snapshots are candidates for `reserved-future-data-release-test-01`, but the owner
   decides that when `kv-core-data-05` is drafted.

## Alternatives considered

- **Replace version 1 with version 2 everywhere.** Rejected: the two approved vintage pairs name
  the 2026-07-17 archive and ledger, so they would need new source and ledger identifiers and a
  fresh owner review, for no change in their answers.
- **Admit only the OECD evidence.** Rejected: the owner approved admitting the weekly captures as
  a whole, and the snapshots add months that the July captures did not hold.
- **Admit the ledgers without a new archive.** Rejected: the resolver would select editions
  `202610` and `202611` and then find no rows for them in the July archive.

## Consequences

- One month can now be shown both right then and wrong now through ledger-proven vintages: the
  May 2026 Korea CLI is 102.66 as of 2026-07-09 (edition `202607`), 102.33 as of 2026-10-08
  (`202610`), and 102.29 as of 2026-11-10 (`202611`). Every month from January to June 2026 was
  revised down by about 0.4.
- Under version 2, cutoffs from 2026-07-17 through 2026-10-07 abstain with
  `unresolved_newer_edition`: editions `202608`–`202610` were absent at the 2026-07-17 capture and
  are provably available only from 2026-10-08. This is the lasting cost of the capture gap.
  2026-11-09 abstains for the same reason, inside the bracket that dates `202611`.
- `kv-core-abstain-05` (as of 2026-08-15) still abstains under version 2, but for
  `unresolved_newer_edition` rather than the `cutoff_beyond_complete_through` that its rationale
  describes. The record is unchanged and is read against version 1.
- The ECOS and KOSIS captures show no revision to any month between 2026-07-17 and 2026-11-23;
  later captures only add months.
- The repository grows by one 22 MB archive. A third capture needs its own owner approval.

## Revisit triggers

- The owner admits a later capture, which becomes version 3.
- The owner designates the reserved test-split data release.
- OECD changes a value in an edition that an admitted archive already holds.
