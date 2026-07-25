"""Frozen structural plan for the 40-record human-reviewed K-VINTAGE core."""

from collections import Counter
from datetime import date
from typing import Literal

from pydantic import Field, model_validator

from sovereignlab.schemas.benchmark import (
    BenchmarkRecord,
    BenchmarkSplit,
    EvidenceRoute,
)
from sovereignlab.schemas.common import Identifier, NonEmptyText, StrictModel
from sovereignlab.schemas.source import LanguageCode


class CoreAuthoringPair(StrictModel):
    """One Korean/English pair reserved for a single evidence unit and split."""

    pair_id: Identifier
    split: BenchmarkSplit
    expected_route: EvidenceRoute
    evidence_group_id: Identifier
    document_unit_ids: tuple[Identifier, ...] = ()
    data_unit_ids: tuple[Identifier, ...] = ()
    ko_record_id: Identifier
    en_record_id: Identifier
    question_intent: NonEmptyText
    initial_batch_id: Identifier | None = None

    @model_validator(mode="after")
    def enforce_pair_shape(self) -> "CoreAuthoringPair":
        if self.ko_record_id == self.en_record_id:
            raise ValueError("Korean and English record IDs must differ")
        if not self.ko_record_id.endswith("-ko") or not self.en_record_id.endswith("-en"):
            raise ValueError("paired record IDs must end in -ko and -en")
        if len(set(self.document_unit_ids)) != len(self.document_unit_ids):
            raise ValueError("document unit IDs must be unique within a pair")
        if len(set(self.data_unit_ids)) != len(self.data_unit_ids):
            raise ValueError("data unit IDs must be unique within a pair")
        if set(self.document_unit_ids) & set(self.data_unit_ids):
            raise ValueError("document and data unit IDs must not overlap")

        expected_inputs = {
            EvidenceRoute.DOCUMENTS: (True, False),
            EvidenceRoute.DATA: (False, True),
            EvidenceRoute.DOCUMENTS_AND_DATA: (True, True),
            EvidenceRoute.ABSTAIN: (False, False),
        }
        if (bool(self.document_unit_ids), bool(self.data_unit_ids)) != expected_inputs[
            self.expected_route
        ]:
            raise ValueError(
                f"{self.expected_route.value} authoring pair has inconsistent evidence units"
            )
        return self


class CoreAuthoringMatrix(StrictModel):
    """The immutable 20-pair allocation that expands to the 40-record core."""

    schema_version: Literal["1.0.0"] = "1.0.0"
    matrix_id: Identifier
    frozen_on: date
    target_record_count: Literal[40] = 40
    pairs: tuple[CoreAuthoringPair, ...] = Field(min_length=20, max_length=20)

    @model_validator(mode="after")
    def enforce_frozen_balance_and_splits(self) -> "CoreAuthoringMatrix":
        pair_ids = [pair.pair_id for pair in self.pairs]
        evidence_group_ids = [pair.evidence_group_id for pair in self.pairs]
        record_ids = [
            record_id for pair in self.pairs for record_id in (pair.ko_record_id, pair.en_record_id)
        ]
        _require_unique(pair_ids, "pair_id")
        _require_unique(evidence_group_ids, "evidence_group_id")
        _require_unique(record_ids, "record_id")

        route_counts = Counter(pair.expected_route for pair in self.pairs)
        if route_counts != Counter({route: 5 for route in EvidenceRoute}):
            raise ValueError("core matrix requires exactly five bilingual pairs per route")

        expected_split_counts = Counter(
            {
                BenchmarkSplit.TRAIN: 3,
                BenchmarkSplit.DEVELOPMENT: 1,
                BenchmarkSplit.TEST: 1,
            }
        )
        for route in EvidenceRoute:
            split_counts = Counter(
                pair.split for pair in self.pairs if pair.expected_route is route
            )
            if split_counts != expected_split_counts:
                raise ValueError(
                    f"{route.value} route requires three train, one dev, and one test pair"
                )

        unit_splits: dict[str, BenchmarkSplit] = {}
        for pair in self.pairs:
            for unit_id in (*pair.document_unit_ids, *pair.data_unit_ids):
                existing = unit_splits.setdefault(unit_id, pair.split)
                if existing is not pair.split:
                    raise ValueError(f"source unit {unit_id} crosses dataset splits")
        return self

    def validate_initial_batch(
        self,
        batch_id: str,
        records: tuple[BenchmarkRecord, ...],
    ) -> None:
        """Validate a draft batch against its frozen bilingual pair allocation."""

        selected_pairs = tuple(pair for pair in self.pairs if pair.initial_batch_id == batch_id)
        if not selected_pairs:
            raise ValueError(f"unknown or empty initial batch: {batch_id}")

        expected: dict[str, tuple[CoreAuthoringPair, LanguageCode]] = {}
        for pair in selected_pairs:
            expected[pair.ko_record_id] = (pair, LanguageCode.KOREAN)
            expected[pair.en_record_id] = (pair, LanguageCode.ENGLISH)

        record_by_id: dict[str, BenchmarkRecord] = {}
        for record in records:
            if record.record_id in record_by_id:
                raise ValueError(f"duplicate batch record_id: {record.record_id}")
            record_by_id[record.record_id] = record

        missing = sorted(set(expected) - set(record_by_id))
        unexpected = sorted(set(record_by_id) - set(expected))
        if missing or unexpected:
            raise ValueError(
                f"batch membership differs from matrix; missing={missing}, unexpected={unexpected}"
            )

        for record_id, (pair, language) in expected.items():
            record = record_by_id[record_id]
            if (
                record.split is not pair.split
                or record.expected_route is not pair.expected_route
                or record.evidence_group_id != pair.evidence_group_id
                or record.parallel_group_id != pair.pair_id
                or record.language is not language
            ):
                raise ValueError(f"batch record {record_id} does not match its frozen matrix pair")


def _require_unique(values: list[str], field_name: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"core matrix contains duplicate {field_name}")
