"""Validation rules of the frozen core authoring matrix."""

import json
from collections import Counter
from pathlib import Path

import pytest
from pydantic import ValidationError

from sovereignlab.schemas import (
    BenchmarkRecord,
    BenchmarkSplit,
    CoreAuthoringMatrix,
    CoreAuthoringPair,
    EvidenceRoute,
)

ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "data" / "benchmark" / "core-authoring-matrix-v1.json"
BATCH_PATH = ROOT / "data" / "benchmark" / "core" / "core-batch-001.jsonl"


def _matrix() -> CoreAuthoringMatrix:
    return CoreAuthoringMatrix.model_validate_json(MATRIX_PATH.read_text(encoding="utf-8"))


def _first_batch() -> tuple[BenchmarkRecord, ...]:
    return tuple(
        BenchmarkRecord.model_validate_json(line)
        for line in BATCH_PATH.read_text(encoding="utf-8").splitlines()
        if line
    )


def test_committed_matrix_allocates_forty_records_evenly() -> None:
    matrix = _matrix()

    assert len(matrix.pairs) * 2 == matrix.target_record_count == 40
    assert Counter(pair.expected_route for pair in matrix.pairs) == Counter(
        {route: 5 for route in EvidenceRoute}
    )
    matrix.validate_initial_batch("core-batch-001", _first_batch())


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
def test_authoring_matrix_rejects_balance_or_split_leakage(mutation: str, message: str) -> None:
    payload = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
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
    records = _first_batch()

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
