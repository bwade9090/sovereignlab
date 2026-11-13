# SovereignLab

> What did the data say *then*? Vintage-conditioned evaluation and auditable briefings for
> Korean/English economic research.

Korea's official statistics APIs (ECOS, KOSIS) return the latest values and have no "as-of" query
path for the series this project uses. An analyst, a forecaster, or a model evaluated on a past
date can therefore silently use numbers that did not exist yet. SovereignLab complements that
public infrastructure with three things:

1. **KOR-RTD** — a point-in-time data layer for Korean macroeconomics: a consolidated OECD edition
   history plus a weekly harvester that captures the latest-only official APIs. Captures are
   append-only and checksummed, and public commit history is the proof of capture dates.
2. **K-VINTAGE** — a bilingual Korean/English benchmark whose gold answers are computed from the
   data vintage available at each question's `as_of` date. To our knowledge, for official
   statistics, this is the first such benchmark; prior art includes arXiv 2605.23497 (statutory
   as-of QA), the Dallas Fed real-time OECD dataset, and the OECD MEI revisions database.
3. **A reference briefing path** — given a question and an `as_of` date, it routes to temporally
   filtered document retrieval, a deterministic vintage-resolving data tool, both, or a justified
   abstention, and returns the evidence with a machine-readable trace.

**Status:** milestone M2 (benchmark and baselines) is in progress. See
[project status](docs/PROJECT_STATUS.md) for the approved-record count, what is implemented, and
what comes next.

## What exists today

- **Evidence contracts** — strict models for source manifests, rights decisions, availability
  ledgers, benchmark records, and execution traces, published as JSON Schema in `data/schemas/`.
- **Weekly capture** — a GitHub Actions job that archives OECD edition metadata and the
  rights-approved ECOS GDP, ECOS current-account, and KOSIS CPI series.
- **Three offline evidence tools** — a fail-closed OECD vintage resolver, a latest-only snapshot
  reader, and bilingual document retrieval that filters by publication date before scoring. Each
  abstains rather than use evidence it cannot prove was available at the cutoff.
- **Typed function calling with committed traces** — a one-shot plan, the three tools, and an
  evidence packet, recorded as five replayable traces in `traces/replay/v1/`. These are
  deterministic offline replays: there is no live model integration yet, and no model-quality or
  briefing-performance result is claimed.
- **The K-VINTAGE core** — human-reviewed Korean/English record pairs under
  `data/benchmark/core/`, each reproduced by the tools in the test suite.

The searchable document corpus is a synthetic fixture. The real Bank of Korea reports are bound by
manifest and page-anchored in the benchmark, but their text is not committed.

## What will be tested

Four variants under one frozen benchmark: closed-book generation, temporal RAG, temporal RAG plus
the deterministic data tools, and the same system with a LoRA-tuned evidence router.

**Temporal-leakage rate is the headline metric**: a system that answers from values that did not
exist at `as_of` is caught mechanically, with no LLM judge. Further measurements are routing
macro-F1, tool-argument validity, Korean/English retrieval recall, citation correctness, numerical
provenance, abstention, latency, and cost.

## Quick start

Requires Python 3.12.

```bash
python3.12 -m venv .venv
source .venv/bin/activate            # Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

Everything above runs offline. `ECOS_API_KEY` and `KOSIS_API_KEY` are needed only to run the
capture yourself (`python scripts/harvest_weekly.py`); a missing key skips that provider.

## Documentation

- [Project charter](docs/project/01_project_charter.md) — scope and evaluation contract
- [Project status](docs/PROJECT_STATUS.md) — progress, next step, blockers, spend
- [Architecture](docs/architecture.md) — how the data layer, tools, and execution path work
- [Decision records](docs/decisions/README.md) — why it is built this way
- [Benchmark data guide](data/benchmark/README.md) and [data policy](data/README.md)
- [Replay traces](traces/README.md)
- [Number-normalization specification](docs/project/06_number_normalization_spec.md)
- [Contributor guide](AGENTS.md)

## Responsible disclosure

This project is conducted in a personal capacity using public information. It is not affiliated
with or endorsed by the Bank of Korea, the OECD, or Mistral AI.

## License

Original project code and documentation are licensed under Apache-2.0; see [LICENSE](LICENSE).
Third-party source data and redistributed observations are not relicensed: they remain subject to
the originating provider's terms and the attribution recorded in their manifests and rights
decisions. See the [data licensing boundary](data/README.md#licensing-boundary).
