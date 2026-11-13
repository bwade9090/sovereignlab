# Replay traces

`replay/v1/` holds five `ExecutionTrace` 1.0.0 files produced by the offline executor from the
fixed scenarios in `scripts/export_execution_replay_traces.py`. They are generated, not
hand-written, and contain no provider response, credential, or machine-local path.

```bash
python scripts/export_execution_replay_traces.py --check   # confirm the files are reproducible
python scripts/export_execution_replay_traces.py --write   # regenerate after changing src/
```

Each trace records `executor_sha256`, a digest of the source tree that produced it, so the files
must be regenerated whenever `src/` changes. The test suite fails until they match.

| Trace | Route | Language | Cutoff | Outcome |
| --- | --- | --- | --- | --- |
| 001 | documents | Korean | explicit | complete |
| 002 | data (`resolve_stes_as_of`) | English | explicit | complete |
| 003 | documents and data (`read_snapshot_as_of`) | English | implicit | complete |
| 004 | abstain | Korean | implicit | planned abstention; no tool runs |
| 005 | documents and data | English | explicit | the snapshot tool abstains; the later STES call does not run and the packet carries no partial evidence |

These are deterministic offline replays of scripted plans. They are not model outputs and support
no claim about model quality or briefing performance. Failure traces (a rejected plan, a tool
error) are covered by tests rather than committed here, because the committed evidence does not
produce them.

In trace 002 the archive was captured on 2026-07-17 while the cutoff is 2026-07-09. That is not
leakage: the availability ledger proves edition `202607` was available by
`2026-07-08T09:33:35.737Z`, and the later date only says when these exact archive bytes were
captured.

## Attribution and terms

The document passages are synthetic fixtures. The traces follow the repository's non-commercial
public-research profile. The ECOS and OECD observations they contain keep their providers' terms
and attribution; Apache-2.0 does not relicense them.

Required rendered attribution for the ECOS observation in trace 003:

> 출처: ECOS(한국은행; 작성기관: 한국은행; 국내총생산에 대한 지출; 표 200Y108/항목 10601),
> 조회일 2026-07-17. KOR-RTD에서 빈티지 구조로 가공함.
> https://ecos.bok.or.kr/api/StatisticSearch/%7Bapi-key%7D/json/kr/1/1000/200Y108/Q/1960Q1/2026Q3/10601

Required rendered attribution for the OECD observation in trace 002:

> Source: OECD; original producer: OECD; statistic: Composite leading indicator (CLI) amplitude
> adjusted — Korea; retrieved 2026-07-17;
> https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES_REVISIONS%40DF_STES_REVISIONS,4.0/KOR.M.LI_AA...?format=csvfilewithlabels.
> KOR-RTD preserves the captured vintage; no OECD endorsement is implied.

Private or credential-bearing traces belong under `traces/private/`, which Git ignores. Never
promote one into this public set.
