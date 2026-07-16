# Week-1 verification log — 2026-07-15

- Status: observed, metadata-only verification record
- Scope: public OECD SDMX accessibility, response integrity, edition semantics, forecast coverage,
  and candidate ECOS rights metadata
- Cost: USD 0; no key, paid API, OCR, embedding, or GPU operation
- Payload policy: response bodies were inspected under `%TEMP%` and were not added to the repository

This file preserves enough request metadata and parsing instructions to repeat the spike after a
workstation loss without committing the downloaded datasets. All timestamps are UTC. On the Windows
workstation, `curl.exe --ssl-no-revoke` was needed because Schannel could not reach its certificate
revocation service; ordinary TLS certificate validation remained enabled.

## 1. Capture method

Create one run directory, then call `Save-Probe` for every entry in the request catalog. Re-running
the setup block creates a different directory, so do it only once before all captures that will be
parsed together. Bodies and headers remain outside the repository.

```powershell
$run = Join-Path $env:TEMP ("sovereignlab-week1-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
New-Item -ItemType Directory -Path $run | Out-Null

function Save-Probe([string] $Id, [string] $Url) {
  $body = Join-Path $run "$Id.body"
  $headers = Join-Path $run "$Id.headers"
  $started = (Get-Date).ToUniversalTime().ToString("o")
  $metrics = curl.exe --ssl-no-revoke --silent --show-error --location `
    --dump-header $headers --output $body `
    --write-out "%{http_code}|%{content_type}|%{size_download}|%{time_total}" `
    $Url
  [pscustomobject]@{
    id = $Id
    started_at_utc = $started
    metrics = $metrics
    bytes = (Get-Item -LiteralPath $body).Length
    sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $body).Hash.ToLowerInvariant()
  }
}

Save-Probe -Id "<id>" -Url "<url>"
```

## 2. Exact request catalog and response metadata

### Archive/public tenant conflict

| ID | Exact URL | Started UTC | HTTP / bytes | SHA-256 |
|---|---|---|---:|---|
| `mei_archive_data` | `https://sdmx.oecd.org/archive/rest/data/OECD,DF_MEI_ARCHIVE,/KOR.101..Q?format=csvfilewithlabels` | `2026-07-15T05:58:07.4755157Z` | 200 / 10,581,205 | `0bf918fe7415787fb1f6a3ddf52a406527d6a09b76b00db53de3175354d61f80` |
| `mei_public_data` | `https://sdmx.oecd.org/public/rest/data/OECD,DF_MEI_ARCHIVE,/KOR.101..Q?format=csvfilewithlabels` | `2026-07-15T05:58:12.0038485Z` | 404 / 65 | `846d4838318a0ab8726d76d2c19235993e04609ee3f68e66f2404eda8fc293c2` |
| `mei_archive_structure` | `https://sdmx.oecd.org/archive/rest/dataflow/OECD/DF_MEI_ARCHIVE/latest?references=all` | `2026-07-15T05:58:12.2389329Z` | 200 / 422,749 | `7ef09475bfd64922cc7bd6b27d26ba5cab81aed4a944b06d632f9edc1a25dd34` |
| `mei_public_structure` | `https://sdmx.oecd.org/public/rest/dataflow/OECD/DF_MEI_ARCHIVE/latest?references=all` | `2026-07-15T05:58:13.9864994Z` | 404 / 35 | `eb633bf10c57d8e2934d96cdd0cec1fbb2fd376a2ea72e4a729bbe6867e05761` |

The data response media type was SDMX-CSV v2. The structure response was SDMX-ML 2.1. The exact
public-tenant 404s and archive-tenant 200s settle current accessibility, while the unpreserved
2026-07-14 failing URL remains insufficient to prove the historical cause.

### Live STES examples

| ID | Exact URL | Started UTC | HTTP / bytes | SHA-256 |
|---|---|---|---:|---|
| `stes_structure` | `https://sdmx.oecd.org/public/rest/dataflow/OECD.SDD.STES/DSD_STES_REVISIONS%40DF_STES_REVISIONS/latest?references=all` | `2026-07-15T05:58:14.9575674Z` | 200 / 1,890,676 | `c38459138c7748ff35cd1b2af255bcf8b0dade35632e54c02df6a7e6eaa9a0cf` |
| `stes_gdp_2025q1` | `https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES_REVISIONS%40DF_STES_REVISIONS,/KOR.Q.B1GQ_Q...?startPeriod=2025-Q1&endPeriod=2025-Q1&format=csvfilewithlabels` | `2026-07-15T05:58:16.2130721Z` | 200 / 4,770 | `484ba74366c07d1911e70988aa202fcbe1bc384b0f743aae2b70bf6d9dc497fa` |
| `stes_cpi_2005m01` | `https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES_REVISIONS%40DF_STES_REVISIONS,/KOR.M.CP...?startPeriod=2005-01&endPeriod=2005-01&format=csvfilewithlabels` | `2026-07-15T05:58:16.4203699Z` | 200 / 63,799 | `0e45f924a9c2a4742729f649893c54e836200ca268171e7897f1748cd7c3a572` |

All three returned HTTP 200. The two data responses were SDMX-CSV v2; the structure response was
SDMX-ML 2.1.

### Edition availability metadata

| ID | Exact URL | Started UTC | HTTP / bytes | SHA-256 |
|---|---|---|---:|---|
| `stes_content_constraint` | `https://sdmx.oecd.org/public/rest/contentconstraint/OECD.SDD.STES/CR_A_DSD_STES_REVISIONS%40DF_STES_REVISIONS/4.0?references=none` | `2026-07-15T06:00:08.0530300Z` | 200 / 23,251 | `d1baba8888a670ae3cd9250d1a634f3b245035dec38452157f166146574c32c2` |
| `stes_edition_codelist` | `https://sdmx.oecd.org/public/rest/codelist/OECD.SDD.STES/CL_EDITION/1.0?references=none` | `2026-07-15T06:00:09.3539748Z` | 200 / 70,366 | `677711acbc834c44b37381fda235468e905e9253ef35b4dd315f0da7d9b630dd` |
| `stes_available_editions` | `https://sdmx.oecd.org/public/rest/availableconstraint/OECD.SDD.STES,DSD_STES_REVISIONS%40DF_STES_REVISIONS,4.0/all/all/EDITION?mode=exact` | `2026-07-15T06:00:10.4907984Z` | 200 / 17,828 | `894048245d07e8d445a53bbbd803ca7e468f546a0335b2118f6dcab947dd9598` |

The codelist contains 359 labels from `199902` through future `202812`; the constraint and exact
availability response contain 330 actual editions through `202607`. The content constraint records
`validFrom=2026-07-08T09:33:35.737Z` and an observation-count annotation of 77,774,490. These facts
show that code existence and current data availability are different concepts.

### `updatedAfter` diagnostic boundaries

All four requests use one exact KOR 2025-Q1 GDP edition. They were made between
`2026-07-15T05:58:16Z` and `05:58:30Z`.

| Edition | `updatedAfter` | HTTP / bytes | SHA-256 |
|---|---|---:|---|
| `202606` | `2026-06-09T00:00:00Z` | 200 / 2,064 | `7369115b485bf7d3f09895be510fdf8b5a608392faa2d829b6480354e028907d` |
| `202606` | `2026-06-10T00:00:00Z` | 404 / 14 | `561bbca5e9218b3118675bf69a7d4916bac5a1b54b1d0abd268a7adca13fc0dc` |
| `202607` | `2026-07-08T00:00:00Z` | 200 / 2,064 | `e32350be075f35f09a6b54b225bde62b5f0e34bd0350e11e482346e976da884d` |
| `202607` | `2026-07-09T00:00:00Z` | 404 / 14 | `561bbca5e9218b3118675bf69a7d4916bac5a1b54b1d0abd268a7adca13fc0dc` |

Request shape, with the edition and date substituted per row:

```text
https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES_REVISIONS%40DF_STES_REVISIONS,/KOR.Q.B1GQ_Q...<edition>?startPeriod=2025-Q1&endPeriod=2025-Q1&updatedAfter=<timestamp>&format=csvfilewithlabels
```

This brackets when the current rows were last updated. It does **not** prove first publication,
especially for historical editions that may have been migrated or rebased later. ADR 0005 therefore
keeps June 2026 unresolved for strict-core use and relies on the July constraint only as a
conservative `available_by` bound; state before that bound remains unknown without absence evidence.

## 3. Parser commands and reproduced results

SDMX label CSV contains case-insensitively duplicated column names such as `MEASURE`/`Measure`, so
PowerShell `Import-Csv` is not a valid parser for these responses. The spike used Python's standard
`csv.DictReader` against the temporary files:

```powershell
$env:SOVEREIGNLAB_SPIKE_DIR = $run
@'
import csv
import os
from pathlib import Path

root = Path(os.environ["SOVEREIGNLAB_SPIKE_DIR"])

def read(name):
    with (root / name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))

archive = read("mei_archive_data.body")
gdp = read("stes_gdp_2025q1.body")
cpi = read("stes_cpi_2005m01.body")
archive_editions = sorted({row["EDI"] for row in archive})
archive_2010q1 = [row for row in archive if row["TIME_PERIOD"] == "2010-Q1"]
gdp_editions = sorted({row["EDITION"] for row in gdp})
cpi_editions = sorted({row["EDITION"] for row in cpi})

print(len(archive), len(archive_editions), archive_editions[0], archive_editions[-1])
print("200904" in archive_editions)
print(len(archive_2010q1), len({row["OBS_VALUE"] for row in archive_2010q1}))
print(len(gdp), gdp_editions[0], gdp_editions[-1])
print({row["EDITION"]: row["OBS_VALUE"] for row in gdp if row["EDITION"] in {"202606", "202607"}})
print(len(cpi), cpi_editions[0], cpi_editions[-1])
'@ | .\.venv\Scripts\python.exe -
```

Observed output:

```text
44138 299 199902 202401
False
165 10
15 202505 202607
{'202606': '572057700000000', '202607': '574984300000000'}
258 200502 202607
```

The archive structure separately declares 300 edition codes, 65 location codes (including
aggregates), 24 variables, and two frequencies. The KOR quarterly-GDP slice has 299 editions because
`200904` has no row. The 2010-Q1 slice has 165 editions and ten distinct values. The live GDP and CPI
counts reproduce the feasibility examples without committing their response bodies.

## 4. Economic Outlook observation-range spike

The archive catalog request
`https://sdmx.oecd.org/archive/rest/dataflow/all/all/latest` returned HTTP 200 at
`2026-07-15T06:00:07.982Z`: 1,204,828 bytes, SHA-256
`772083ab857b83a78cd5c4f27745e98c3b9c938490c2254899d93e247e0908eb`. Its 112 EO flows
enumerate all edition numbers 60–114, but catalog continuity is not observation continuity.

Archive boundary structures:

| Edition | Exact structure URL | Started UTC | HTTP / bytes | SHA-256 |
|---|---|---|---:|---|
| EO60 | `https://sdmx.oecd.org/archive/rest/dataflow/OECD/DF_EO60_MAIN/latest?references=all` | `2026-07-15T06:01:09.600Z` | 200 / 268,243 | `17eeb1692a3750bbbdb545c4a60bae84f9623b3cda0bcf2c553a20c46409badd` |
| EO107 | `https://sdmx.oecd.org/archive/rest/dataflow/OECD/DF_EO107_EDITIONS/latest?references=all` | `2026-07-15T06:01:11.347Z` | 200 / 276,603 | `eba1bd645f12bb18a05b9f32b40458e7164fefa1ed35422ff23034063bb4eea6` |
| EO114 | `https://sdmx.oecd.org/archive/rest/dataflow/OECD/DF_EO114_INTERNET/latest?references=all` | `2026-07-15T06:01:13.215Z` | 200 / 451,478 | `83447c160473e68d7995720e6588211f21a39b0a3567cb3663f3d941f4bb89f6` |

The exact DSD dimension orders are `LOCATION.VARIABLE.FREQUENCY` for EO60 and EO114, and
`LOCATION.VARIABLE.EDITION.FREQUENCY` for the two-scenario EO107. Archive KOR observation samples:
when reproducing, save these bodies with IDs `eo_archive_60`, `eo_archive_107`, and
`eo_archive_114`.

| Flow | Exact KOR URL | Started UTC | HTTP / bytes / rows | SHA-256 | Result boundary |
|---|---|---|---:|---|---|
| EO60 | `https://sdmx.oecd.org/archive/rest/data/OECD,DF_EO60_MAIN,1.0/KOR..?format=csvfilewithlabels` | `2026-07-15T06:03:00.321Z` | 200 / 6,332 / 29 | `d1093f99ea672d0f10afc6c0279747c4dff2d90e5b50f18b0ceb265ce9768476` | Only `EXCHUD`, annual 1970–1998; `GDPV` absent |
| EO107 | `https://sdmx.oecd.org/archive/rest/data/OECD,DF_EO107_EDITIONS,1.0/KOR...?format=csvfilewithlabels` | `2026-07-15T06:03:03.959Z` | 200 / 5,800,292 / 22,258 | `bf8d39ebed973df1b5dbb2f81d7c9d3ce2597831c604a6d62dc48bce853480dc` | 43 variables, two scenarios, A/Q through 2021; `GDPV` present |
| EO114 | `https://sdmx.oecd.org/archive/rest/data/OECD,DF_EO114_INTERNET,1.0/KOR..?format=csvfilewithlabels` | `2026-07-15T06:03:08.130Z` | 200 / 7,737,840 / 36,670 | `f7f0ad03c747831fbb6ac8ff3875202d727cb2340502838c06a6ecbb47227c1a` | 212 variables, A/Q through 2025; `GDPV` present |

The EO60 `KOR.GDPV.A` request returned HTTP 404 `NoRecordsFound` (14 bytes; SHA-256
`561bbca5e9218b3118675bf69a7d4916bac5a1b54b1d0abd268a7adca13fc0dc`). The archive therefore
does not support a blanket KOR-variable continuity claim. There is no literal `DF_EO114`; the main
boundary flow is `DF_EO114_INTERNET`, with a separate `DF_EO114_LTB`.

The public catalog request
`https://sdmx.oecd.org/public/rest/dataflow/OECD.ECO.MAD/all/latest` returned HTTP 200 at
`2026-07-15T06:01:13.595Z`: 46,365 bytes, SHA-256
`a4dedee06b792101977937c5fc6f8e37e4f69666f5b576fb39fc7ecf0380eb5b`. EO114–EO118 use
`DSD_EO_11x@DF_EO_11x` version 1.0; current EO119 uses `DSD_EO@DF_EO` version 1.5. Both boundary
DSDs use `REF_AREA.MEASURE.FREQ`. The exact EO114 structure response was captured at
`2026-07-15T06:02:09.752Z` (HTTP 200, 1,335,358 bytes, SHA-256
`4cc6e4870a1f7639afebf8cddc488ce95e4552577e95aba16ba01d11862c32e3`); EO119 was captured at
`2026-07-15T06:02:14.310Z` (HTTP 200, 1,465,238 bytes, SHA-256
`c819322bbb3996dcf373779e1657686712d938809ab268ffe10b818196722d1a`). The URLs were respectively
`https://sdmx.oecd.org/public/rest/dataflow/OECD.ECO.MAD/DSD_EO_114%40DF_EO_114/latest?references=all`
and `https://sdmx.oecd.org/public/rest/dataflow/OECD.ECO.MAD/DSD_EO%40DF_EO/latest?references=all`.

Public KOR observation responses:
when reproducing, save these bodies with IDs `eo_public_114` through `eo_public_119`.

| Edition | Exact URL | Started UTC | HTTP / bytes / rows | Variables / range | SHA-256 |
|---|---|---|---:|---|---|
| 114 | `https://sdmx.oecd.org/public/rest/data/OECD.ECO.MAD,DSD_EO_114%40DF_EO_114,1.0/KOR..?format=csvfilewithlabels` | `2026-07-15T06:03:14.155Z` | 200 / 13,870,307 / 56,331 | 212; A/Q 1960–2025 | `369a79e2db77ce1b9be89d67c0b42f97b51c0c0514a121ecea6903c4645f0d51` |
| 115 | `https://sdmx.oecd.org/public/rest/data/OECD.ECO.MAD,DSD_EO_115%40DF_EO_115,1.0/KOR..?format=csvfilewithlabels` | `2026-07-15T06:03:22.430Z` | 200 / 8,879,440 / 36,990 | 213; A/Q 1960–2025 | `cec55c85f31e4c38a62771b3a26d29d6bf30ee3e74550ced34411b7e7fd149d2` |
| 116 | `https://sdmx.oecd.org/public/rest/data/OECD.ECO.MAD,DSD_EO_116%40DF_EO_116,1.0/KOR..?format=csvfilewithlabels` | `2026-07-15T06:03:28.001Z` | 200 / 8,950,763 / 36,898 | 213; A/Q 1960–2026 | `53cfcae017baf4f62ea0bb68536dec65cf2bbdb9ccd6dac8ed729dc9af4e94f1` |
| 117 | `https://sdmx.oecd.org/public/rest/data/OECD.ECO.MAD,DSD_EO_117%40DF_EO_117,1.0/KOR..?format=csvfilewithlabels` | `2026-07-15T06:03:34.635Z` | 200 / 8,949,892 / 36,918 | 213; A/Q 1960–2026 | `d32d4bab60cfa038f791f5a98b7c750e9564c5518b7e7fe8a03dd77ad279570a` |
| 118 | `https://sdmx.oecd.org/public/rest/data/OECD.ECO.MAD,DSD_EO_118%40DF_EO_118,1.0/KOR..?format=csvfilewithlabels` | `2026-07-15T06:03:42.143Z` | 200 / 9,122,962 / 37,647 | 213; A/Q 1960–2027 | `b223fa1141a067449aab7f7e2843336d60a9449f55eb2f1d3c2c80e0d1aa01fe` |
| 119 | `https://sdmx.oecd.org/public/rest/data/OECD.ECO.MAD,DSD_EO%40DF_EO,1.5/KOR..?format=csvfilewithlabels` | `2026-07-15T06:03:48.287Z` | 200 / 8,734,331 / 37,782 | 213; A/Q 1960–2027 | `9b54eb6d701257e2786b003e6f347aa32b94a914836e9160bc2345af6b83d546` |

All six full responses contained nonblank annual and quarterly `GDPV` over their reported ranges.
Later narrow repeat requests preserved the following negative rate-limit result; UTC here is the
response-body file modification time because the first probe did not separately log request start:

| Edition | Exact narrow URL | Recorded UTC | HTTP / bytes | SHA-256 |
|---|---|---|---:|---|
| 117 | `https://sdmx.oecd.org/public/rest/data/OECD.ECO.MAD,DSD_EO_117%40DF_EO_117,1.0/KOR.GDPV.A?format=csvfilewithlabels` | `2026-07-15T06:07:29.426Z` | 429 / 281 | `b80fcf2dbe752a67d815c9a78bf9b0d8ceeac7f463dfa14eff6497c40792b609` |
| 118 | `https://sdmx.oecd.org/public/rest/data/OECD.ECO.MAD,DSD_EO_118%40DF_EO_118,1.0/KOR.GDPV.A?format=csvfilewithlabels` | `2026-07-15T06:07:29.633Z` | 429 / 281 | `b80fcf2dbe752a67d815c9a78bf9b0d8ceeac7f463dfa14eff6497c40792b609` |
| 119 | `https://sdmx.oecd.org/public/rest/data/OECD.ECO.MAD,DSD_EO%40DF_EO,1.5/KOR.GDPV.A?format=csvfilewithlabels` | `2026-07-15T06:07:29.825Z` | 429 / 281 | `b80fcf2dbe752a67d815c9a78bf9b0d8ceeac7f463dfa14eff6497c40792b609` |

The identical bodies are OECD API download-rate-limit notices. They do not invalidate the earlier
full HTTP 200 responses. The claimable recent forecast-vintage range is **EO114–EO119**; archive
coverage is described only as catalog continuity plus the three sampled KOR flows.

The row, measure, frequency, period-range, and `GDPV` checks behind both tables use the same
case-sensitive standard-library parser as the STES checks:

```powershell
$env:SOVEREIGNLAB_SPIKE_DIR = $run
@'
import csv
import os
from pathlib import Path

root = Path(os.environ["SOVEREIGNLAB_SPIKE_DIR"])

def summarize(name):
    with (root / f"{name}.body").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    measure_key = "MEASURE" if "MEASURE" in rows[0] else "VARIABLE"
    freq_key = "FREQ" if "FREQ" in rows[0] else "FREQUENCY"
    frequencies = sorted({row[freq_key] for row in rows})
    ranges = {
        freq: (
            min(row["TIME_PERIOD"] for row in rows if row[freq_key] == freq),
            max(row["TIME_PERIOD"] for row in rows if row[freq_key] == freq),
        )
        for freq in frequencies
    }
    gdpv = [row for row in rows if row[measure_key] == "GDPV"]
    return {
        "rows": len(rows),
        "measures": len({row[measure_key] for row in rows}),
        "ranges": ranges,
        "gdpv_rows": len(gdpv),
        "gdpv_nonblank": bool(gdpv) and all(row["OBS_VALUE"] for row in gdpv),
    }

for name in (
    "eo_archive_60", "eo_archive_107", "eo_archive_114",
    "eo_public_114", "eo_public_115", "eo_public_116",
    "eo_public_117", "eo_public_118", "eo_public_119",
):
    print(name, summarize(name))
'@ | .\.venv\Scripts\python.exe -
```

Observed row/measure/range output is recorded in the two tables above. The `gdpv_nonblank` result was
`False` for archive EO60 because no `GDPV` row exists, and `True` for archive EO107/114 and every
public EO114–EO119 response.

## 5. Candidate ECOS metadata and rights gap

No observation endpoint was called. Exact ECOS metadata was read at
`2026-07-15T06:08:58Z`:

- `200Y108/10601`: [item metadata](https://ecos.bok.or.kr/api/StatisticItemList/sample/json/kr/21/21/200Y108/)
  and [table metadata](https://ecos.bok.or.kr/api/StatisticTableList/sample/json/kr/1/10/200Y108/)
  identify “domestic expenditure on GDP,” quarterly, billion KRW, seasonally adjusted and real.
  Exact-table `ORG_NAME` is null.
- `301Y017/SA000`: [item metadata](https://ecos.bok.or.kr/api/StatisticItemList/sample/json/kr/1/10/301Y017/)
  and [table metadata](https://ecos.bok.or.kr/api/StatisticTableList/sample/json/kr/1/10/301Y017/)
  identify the seasonally adjusted current account, monthly, million USD. Exact-table `ORG_NAME` is
  Bank of Korea.

Public Data Portal family metadata was read at `2026-07-15T06:07:57Z`:

- [National Accounts OpenAPI family](https://www.data.go.kr/data/15059629/openapi.do) and its
  [machine metadata](https://www.data.go.kr/catalog/15059629/openapi.json);
- [Balance of Payments OpenAPI family](https://www.data.go.kr/data/15059631/openapi.do) and its
  [machine metadata](https://www.data.go.kr/catalog/15059631/openapi.json).

Both family records name Bank of Korea and state `이용허락범위 제한 없음`, but neither contains the
exact ECOS table/item identifier. The earlier file-data record `15014296` links to an annual
national-accounts family and is not evidence for quarterly `200Y108`. Exact ECOS metadata has no
licence, KOGL, or third-party-rights field. Based only on that 2026-07-15 metadata set, both
candidates were provisionally held `metadata_only`; the source-wide use-guide and producer
evidence verified below supersede that provisional rights conclusion.

### 2026-07-16 rights-policy addendum

No observation endpoint was called and no source response body was committed during this follow-up.

- The official [ECOS site](https://ecos.bok.or.kr/) footer exposes the “ECOS Statistics Information
  Use Guide”. Its deployed official JavaScript bundle was fetched at
  `2026-07-16T02:03:32Z` only for text verification
  ([bundle URL](https://ecos.bok.or.kr/static/js/main.360c53e9.chunk.js), 365,214 bytes, SHA-256
  `bea6909910e2c2c341d3e72a581442addcd515d16b700845c74368fbb39a6080`) and was not added to the
  repository. The text matches the owner-supplied guide: Bank of Korea-produced statistics permit
  attributed commercial/non-commercial use, processing, and redistribution; other-producer
  statistics permit attributed non-commercial use, while commercial use requires that producer's
  approval. The latter branch does not expressly grant processing or redistribution, so public raw
  commits remain fail-closed without a more specific instrument.
- The official [KOSIS Statistics Information Use Guide](https://kosis.kr/nsistN/kosisUseGuide.do)
  was checked on 2026-07-16. In-scope domestic macro statistics permit attributed commercial and
  non-commercial use, reuse, and redistribution, while unchanged raw information may not be sold
  as a paid standalone product. International and North Korea statistics are non-commercial-only
  and may not be redistributed; publications follow their individual KOGL notices.
- `301Y017/SA000` is directly classified as Bank of Korea-produced by its ECOS table metadata.
  For `200Y108/10601`, the ECOS item endpoint maps the exact item code to the quarterly seasonally
  adjusted real domestic-expenditure-on-GDP table; the
  [KOSIS official recent-data record](https://kosis.kr/serviceInfo/newContrainDataDetail.do?boardIdx=1976017&boardOrgId=301)
  names Bank of Korea for the same title and frequency, corroborated by an official
  [Bank of Korea GDP release](https://www.bok.or.kr/portal/bbs/B0000501/view.do?menuNo=200690&nttId=10097644).
  This is official cross-source evidence, but the exact ECOS code-to-producer join is
  title/frequency-based rather than a direct identifier field and therefore remains an
  owner-approved mapping.

The corrected proposed ruling for `301Y017/SA000` is `allowed` under the ECOS guide, pending owner
approval. The same ruling is proposed for `200Y108/10601` if the owner accepts the recorded
title/frequency mapping; otherwise it remains metadata-only pending a direct code-to-producer
source. Neither is rights-unknown, but operationally both remain metadata-only until each exact
series has a complete, owner-approved `SeriesRightsDecision`, required attribution, and a matching
validated source manifest. This turns the gate from repeated licence discovery into a fail-closed,
auditable producer/category and attribution mapping.

## 6. Claim boundary

- `DF_MEI_ARCHIVE` is currently accessible only on the archive tenant and is marked
  `NonProductionDataflow=true`; availability is not a service guarantee.
- The live STES flow is also marked non-production.
- Monthly edition labels cannot answer a day-specific `as_of` request without a separate verified
  availability mapping.
- Public EO114–EO119 is the verified KOR observation range for forecast-vintage work. The archive
  catalog enumerates EO60–EO114, but only EO60/107/114 KOR observations were sampled; no continuous
  archive KOR backfill or variable-consistency claim is permitted.
- No downloaded response body in this spike is a committed data artifact or redistribution ruling.
