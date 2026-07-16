"""Cross-record integrity checks that JSON Schema alone cannot express."""

from datetime import datetime, time, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import model_validator

from sovereignlab.schemas.availability import EditionAvailabilityLedger
from sovereignlab.schemas.benchmark import BenchmarkRecord, BenchmarkSplit, ToolExpectation
from sovereignlab.schemas.common import EVIDENCE_SCHEMA_VERSION, StrictModel
from sovereignlab.schemas.rights import RightsCatalog, SeriesRightsDecision
from sovereignlab.schemas.source import (
    RedistributionStatus,
    SourceKind,
    SourceManifest,
    VintageSemantics,
)

BENCHMARK_CUTOFF_TIMEZONE = "Asia/Seoul"


class BenchmarkBundle(StrictModel):
    """Validate references, source kinds, cutoffs, vintages, rights links, and splits."""

    schema_version: Literal["2.0.0"] = EVIDENCE_SCHEMA_VERSION
    sources: tuple[SourceManifest, ...]
    records: tuple[BenchmarkRecord, ...]
    availability_ledgers: tuple[EditionAvailabilityLedger, ...] = ()
    rights_catalogs: tuple[RightsCatalog, ...] = ()

    @model_validator(mode="after")
    def enforce_bundle_integrity(self) -> "BenchmarkBundle":
        source_by_id = _unique_by_id(self.sources, "source_id")
        _unique_by_id(self.records, "record_id")
        ledger_by_id = _unique_by_id(self.availability_ledgers, "ledger_id")
        catalog_by_id = _unique_by_id(self.rights_catalogs, "catalog_id")
        superseded_ledger_ids = {
            ledger.supersedes_ledger_id
            for ledger in self.availability_ledgers
            if ledger.supersedes_ledger_id is not None
        }
        superseded_catalog_ids = {
            catalog.supersedes_catalog_id
            for catalog in self.rights_catalogs
            if catalog.supersedes_catalog_id is not None
        }
        _require_one_active_catalog_per_scope(self.rights_catalogs, superseded_catalog_ids)

        for ledger in self.availability_ledgers:
            _require_offline_checkable_evidence(ledger, source_by_id)

        for source in self.sources:
            _validate_rights_link(source, catalog_by_id, superseded_catalog_ids)

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
                if source.vintage_semantics is VintageSemantics.HISTORICAL_ARCHIVE:
                    _validate_archive_vintage(
                        record, expectation, source, ledger_by_id, superseded_ledger_ids
                    )
                else:
                    if expectation.vintage is not None:
                        raise ValueError(
                            f"record {record.record_id} vintage evidence requires a "
                            f"historical-archive source, not {source.source_id}"
                        )
                    if record.as_of is not None and source.published_on > record.as_of:
                        raise ValueError(
                            f"record {record.record_id} includes post-cutoff source "
                            f"{source.source_id}"
                        )
        return self


def _validate_archive_vintage(
    record: BenchmarkRecord,
    expectation: ToolExpectation,
    source: SourceManifest,
    ledger_by_id: dict[str, EditionAvailabilityLedger],
    superseded_ledger_ids: set[str],
) -> None:
    if record.as_of is None:
        raise ValueError(
            f"record {record.record_id} uses historical-archive source "
            f"{source.source_id} without as_of"
        )
    vintage = expectation.vintage
    if vintage is None:
        raise ValueError(
            f"record {record.record_id} uses historical-archive source "
            f"{source.source_id} without vintage evidence"
        )
    ledger = ledger_by_id.get(vintage.ledger_id)
    if ledger is None:
        raise ValueError(
            f"record {record.record_id} references unknown availability ledger {vintage.ledger_id}"
        )
    if vintage.ledger_id in superseded_ledger_ids:
        raise ValueError(
            f"record {record.record_id} references superseded availability ledger "
            f"{vintage.ledger_id}"
        )
    if ledger.cutoff_timezone != BENCHMARK_CUTOFF_TIMEZONE:
        raise ValueError(
            f"record {record.record_id} vintage resolution requires an "
            f"{BENCHMARK_CUTOFF_TIMEZONE} end-of-day ledger"
        )
    selection = ledger.select_edition(ledger.cutoff_exclusive(record.as_of))
    if selection.abstention is not None:
        raise ValueError(
            f"record {record.record_id} asserts a vintage its ledger cannot resolve "
            f"({selection.abstention.value})"
        )
    if selection.selected_edition != vintage.selected_edition:
        raise ValueError(
            f"record {record.record_id} vintage does not match the ledger-resolved edition"
        )


def _require_offline_checkable_evidence(
    ledger: EditionAvailabilityLedger,
    source_by_id: dict[str, SourceManifest],
) -> None:
    for edition_record in ledger.editions:
        for evidence in edition_record.evidence:
            for manifest_id in evidence.source_manifest_ids:
                if manifest_id not in source_by_id:
                    raise ValueError(
                        f"ledger {ledger.ledger_id} availability evidence references "
                        f"unknown source {manifest_id}"
                    )


def _require_one_active_catalog_per_scope(
    catalogs: tuple[RightsCatalog, ...],
    superseded_catalog_ids: set[str],
) -> None:
    active_scope_catalogs: dict[tuple[str, str, str, str], str] = {}
    for catalog in catalogs:
        if catalog.catalog_id in superseded_catalog_ids:
            continue
        for decision in catalog.decisions:
            existing = active_scope_catalogs.setdefault(decision.scope, catalog.catalog_id)
            if existing != catalog.catalog_id:
                raise ValueError(
                    f"series scope {decision.scope!r} has decisions in multiple active "
                    f"catalogs: {existing}, {catalog.catalog_id}"
                )


def _validate_rights_link(
    source: SourceManifest,
    catalog_by_id: dict[str, RightsCatalog],
    superseded_catalog_ids: set[str],
) -> None:
    reference = source.rights_decision
    if reference is None:
        return
    catalog = catalog_by_id.get(reference.catalog_id)
    if catalog is None:
        raise ValueError(
            f"source {source.source_id} references unknown rights catalog {reference.catalog_id}"
        )
    if reference.catalog_id in superseded_catalog_ids:
        raise ValueError(
            f"source {source.source_id} references superseded rights catalog {reference.catalog_id}"
        )
    decision = _decision_in_catalog(catalog, reference.decision_id)
    if decision is None:
        raise ValueError(
            f"source {source.source_id} references unknown rights decision {reference.decision_id}"
        )
    if (
        decision.publisher != source.publisher
        or decision.source_system is not reference.source_system
        or decision.table_id != reference.table_id
        or decision.item_id != reference.item_id
    ):
        raise ValueError(
            f"source {source.source_id} rights decision scope does not match "
            f"{reference.decision_id}"
        )
    if source.redistribution.status is RedistributionStatus.ALLOWED:
        if decision.decision_state is not RedistributionStatus.ALLOWED:
            raise ValueError(
                f"source {source.source_id} allowed redistribution requires an allowed "
                "rights decision"
            )
        if decision.valid_until is not None:
            try:
                first_expired_day = decision.valid_until + timedelta(days=1)
            except OverflowError as error:
                raise ValueError(
                    f"source {source.source_id} rights decision valid_until is out of the "
                    "supported range"
                ) from error
            expiry_exclusive = datetime.combine(
                first_expired_day, time.min, tzinfo=ZoneInfo(BENCHMARK_CUTOFF_TIMEZONE)
            )
            if source.retrieved_at >= expiry_exclusive:
                raise ValueError(
                    f"source {source.source_id} rights decision expired before retrieval"
                )


def _decision_in_catalog(catalog: RightsCatalog, decision_id: str) -> SeriesRightsDecision | None:
    for decision in catalog.decisions:
        if decision.decision_id == decision_id:
            return decision
    return None


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
