"""Contract and evidence checks for the frozen core matrix and first draft batch."""

import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from sovereignlab.normalization import (
    NormalizedUnit,
    format_display,
    normalization_rule,
    normalize_source_value,
)
from sovereignlab.schemas import (
    AnnotationStatus,
    BenchmarkBundle,
    BenchmarkRecord,
    BenchmarkSplit,
    CoreAuthoringMatrix,
    CoreAuthoringPair,
    EditionAbstentionReason,
    EditionAvailabilityLedger,
    EvidenceRoute,
    RightsCatalog,
    SourceManifest,
    SourceSystem,
)
from sovereignlab.vintage import AsOfQuery, StesSeriesKey, resolve_stes_as_of

ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "data" / "benchmark" / "core-authoring-matrix-v1.json"
BATCH_PATH = ROOT / "data" / "benchmark" / "drafts" / "core-batch-001.jsonl"
CLI_SOURCE_ID = "oecd-stes-cli-kor-li-aa-20260717t115302688498z"
LEDGER_ID = "oecd-stes-ledger-20260717t115242998550z"
AVAILABILITY_SOURCE_ID = "oecd-stes-availableconstraint-20260717t101906273935z"
CONTENT_SOURCE_ID = "oecd-stes-contentconstraint-20260717t101906273935z"


def _matrix() -> CoreAuthoringMatrix:
    return CoreAuthoringMatrix.model_validate_json(MATRIX_PATH.read_text(encoding="utf-8"))


def _records() -> tuple[BenchmarkRecord, ...]:
    return tuple(
        BenchmarkRecord.model_validate_json(line)
        for line in BATCH_PATH.read_text(encoding="utf-8").splitlines()
        if line
    )


def _matrix_payload() -> dict:
    return json.loads(MATRIX_PATH.read_text(encoding="utf-8"))


def _manifest(source_id: str) -> SourceManifest:
    path = ROOT / "data" / "manifests" / f"{source_id}.json"
    return SourceManifest.model_validate_json(path.read_text(encoding="utf-8"))


def _ledger() -> EditionAvailabilityLedger:
    path = ROOT / "data" / "availability" / f"{LEDGER_ID}.json"
    return EditionAvailabilityLedger.model_validate_json(path.read_text(encoding="utf-8"))


def _fact_map(record: BenchmarkRecord) -> dict[str, str]:
    expectation = record.tool_expectations[0]
    facts = dict(fact.split("=", maxsplit=1) for fact in expectation.expected_facts)
    assert len(facts) == len(expectation.expected_facts)
    return facts


def test_frozen_matrix_has_40_balanced_records_and_validates_initial_batch() -> None:
    matrix = _matrix()
    records = _records()

    matrix.validate_initial_batch("core-batch-001", records)

    assert len(matrix.pairs) * 2 == matrix.target_record_count == 40
    assert Counter(pair.expected_route for pair in matrix.pairs) == Counter(
        {route: 5 for route in EvidenceRoute}
    )
    assert Counter(record.language.value for record in records) == {"ko": 2, "en": 2}
    assert all(record.annotation.status is AnnotationStatus.DRAFT for record in records)


def test_first_batch_forms_a_real_bundle_and_reproduces_cli_gold() -> None:
    records = _records()
    ledger = _ledger()
    cli_manifest = _manifest(CLI_SOURCE_ID)
    evidence_manifests = (
        _manifest(AVAILABILITY_SOURCE_ID),
        _manifest(CONTENT_SOURCE_ID),
    )
    catalog = RightsCatalog.model_validate_json(
        (ROOT / "data" / "rights" / "kor-rtd-rights-2026-07-17.json").read_text(encoding="utf-8")
    )

    BenchmarkBundle(
        sources=(cli_manifest, *evidence_manifests),
        records=records,
        availability_ledgers=(ledger,),
        rights_catalogs=(catalog,),
    )

    archive = (
        ROOT
        / "data"
        / "archive"
        / "oecd-stes"
        / "oecd-stes-cli-kor-li-aa-20260717t115302688498z.csv"
    ).read_bytes()
    data_records = tuple(
        record for record in records if record.expected_route is EvidenceRoute.DATA
    )
    for record in data_records:
        arguments = record.tool_expectations[0].arguments
        resolution = resolve_stes_as_of(
            archive_bytes=archive,
            manifest=cli_manifest,
            ledger=ledger,
            query=AsOfQuery(
                as_of=record.as_of,
                series=StesSeriesKey(
                    ref_area=arguments["ref_area"],
                    freq=arguments["freq"],
                    measure=arguments["measure"],
                    unit_measure=arguments["unit_measure"],
                    activity=arguments["activity"],
                ),
                period=arguments["period"],
            ),
        )
        assert resolution.abstention is None
        assert resolution.evidence is not None
        facts = _fact_map(record)
        assert resolution.evidence.observation.edition == facts["selected_edition"]
        assert resolution.evidence.observation.observation_value == facts["raw_value"]

        rule = normalization_rule(
            SourceSystem.OECD,
            "DSD_STES_REVISIONS@DF_STES_REVISIONS",
            "KOR.M.LI_AA.IX._T",
        )
        normalized = normalize_source_value(
            rule,
            resolution.evidence.observation.observation_value,
        )
        assert normalized.exact_value == Decimal(facts["normalized_value"])
        assert normalized.unit is NormalizedUnit.OECD_AMPLITUDE_ADJUSTED_INDEX
        assert normalized.unit.value == facts["canonical_unit"]
        assert format_display(normalized.exact_value, places=2) == facts["normalized_value"]

    abstain_records = tuple(
        record for record in records if record.expected_route is EvidenceRoute.ABSTAIN
    )
    for record in abstain_records:
        selection = ledger.select_edition(ledger.cutoff_exclusive(record.as_of))
        assert selection.selected_edition is None
        assert selection.abstention is EditionAbstentionReason.NO_EDITION_DEFINITELY_AVAILABLE


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("same-record-id", "must differ"),
        ("bad-suffix", "must end"),
        ("duplicate-document-unit", "document unit IDs must be unique"),
        ("duplicate-data-unit", "data unit IDs must be unique"),
        ("overlapping-units", "must not overlap"),
        ("wrong-route-shape", "inconsistent evidence units"),
    ],
)
def test_authoring_pair_rejects_ambiguous_shapes(mutation: str, message: str) -> None:
    payload = {
        "pair_id": "pair-example-01",
        "split": "train",
        "expected_route": "documents_and_data",
        "evidence_group_id": "evidence-example-01",
        "document_unit_ids": ["document-unit-01"],
        "data_unit_ids": ["data-unit-01"],
        "ko_record_id": "record-example-01-ko",
        "en_record_id": "record-example-01-en",
        "question_intent": "Exercise the authoring-pair contract.",
    }
    if mutation == "same-record-id":
        payload["en_record_id"] = payload["ko_record_id"]
    elif mutation == "bad-suffix":
        payload["en_record_id"] = "record-example-01-english"
    elif mutation == "duplicate-document-unit":
        payload["document_unit_ids"] = ["document-unit-01", "document-unit-01"]
    elif mutation == "duplicate-data-unit":
        payload["data_unit_ids"] = ["data-unit-01", "data-unit-01"]
    elif mutation == "overlapping-units":
        payload["data_unit_ids"] = ["document-unit-01"]
    else:
        payload["expected_route"] = "documents"

    with pytest.raises(ValidationError, match=message):
        CoreAuthoringPair.model_validate(payload)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("pair-id", "duplicate pair_id"),
        ("evidence-group", "duplicate evidence_group_id"),
        ("record-id", "duplicate record_id"),
        ("route-count", "five bilingual pairs per route"),
        ("split-count", "three train, one dev, and one test"),
        ("source-split", "crosses dataset splits"),
    ],
)
def test_authoring_matrix_rejects_balance_or_split_leakage(
    mutation: str,
    message: str,
) -> None:
    payload = _matrix_payload()
    pairs = payload["pairs"]
    if mutation == "pair-id":
        pairs[1]["pair_id"] = pairs[0]["pair_id"]
    elif mutation == "evidence-group":
        pairs[1]["evidence_group_id"] = pairs[0]["evidence_group_id"]
    elif mutation == "record-id":
        pairs[1]["ko_record_id"] = pairs[0]["ko_record_id"]
    elif mutation == "route-count":
        pairs[-1]["expected_route"] = "data"
        pairs[-1]["data_unit_ids"] = ["new-test-data-unit"]
    elif mutation == "split-count":
        pairs[-4]["split"] = "dev"
    else:
        pairs[9]["data_unit_ids"] = ["oecd-stes-edition-202607"]

    with pytest.raises(ValidationError, match=message):
        CoreAuthoringMatrix.model_validate(payload)


def test_initial_batch_rejects_unknown_duplicate_or_mismatched_records() -> None:
    matrix = _matrix()
    records = _records()

    with pytest.raises(ValueError, match="unknown or empty"):
        matrix.validate_initial_batch("unknown-batch", records)
    with pytest.raises(ValueError, match="duplicate batch record_id"):
        matrix.validate_initial_batch("core-batch-001", (*records, records[0]))
    with pytest.raises(ValueError, match="batch membership differs"):
        matrix.validate_initial_batch("core-batch-001", records[:-1])
    unexpected = records[0].model_copy(update={"record_id": "unexpected-record-en"})
    with pytest.raises(ValueError, match="batch membership differs"):
        matrix.validate_initial_batch("core-batch-001", (*records, unexpected))

    wrong_split = records[0].model_copy(update={"split": BenchmarkSplit.DEVELOPMENT})
    with pytest.raises(ValueError, match="does not match"):
        matrix.validate_initial_batch("core-batch-001", (wrong_split, *records[1:]))

    reviewed_annotation = records[0].annotation.model_copy(
        update={"status": AnnotationStatus.APPROVED}
    )
    reviewed = records[0].model_copy(update={"annotation": reviewed_annotation})
    with pytest.raises(ValueError, match="must remain draft"):
        matrix.validate_initial_batch("core-batch-001", (reviewed, *records[1:]))
