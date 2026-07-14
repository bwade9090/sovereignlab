"""Cross-record integrity checks that JSON Schema alone cannot express."""

from typing import Literal

from pydantic import model_validator

from sovereignlab.schemas.benchmark import BenchmarkRecord, BenchmarkSplit
from sovereignlab.schemas.common import SCHEMA_VERSION, StrictModel
from sovereignlab.schemas.source import SourceKind, SourceManifest


class BenchmarkBundle(StrictModel):
    """Validate source references, source kinds, cutoffs, and split isolation."""

    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    sources: tuple[SourceManifest, ...]
    records: tuple[BenchmarkRecord, ...]

    @model_validator(mode="after")
    def enforce_bundle_integrity(self) -> "BenchmarkBundle":
        source_by_id = _unique_by_id(self.sources, "source_id")
        _unique_by_id(self.records, "record_id")

        evidence_splits: dict[str, BenchmarkSplit] = {}
        parallel_splits: dict[str, BenchmarkSplit] = {}

        for record in self.records:
            _claim_group_split(evidence_splits, record.evidence_group_id, record.split, "evidence")
            if record.parallel_group_id is not None:
                _claim_group_split(
                    parallel_splits,
                    record.parallel_group_id,
                    record.split,
                    "parallel",
                )

            for evidence in record.document_evidence:
                source = _referenced_source(source_by_id, evidence.source_id, record.record_id)
                if source.source_kind is not SourceKind.DOCUMENT:
                    raise ValueError(
                        f"record {record.record_id} document evidence references "
                        f"non-document source {source.source_id}"
                    )
                if record.as_of is not None and source.published_on > record.as_of:
                    raise ValueError(
                        f"record {record.record_id} includes post-cutoff source {source.source_id}"
                    )

            for expectation in record.tool_expectations:
                source = _referenced_source(source_by_id, expectation.source_id, record.record_id)
                if source.source_kind not in {SourceKind.API, SourceKind.DATASET}:
                    raise ValueError(
                        f"record {record.record_id} tool expectation references "
                        f"non-data source {source.source_id}"
                    )
                if record.as_of is not None and source.published_on > record.as_of:
                    raise ValueError(
                        f"record {record.record_id} includes post-cutoff source {source.source_id}"
                    )
        return self


def _unique_by_id[IndexedModel](
    items: tuple[IndexedModel, ...], attribute: str
) -> dict[str, IndexedModel]:
    indexed: dict[str, IndexedModel] = {}
    for item in items:
        item_id = getattr(item, attribute)
        if item_id in indexed:
            raise ValueError(f"duplicate {attribute}: {item_id}")
        indexed[item_id] = item
    return indexed


def _referenced_source(
    source_by_id: dict[str, SourceManifest], source_id: str, record_id: str
) -> SourceManifest:
    source = source_by_id.get(source_id)
    if source is None:
        raise ValueError(f"record {record_id} references unknown source {source_id}")
    return source


def _claim_group_split(
    claimed: dict[str, BenchmarkSplit],
    group_id: str,
    split: BenchmarkSplit,
    group_kind: str,
) -> None:
    existing = claimed.setdefault(group_id, split)
    if existing is not split:
        raise ValueError(f"{group_kind} group {group_id} crosses dataset splits")
