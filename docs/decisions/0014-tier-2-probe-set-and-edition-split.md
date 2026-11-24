# ADR 0014: tier-2 probe set v1 and the edition split

- Status: accepted. On 2026-11-24 the owner asked for the probe generator and chose the test
  edition. The human audit of the probe sample is pending.
- Date: 2026-11-24
- Related: charter §5 (two-tier gold set) and §7 (week 2); ADR 0005; ADR 0013;
  `data/benchmark/probes/README.md`
- Amends: nothing. It settles the designation that ADR 0013 decision 5 left open.

## Context

The charter defines K-VINTAGE as two tiers, always reported separately: 40 human-reviewed core
records, and 200–300 machine-generated data-route probes with computed, regenerable golds and a
documented human audit of a sample. Until now only the core existed (26 of 40 records approved).

Evidence version 2 made three OECD editions answerable through ledger-proven availability:
`202607` for cutoffs from 2026-07-08 to 2026-07-16, `202610` from 2026-10-08 to 2026-11-08, and
`202611` from 2026-11-10 to 2026-11-22. Their values differ for many months, so questions can be
generated whose gold depends on the cutoff, and an answer taken from a later vintage can be caught
mechanically.

Splits must be evidence-disjoint. The core matrix already places edition `202607` in train
(`kv-core-data-01`, `kv-core-both-01`). It reserves an unnamed test-split data release,
`reserved-future-data-release-test-01`, for `kv-core-data-05` and `kv-core-both-05`.

## Decision

1. **Probe set `kv-probes-oecd-cli-v1`.** It lives in `data/benchmark/probes/`, and
   `sovereignlab.probes` generates it from evidence version 2 only, through
   `scripts/generate_probes.py`. It has two families over the Korea CLI, each asked as a
   Korean/English pair:
   - *As-of value* (route `data`): every month from January 2023 to the edition's last month.
     A month is tagged `revision-trap` when any later edition in the admitted archive holds a
     different value, and `unrevised` otherwise.
   - *Future period* (route `abstain`): the two months after the edition's last month.
2. **The ledger sets the cutoffs and the resolver sets the golds.** Each item's cutoff is one of
   the days on which the ledger selects its edition, taken in turn, so both edges of every window
   are used. The gold is the resolver's result for the record's exact typed arguments. Generation
   stops if the resolver selects another edition, or does not abstain with `missing_selected_row`
   for a future month. The committed file must equal a fresh generation byte for byte.
3. **Machine items stay drafts.** Every probe is a `draft`, annotated by
   `sovereignlab probe generator v1` and tagged `probe`, never `core`. No probe enters
   `data/benchmark/core/` or counts toward the core.
4. **The split follows the edition.** Each edition is one evidence group,
   `eg-probe-oecd-cli-{edition}`, in exactly one split. `202607` is train, because the core
   already uses it there. The owner chose `202610` for test on 2026-11-24, which leaves `202611`
   for dev.
5. **The split holds in both tiers.** The question the owner answered stated that choosing the
   test edition also fixes the core's reserved test-split data release. Edition `202610` is
   therefore the release for `kv-core-data-05` and `kv-core-both-05`. A core record may use an
   OECD edition only in that edition's probe split, so `202611` may not appear in core train or
   test. `tests/benchmark/test_core.py` enforces this. The matrix keeps its placeholder unit ID
   until those pairs are drafted and reviewed; this ADR does not edit the matrix.
6. **The audit sample is fixed in advance.** It has all six future-period pairs and every tenth
   as-of value pair in file order: 20 pairs, 40 records. The probe README lists the sample and
   the procedure. The owner performs the audit, and its outcome is recorded there. The audit
   checks the generator, so it changes no record's annotation.

## Alternatives considered

- **Test = `202611`**, following the convention that the newest data is the test set. The owner
  declined it: no admitted edition revises `202611` yet, so the test split could not measure
  leakage until an edition from `202612` on is captured and admitted.
- **Split by month or by cutoff inside an edition.** Rejected: one edition's values would appear
  in train and test. The bundle validator rejects an evidence group that crosses splits.
- **Paraphrased questions written by a model.** Rejected for v1: it is a paid operation, it is not
  deterministic, and it would need its own review. Templates keep every gold reproducible offline.
- **ECOS and KOSIS probes.** Deferred: no value of those series changed between 2026-07-17 and
  2026-11-23, so they would add no revision traps.
- **Data-route items only**, as the charter's tier-2 wording reads. Not chosen: future-period
  items are the plainest leakage test, since any number at all comes from a later vintage. Their
  12 records are reported as a family of their own, and the 266 as-of value records are the tier-2
  count, so the family can be dropped without changing anything else.

## Consequences

- 278 records, 139 pairs, 139 records in each language. Train has 84 as-of value records (all
  revision traps) and 4 future-period records. Test has 90 as-of value records (40 revision traps)
  and 4 future-period records. Dev has 92 as-of value records (none revised yet) and 4
  future-period records.
- Leakage is measurable now on train and test. Dev gains revision traps only when an edition newer
  than `202611` is admitted. Probe set v1 stays pinned to evidence version 2; a later version
  would yield a new probe set under its own ID.
- One train trap, May 2023 in `202607`, differs only in `202609`, an edition no cutoff can select.
  An answer from the newest edition passes it.
- The core's test-split data pairs can be drafted on edition `202610` whenever the owner selects
  them.
- The probes cover one series with one template per family and language. They test cutoff and
  vintage discipline, not language understanding or document use.
- Regenerating and replaying the probes adds about two seconds to the test suite. The resolver now
  caches its parse of an archive by the archive's bytes. Its answers are unchanged: before the
  cache was committed, it was compared with the previous implementation on 1,336 calls.

## Revisit triggers

- The owner records the audit, or the audit finds an error.
- An edition newer than `202611` is admitted.
- `kv-core-data-05` or `kv-core-both-05` is drafted.
- Any model is tuned or selected on probe data.
