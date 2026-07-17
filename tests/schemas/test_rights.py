"""Fail-closed tests for source-specific rights instruments and series rulings."""

from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from sovereignlab.schemas import (
    AttributionField,
    AttributionRequirement,
    ContentClass,
    EvidenceClaim,
    EvidenceObservation,
    KosisContentCategory,
    OperationRule,
    OperationStatus,
    ProducerMappingBasis,
    ProjectUseProfile,
    RedistributionStatus,
    RightsCatalog,
    RightsEvidence,
    RightsEvidenceKind,
    RightsInstrument,
    RightsOperation,
    SeriesRightsDecision,
    SourceSystem,
    ThirdPartyStatus,
)

CATALOG_RECORDED_AT = datetime(2026, 7, 16, 9, 0, tzinfo=UTC)
COMMON_ATTRIBUTION = (
    AttributionField.PUBLISHER,
    AttributionField.ORIGINAL_PRODUCER,
    AttributionField.STATISTIC_NAME,
    AttributionField.RETRIEVAL_DATE,
    AttributionField.SOURCE_URL,
)
KOSIS_DETAIL_ATTRIBUTION = (
    AttributionField.SURVEY_NAME,
    AttributionField.TABLE_NAME,
    AttributionField.AUTHORING_DATE,
    AttributionField.REFERENCE_DATE,
)


def test_rights_catalog_accepts_complete_allowed_ruling(rights_catalog: RightsCatalog) -> None:
    decision = rights_catalog.decisions[0]

    assert rights_catalog.schema_version == "1.0.0"
    assert rights_catalog.instruments[0].schema_version == "1.0.0"
    assert rights_catalog.instruments[0].verification_capture is not None
    assert decision.schema_version == "1.0.0"
    assert decision.scope == (
        "Example Public Institution",
        "other_official",
        "TABLE_001",
        "ITEM_001",
    )


def test_rights_instrument_rejects_undeclared_fields(
    rights_instrument: RightsInstrument,
) -> None:
    payload = rights_instrument.model_dump(mode="python")
    payload["cached_terms"] = "not part of the public contract"

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        RightsInstrument.model_validate(payload)


def test_nonpermitted_operation_rule_requires_notes() -> None:
    with pytest.raises(ValidationError, match="requires notes"):
        OperationRule(
            operation=RightsOperation.REDISTRIBUTE,
            status=OperationStatus.NOT_EXPRESSLY_GRANTED,
        )


@pytest.mark.parametrize(
    ("claims", "observed", "message"),
    [
        ((EvidenceClaim.SERIES_SCOPE,), None, "structured observations"),
        (
            (EvidenceClaim.SERIES_SCOPE,),
            EvidenceObservation(source_system=SourceSystem.ECOS, table_id="TABLE_001"),
            "table ID, and item ID",
        ),
        ((EvidenceClaim.ORIGINAL_PRODUCER,), EvidenceObservation(), "original_producer"),
        ((EvidenceClaim.TITLE_FREQUENCY,), EvidenceObservation(), "title and frequency"),
        ((EvidenceClaim.CONTENT_CATEGORY,), EvidenceObservation(), "KOSIS category"),
    ],
)
def test_evidence_claims_require_matching_observations(
    claims: tuple[EvidenceClaim, ...],
    observed: EvidenceObservation | None,
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        RightsEvidence(
            kind=RightsEvidenceKind.SOURCE_METADATA,
            official_url="https://example.org/evidence",
            accessed_on=date(2026, 7, 16),
            claims=claims,
            assertion="Synthetic assertion.",
            observed=observed,
        )


def test_evidence_claims_must_be_unique() -> None:
    with pytest.raises(ValidationError, match="evidence claims must contain unique"):
        RightsEvidence(
            kind=RightsEvidenceKind.PUBLISHER_USE_GUIDE,
            official_url="https://example.org/rights",
            accessed_on=date(2026, 7, 16),
            claims=(EvidenceClaim.RIGHTS_TERMS, EvidenceClaim.RIGHTS_TERMS),
            assertion="Synthetic terms.",
        )


@pytest.mark.parametrize(
    ("fields", "template", "message"),
    [
        (
            (AttributionField.PUBLISHER, AttributionField.PUBLISHER),
            "{publisher}",
            "attribution fields must contain unique",
        ),
        ((AttributionField.PUBLISHER,), "{publisher", "not valid format syntax"),
        ((AttributionField.PUBLISHER,), "{publisher.name}", "plain field names"),
        ((AttributionField.PUBLISHER,), "{publisher} {publisher}", "placeholders.*unique"),
        ((AttributionField.PUBLISHER,), "{source_url}", "exactly match"),
    ],
)
def test_attribution_template_is_exactly_typed(
    fields: tuple[AttributionField, ...],
    template: str,
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        AttributionRequirement(fields=fields, template=template)


def test_attribution_template_may_contain_escaped_literal_braces() -> None:
    requirement = AttributionRequirement(
        fields=(AttributionField.PUBLISHER,),
        template="{{literal}} {publisher}",
    )

    assert requirement.fields == (AttributionField.PUBLISHER,)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ({"applicable_source_systems": (SourceSystem.ECOS, SourceSystem.ECOS)}, "must contain"),
        (
            {"applicable_content_classes": (ContentClass.OTHER_OFFICIAL_DATA,) * 2},
            "must contain",
        ),
        (
            {
                "applicable_source_systems": (SourceSystem.ECOS,),
                "applicable_content_classes": (ContentClass.OTHER_OFFICIAL_DATA,),
            },
            "outside its source-system scope",
        ),
    ],
)
def test_instrument_scope_is_typed_and_unique(
    rights_instrument: RightsInstrument,
    mutation: dict[str, object],
    message: str,
) -> None:
    payload = rights_instrument.model_dump(mode="python")
    payload.update(mutation)

    with pytest.raises(ValidationError, match=message):
        RightsInstrument.model_validate(payload)


@pytest.mark.parametrize(
    ("field_name", "field_value", "message"),
    [
        ("claims", (EvidenceClaim.SERIES_SCOPE,), "must claim rights terms"),
        ("kind", RightsEvidenceKind.SOURCE_METADATA, "invalid evidence kind"),
        ("official_url", "https://example.org/other", "URL must match"),
        ("accessed_on", date(2026, 7, 15), "access date must match"),
        ("assertion", "Different terms.", "assertion must match"),
    ],
)
def test_instrument_terms_evidence_must_match_capture(
    rights_instrument: RightsInstrument,
    field_name: str,
    field_value: object,
    message: str,
) -> None:
    payload = rights_instrument.model_dump(mode="python")
    payload["terms_evidence"][field_name] = field_value
    if field_name == "claims":
        payload["terms_evidence"]["observed"] = _scope_observation(
            _base_decision_payload(), SourceSystem.OTHER_OFFICIAL
        )

    with pytest.raises(ValidationError, match=message):
        RightsInstrument.model_validate(payload)


@pytest.mark.parametrize(
    ("field_name", "field_value", "message"),
    [
        ("source_system", SourceSystem.ECOS, "does not match source system"),
        (
            "kosis_content_category",
            KosisContentCategory.DOMESTIC_STATISTICS,
            "exact KOSIS content category",
        ),
    ],
)
def test_content_class_requires_exact_source_and_category(
    series_rights_decision: SeriesRightsDecision,
    field_name: str,
    field_value: object,
    message: str,
) -> None:
    payload = _decision_payload(series_rights_decision)
    payload[field_name] = field_value

    with pytest.raises(ValidationError, match=message):
        SeriesRightsDecision.model_validate(payload)


def test_decision_requires_producer_or_kosis_category(
    series_rights_decision: SeriesRightsDecision,
) -> None:
    payload = _decision_payload(series_rights_decision)
    payload.update(original_producer=None, kosis_content_category=None)

    with pytest.raises(ValidationError, match="producer or KOSIS content category"):
        SeriesRightsDecision.model_validate(payload)


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("original_producer", "다른기관"),
        ("third_party_status", ThirdPartyStatus.THIRD_PARTY),
    ],
)
def test_ecos_bok_requires_bok_first_party(
    series_rights_decision: SeriesRightsDecision,
    field_name: str,
    field_value: object,
) -> None:
    payload = _ecos_payload(series_rights_decision, ContentClass.ECOS_BOK_AUTHORED)
    payload[field_name] = field_value

    with pytest.raises(ValidationError, match="한국은행 as first-party"):
        SeriesRightsDecision.model_validate(payload)


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [("original_producer", None), ("third_party_status", ThirdPartyStatus.FIRST_PARTY)],
)
def test_ecos_other_requires_named_third_party(
    series_rights_decision: SeriesRightsDecision,
    field_name: str,
    field_value: object,
) -> None:
    payload = _ecos_payload(series_rights_decision, ContentClass.ECOS_OTHER_AUTHORED)
    payload[field_name] = field_value

    with pytest.raises(ValidationError, match="named third-party producer"):
        SeriesRightsDecision.model_validate(payload)


@pytest.mark.parametrize(
    ("third_party_status", "publisher", "message"),
    [
        (ThirdPartyStatus.FIRST_PARTY, "Different Publisher", "publisher to equal producer"),
        (
            ThirdPartyStatus.THIRD_PARTY,
            "Example Public Institution",
            "publisher and producer to differ",
        ),
    ],
)
def test_party_status_matches_publisher_and_producer(
    series_rights_decision: SeriesRightsDecision,
    third_party_status: ThirdPartyStatus,
    publisher: str,
    message: str,
) -> None:
    payload = _decision_payload(series_rights_decision)
    payload.update(third_party_status=third_party_status, publisher=publisher)

    with pytest.raises(ValidationError, match=message):
        SeriesRightsDecision.model_validate(payload)


@pytest.mark.parametrize("field_name", ["operation_rules", "intended_operations", "evidence"])
def test_decision_rejects_duplicate_values(
    series_rights_decision: SeriesRightsDecision,
    field_name: str,
) -> None:
    payload = _decision_payload(series_rights_decision)
    first = payload[field_name][0]
    payload[field_name] = (first, first)

    with pytest.raises(ValidationError, match="must contain unique values"):
        SeriesRightsDecision.model_validate(payload)


@pytest.mark.parametrize(
    ("observed_field", "observed_value"),
    [
        ("source_system", SourceSystem.ECOS),
        ("table_id", "WRONG_TABLE"),
        ("item_id", "WRONG_ITEM"),
        ("table_title", "Wrong table"),
        ("item_title", "Wrong item"),
        ("frequency", "quarterly"),
    ],
)
def test_direct_mapping_requires_exact_source_scope(
    series_rights_decision: SeriesRightsDecision,
    observed_field: str,
    observed_value: object,
) -> None:
    payload = _decision_payload(series_rights_decision)
    payload["evidence"][0]["observed"][observed_field] = observed_value

    with pytest.raises(ValidationError, match="exact source-scope"):
        SeriesRightsDecision.model_validate(payload)


@pytest.mark.parametrize(
    ("observed_field", "observed_value"),
    [("original_producer", "Wrong producer"), ("mapping_title", "Wrong title")],
)
def test_direct_mapping_requires_exact_producer_and_title(
    series_rights_decision: SeriesRightsDecision,
    observed_field: str,
    observed_value: str,
) -> None:
    payload = _decision_payload(series_rights_decision)
    payload["evidence"][0]["observed"][observed_field] = observed_value

    with pytest.raises(ValidationError, match="exact producer metadata"):
        SeriesRightsDecision.model_validate(payload)


def test_cross_mapping_requires_exact_source_scope(
    series_rights_decision: SeriesRightsDecision,
) -> None:
    payload = _cross_payload(series_rights_decision)
    payload["evidence"] = (payload["evidence"][1],)

    with pytest.raises(ValidationError, match="exact source-scope"):
        SeriesRightsDecision.model_validate(payload)


@pytest.mark.parametrize(
    ("observed_field", "observed_value"),
    [
        ("source_system", SourceSystem.OTHER_OFFICIAL),
        ("original_producer", "Wrong producer"),
        ("mapping_title", "Wrong title"),
        ("frequency", "quarterly"),
    ],
)
def test_cross_mapping_requires_true_cross_source_exact_mapping(
    series_rights_decision: SeriesRightsDecision,
    observed_field: str,
    observed_value: object,
) -> None:
    payload = _cross_payload(series_rights_decision)
    payload["evidence"][1]["observed"][observed_field] = observed_value

    with pytest.raises(ValidationError, match="exact official producer/title/frequency"):
        SeriesRightsDecision.model_validate(payload)


def test_cross_mapping_accepts_exact_official_mapping(
    series_rights_decision: SeriesRightsDecision,
) -> None:
    decision = SeriesRightsDecision.model_validate(_cross_payload(series_rights_decision))

    assert decision.producer_mapping_basis.value.startswith("owner_approved")


def test_cross_mapping_accepts_only_normalized_outline_prefix_difference(
    series_rights_decision: SeriesRightsDecision,
) -> None:
    payload = _cross_payload(series_rights_decision)
    payload["table_title"] = "2.1.2.2.2.  Synthetic  Statistics Table"
    payload["evidence"][0]["observed"]["table_title"] = payload["table_title"]

    assert SeriesRightsDecision.model_validate(payload).producer_mapping_title == (
        "Synthetic Statistics Table"
    )

    payload["producer_mapping_title"] = "Different title"
    payload["evidence"][1]["observed"]["mapping_title"] = "Different title"
    with pytest.raises(ValidationError, match="equivalent normalized"):
        SeriesRightsDecision.model_validate(payload)


def test_publisher_documentation_mapping_requires_scope_and_release(
    series_rights_decision: SeriesRightsDecision,
) -> None:
    payload = _decision_payload(series_rights_decision)
    payload["producer_mapping_basis"] = ProducerMappingBasis.OFFICIAL_PUBLISHER_DOCUMENTATION

    with pytest.raises(ValidationError, match="scope and producer evidence"):
        SeriesRightsDecision.model_validate(payload)


def test_publisher_documentation_mapping_accepts_exact_release(
    series_rights_decision: SeriesRightsDecision,
) -> None:
    payload = _decision_payload(series_rights_decision)
    payload["producer_mapping_basis"] = ProducerMappingBasis.OFFICIAL_PUBLISHER_DOCUMENTATION
    payload["evidence"] = (
        *payload["evidence"],
        _producer_evidence(payload, RightsEvidenceKind.OFFICIAL_PUBLISHER_RELEASE),
    )

    assert (
        SeriesRightsDecision.model_validate(payload).decision_state is RedistributionStatus.ALLOWED
    )


def test_kosis_decision_requires_exact_category_evidence(
    series_rights_decision: SeriesRightsDecision,
) -> None:
    payload = _kosis_payload(
        series_rights_decision,
        ContentClass.KOSIS_DOMESTIC_STATISTICS,
        KosisContentCategory.DOMESTIC_STATISTICS,
    )
    payload["evidence"][0]["claims"] = tuple(
        claim
        for claim in payload["evidence"][0]["claims"]
        if claim is not EvidenceClaim.CONTENT_CATEGORY
    )

    with pytest.raises(ValidationError, match="exact content-category evidence"):
        SeriesRightsDecision.model_validate(payload)


def test_kosis_category_evidence_must_be_source_metadata(
    series_rights_decision: SeriesRightsDecision,
) -> None:
    payload = _kosis_payload(
        series_rights_decision,
        ContentClass.KOSIS_DOMESTIC_STATISTICS,
        KosisContentCategory.DOMESTIC_STATISTICS,
    )
    payload["evidence"][0]["claims"] = tuple(
        claim
        for claim in payload["evidence"][0]["claims"]
        if claim is not EvidenceClaim.CONTENT_CATEGORY
    )
    category_evidence = _producer_evidence(
        payload,
        RightsEvidenceKind.OFFICIAL_CROSS_SOURCE_CATALOG,
    )
    category_evidence["claims"] = (*category_evidence["claims"], EvidenceClaim.CONTENT_CATEGORY)
    category_evidence["observed"]["kosis_content_category"] = (
        KosisContentCategory.DOMESTIC_STATISTICS
    )
    payload["evidence"] = (*payload["evidence"], category_evidence)

    with pytest.raises(ValidationError, match="exact content-category evidence"):
        SeriesRightsDecision.model_validate(payload)


@pytest.mark.parametrize(
    "missing_field",
    ["approved_by", "approval_recorded_at", "approval_record_reference"],
)
def test_approval_record_is_an_atomic_trio(
    series_rights_decision: SeriesRightsDecision,
    missing_field: str,
) -> None:
    payload = _decision_payload(series_rights_decision)
    payload[missing_field] = None

    with pytest.raises(ValidationError, match="complete trio"):
        SeriesRightsDecision.model_validate(payload)


def test_approval_record_reference_is_typed_repo_adr_locator(
    series_rights_decision: SeriesRightsDecision,
) -> None:
    payload = _decision_payload(series_rights_decision)
    payload["approval_record_reference"] = "docs/PROJECT_STATUS.md#approval-record"

    with pytest.raises(ValidationError, match="approval_record_reference"):
        SeriesRightsDecision.model_validate(payload)


def test_allowed_decision_requires_approval_record(
    series_rights_decision: SeriesRightsDecision,
) -> None:
    payload = _decision_payload(series_rights_decision)
    payload.update(
        approved_by=None,
        approval_recorded_at=None,
        approval_record_reference=None,
    )

    with pytest.raises(ValidationError, match="complete approval record"):
        SeriesRightsDecision.model_validate(payload)


def test_metadata_only_decision_may_be_unapproved(
    series_rights_decision: SeriesRightsDecision,
) -> None:
    payload = _decision_payload(series_rights_decision)
    payload.update(
        decision_state=RedistributionStatus.METADATA_ONLY,
        approved_by=None,
        approval_recorded_at=None,
        approval_record_reference=None,
    )

    assert SeriesRightsDecision.model_validate(payload).approved_by is None


def test_allowed_decision_requires_original_producer(
    series_rights_decision: SeriesRightsDecision,
) -> None:
    payload = _kosis_payload(
        series_rights_decision,
        ContentClass.KOSIS_DOMESTIC_STATISTICS,
        KosisContentCategory.DOMESTIC_STATISTICS,
    )
    payload["original_producer"] = None
    payload["producer_mapping_basis"] = ProducerMappingBasis.OFFICIAL_CONTENT_CATEGORY
    payload["third_party_status"] = ThirdPartyStatus.UNKNOWN

    with pytest.raises(ValidationError, match="requires an original producer"):
        SeriesRightsDecision.model_validate(payload)


@pytest.mark.parametrize(
    "basis",
    [ProducerMappingBasis.OFFICIAL_CONTENT_CATEGORY, ProducerMappingBasis.UNRESOLVED],
)
def test_allowed_decision_requires_resolved_producer_mapping(
    series_rights_decision: SeriesRightsDecision,
    basis: ProducerMappingBasis,
) -> None:
    payload = _decision_payload(series_rights_decision)
    payload["producer_mapping_basis"] = basis

    with pytest.raises(ValidationError, match="resolved producer mapping"):
        SeriesRightsDecision.model_validate(payload)


@pytest.mark.parametrize(
    "missing_operation",
    [
        RightsOperation.USE,
        RightsOperation.PROCESS,
        RightsOperation.REDISTRIBUTE,
        RightsOperation.NONCOMMERCIAL_USE,
    ],
)
def test_allowed_decision_requires_all_project_operations(
    series_rights_decision: SeriesRightsDecision,
    missing_operation: RightsOperation,
) -> None:
    payload = _decision_payload(series_rights_decision)
    payload["intended_operations"] = tuple(
        operation
        for operation in payload["intended_operations"]
        if operation is not missing_operation
    )

    with pytest.raises(ValidationError, match="missing required intended operations"):
        SeriesRightsDecision.model_validate(payload)


def test_oecd_data_requires_exact_first_party_classification(
    series_rights_decision: SeriesRightsDecision,
) -> None:
    payload = _other_source_payload(
        series_rights_decision,
        SourceSystem.OECD,
        ContentClass.OECD_DATA,
    )

    with pytest.raises(ValidationError, match="OECD as first-party producer"):
        SeriesRightsDecision.model_validate(payload)

    payload.update(
        publisher="OECD",
        original_producer="OECD",
        third_party_status=ThirdPartyStatus.FIRST_PARTY,
    )
    payload["evidence"] = (_scope_evidence(payload, SourceSystem.OECD),)

    assert SeriesRightsDecision.model_validate(payload).content_class is ContentClass.OECD_DATA


@pytest.mark.parametrize(
    ("content_class", "category"),
    [
        (
            ContentClass.KOSIS_INTERNATIONAL_STATISTICS,
            KosisContentCategory.INTERNATIONAL_STATISTICS,
        ),
        (
            ContentClass.KOSIS_NORTH_KOREA_STATISTICS,
            KosisContentCategory.NORTH_KOREA_STATISTICS,
        ),
    ],
)
def test_kosis_international_and_north_korea_cannot_be_raw_allowed(
    series_rights_decision: SeriesRightsDecision,
    content_class: ContentClass,
    category: KosisContentCategory,
) -> None:
    payload = _kosis_payload(series_rights_decision, content_class, category)

    with pytest.raises(ValidationError, match="cannot be redistributed"):
        SeriesRightsDecision.model_validate(payload)


def test_ecos_other_allowed_requires_producer_terms_evidence(
    series_rights_decision: SeriesRightsDecision,
) -> None:
    payload = _ecos_payload(series_rights_decision, ContentClass.ECOS_OTHER_AUTHORED)

    with pytest.raises(ValidationError, match="requires producer-specific terms"):
        SeriesRightsDecision.model_validate(payload)


def test_kosis_publication_allowed_requires_dataset_terms_evidence(
    series_rights_decision: SeriesRightsDecision,
) -> None:
    payload = _kosis_payload(
        series_rights_decision,
        ContentClass.KOSIS_PUBLICATION,
        KosisContentCategory.PUBLICATION,
    )

    with pytest.raises(ValidationError, match="requires dataset terms"):
        SeriesRightsDecision.model_validate(payload)


def test_allowed_operations_must_all_be_permitted(
    series_rights_decision: SeriesRightsDecision,
) -> None:
    payload = _decision_payload(series_rights_decision)
    _set_rule(payload, RightsOperation.REDISTRIBUTE, OperationStatus.NOT_EXPRESSLY_GRANTED)

    with pytest.raises(ValidationError, match="every intended operation"):
        SeriesRightsDecision.model_validate(payload)


def test_allowed_requires_distortion_prohibition(
    series_rights_decision: SeriesRightsDecision,
) -> None:
    payload = _decision_payload(series_rights_decision)
    _set_rule(payload, RightsOperation.DISTORT, OperationStatus.NOT_EXPRESSLY_GRANTED)

    with pytest.raises(ValidationError, match="distortion to be prohibited"):
        SeriesRightsDecision.model_validate(payload)


def test_allowed_requires_structured_attribution(
    series_rights_decision: SeriesRightsDecision,
) -> None:
    payload = _decision_payload(series_rights_decision)
    payload["attribution"] = None

    with pytest.raises(ValidationError, match="requires structured attribution"):
        SeriesRightsDecision.model_validate(payload)


def test_allowed_requires_common_attribution_fields(
    series_rights_decision: SeriesRightsDecision,
) -> None:
    payload = _decision_payload(series_rights_decision)
    payload["attribution"] = _attribution((AttributionField.PUBLISHER,))

    with pytest.raises(ValidationError, match="missing common attribution"):
        SeriesRightsDecision.model_validate(payload)


@pytest.mark.parametrize(
    "content_class",
    [ContentClass.KOSIS_DOMESTIC_STATISTICS, ContentClass.KOSIS_EASY_VIEW_STATISTICS],
)
def test_kosis_domestic_and_easy_require_prohibitions_and_detailed_attribution(
    series_rights_decision: SeriesRightsDecision,
    content_class: ContentClass,
) -> None:
    category = (
        KosisContentCategory.DOMESTIC_STATISTICS
        if content_class is ContentClass.KOSIS_DOMESTIC_STATISTICS
        else KosisContentCategory.EASY_VIEW_STATISTICS
    )
    payload = _kosis_payload(series_rights_decision, content_class, category)
    payload["operation_rules"] = tuple(
        rule
        for rule in payload["operation_rules"]
        if rule["operation"] is not RightsOperation.SELL_UNCHANGED
    )

    with pytest.raises(ValidationError, match="missing prohibited operations"):
        SeriesRightsDecision.model_validate(payload)

    payload = _kosis_payload(series_rights_decision, content_class, category)
    payload["attribution"] = _attribution(COMMON_ATTRIBUTION)
    with pytest.raises(ValidationError, match="detailed attribution"):
        SeriesRightsDecision.model_validate(payload)


def test_complete_kosis_domestic_decision_is_valid(
    series_rights_decision: SeriesRightsDecision,
) -> None:
    payload = _kosis_payload(
        series_rights_decision,
        ContentClass.KOSIS_DOMESTIC_STATISTICS,
        KosisContentCategory.DOMESTIC_STATISTICS,
    )

    assert SeriesRightsDecision.model_validate(payload).content_class is (
        ContentClass.KOSIS_DOMESTIC_STATISTICS
    )


def test_valid_until_cannot_precede_approval_record(
    series_rights_decision: SeriesRightsDecision,
) -> None:
    payload = _decision_payload(series_rights_decision)
    payload["valid_until"] = date(2026, 7, 15)

    with pytest.raises(ValidationError, match="cannot precede approval_recorded_at"):
        SeriesRightsDecision.model_validate(payload)


def test_external_series_identifiers_reject_spaces(
    series_rights_decision: SeriesRightsDecision,
) -> None:
    payload = _decision_payload(series_rights_decision)
    payload["table_id"] = "TABLE 001"

    with pytest.raises(ValidationError, match="table_id"):
        SeriesRightsDecision.model_validate(payload)


def test_catalog_cannot_supersede_itself(rights_catalog: RightsCatalog) -> None:
    payload = rights_catalog.model_dump(mode="python")
    payload["supersedes_catalog_id"] = rights_catalog.catalog_id

    with pytest.raises(ValidationError, match="cannot supersede itself"):
        RightsCatalog.model_validate(payload)


def test_catalog_rejects_duplicate_instrument_and_decision_ids(
    rights_instrument: RightsInstrument,
    series_rights_decision: SeriesRightsDecision,
) -> None:
    with pytest.raises(ValidationError, match="duplicate instrument_id"):
        _catalog((rights_instrument, rights_instrument), (series_rights_decision,))
    with pytest.raises(ValidationError, match="duplicate decision_id"):
        _catalog((rights_instrument,), (series_rights_decision, series_rights_decision))


def test_catalog_rejects_multiple_decisions_for_one_scope(
    rights_instrument: RightsInstrument,
    series_rights_decision: SeriesRightsDecision,
) -> None:
    payload = _decision_payload(series_rights_decision)
    payload["decision_id"] = "example-series-rights-002"
    second = SeriesRightsDecision.model_validate(payload)

    with pytest.raises(ValidationError, match="has multiple decisions"):
        _catalog((rights_instrument,), (series_rights_decision, second))


@pytest.mark.parametrize(
    ("field_name", "field_value", "message"),
    [
        ("rights_instrument_id", "unknown-rights-instrument", "unknown rights instrument"),
        ("rights_instrument_url", "https://example.org/rights/different", "URL does not match"),
        ("rights_instrument_accessed_on", date(2026, 7, 15), "access date does not match"),
        ("approval_recorded_at", "2026-07-15T08:00:00Z", "approval cannot precede"),
        ("approval_recorded_at", "2026-07-17T08:00:00Z", "approval cannot follow"),
    ],
)
def test_catalog_rejects_inconsistent_decision_provenance(
    rights_instrument: RightsInstrument,
    series_rights_decision: SeriesRightsDecision,
    field_name: str,
    field_value: object,
    message: str,
) -> None:
    payload = _decision_payload(series_rights_decision)
    payload[field_name] = field_value
    decision = SeriesRightsDecision.model_validate(payload)

    with pytest.raises(ValidationError, match=message):
        _catalog((rights_instrument,), (decision,))


@pytest.mark.parametrize(
    ("instrument_mutation", "message"),
    [
        (
            {
                "applicable_source_systems": (SourceSystem.ECOS,),
                "applicable_content_classes": (ContentClass.ECOS_BOK_AUTHORED,),
            },
            "source system is outside",
        ),
        (
            {
                "applicable_source_systems": (
                    SourceSystem.ECOS,
                    SourceSystem.OTHER_OFFICIAL,
                ),
                "applicable_content_classes": (ContentClass.ECOS_BOK_AUTHORED,),
            },
            "content class is outside",
        ),
    ],
)
def test_catalog_combines_decision_with_instrument_scope(
    rights_instrument: RightsInstrument,
    series_rights_decision: SeriesRightsDecision,
    instrument_mutation: dict[str, object],
    message: str,
) -> None:
    payload = rights_instrument.model_dump(mode="python")
    payload.update(instrument_mutation)
    instrument = RightsInstrument.model_validate(payload)

    with pytest.raises(ValidationError, match=message):
        _catalog((instrument,), (series_rights_decision,))


def test_catalog_rejects_instrument_access_or_capture_after_recording(
    rights_instrument: RightsInstrument,
    series_rights_decision: SeriesRightsDecision,
) -> None:
    payload = rights_instrument.model_dump(mode="python")
    payload.update(accessed_on=date(2026, 7, 17), verification_capture=None)
    payload["terms_evidence"]["accessed_on"] = date(2026, 7, 17)
    instrument = RightsInstrument.model_validate(payload)
    with pytest.raises(ValidationError, match="access cannot follow"):
        _catalog((instrument,), (series_rights_decision,))

    payload = rights_instrument.model_dump(mode="python")
    payload["verification_capture"]["captured_at"] = "2026-07-17T08:00:00Z"
    instrument = RightsInstrument.model_validate(payload)
    with pytest.raises(ValidationError, match="capture cannot follow"):
        _catalog((instrument,), (series_rights_decision,))


def test_catalog_accepts_instrument_without_capture(
    rights_instrument: RightsInstrument,
    series_rights_decision: SeriesRightsDecision,
) -> None:
    payload = rights_instrument.model_dump(mode="python")
    payload["verification_capture"] = None
    instrument = RightsInstrument.model_validate(payload)

    assert _catalog((instrument,), (series_rights_decision,)).instruments[0] == instrument


def test_catalog_rejects_future_evidence_and_expired_allowed_decision(
    rights_instrument: RightsInstrument,
    series_rights_decision: SeriesRightsDecision,
) -> None:
    payload = _decision_payload(series_rights_decision)
    payload["evidence"][0]["accessed_on"] = date(2026, 7, 17)
    decision = SeriesRightsDecision.model_validate(payload)
    with pytest.raises(ValidationError, match="evidence access cannot follow"):
        _catalog((rights_instrument,), (decision,))

    payload = _decision_payload(series_rights_decision)
    payload["valid_until"] = date(2026, 7, 16)
    decision = SeriesRightsDecision.model_validate(payload)
    with pytest.raises(ValidationError, match="expired at catalog recording"):
        _catalog(
            (rights_instrument,),
            (decision,),
            recorded_at=datetime(2026, 7, 17, 9, 0, tzinfo=UTC),
        )


def test_noncommercial_catalog_rejects_commercial_intent(
    rights_instrument: RightsInstrument,
    series_rights_decision: SeriesRightsDecision,
) -> None:
    payload = _decision_payload(series_rights_decision)
    payload["intended_operations"] = (
        *payload["intended_operations"],
        RightsOperation.COMMERCIAL_USE,
    )
    payload["operation_rules"] = (
        *payload["operation_rules"],
        _rule(RightsOperation.COMMERCIAL_USE, OperationStatus.PERMITTED),
    )
    decision = SeriesRightsDecision.model_validate(payload)

    with pytest.raises(ValidationError, match="cannot intend commercial use"):
        _catalog((rights_instrument,), (decision,))


def test_ecos_other_allowed_requires_producer_specific_instrument(
    rights_instrument: RightsInstrument,
    series_rights_decision: SeriesRightsDecision,
) -> None:
    payload = _ecos_payload(series_rights_decision, ContentClass.ECOS_OTHER_AUTHORED)
    payload["evidence"] = (
        *payload["evidence"],
        _terms_evidence(RightsEvidenceKind.PRODUCER_SPECIFIC_TERMS),
    )
    decision = SeriesRightsDecision.model_validate(payload)
    generic_instrument = _instrument_for(
        rights_instrument,
        SourceSystem.ECOS,
        ContentClass.ECOS_OTHER_AUTHORED,
    )

    with pytest.raises(ValidationError, match="producer-specific instrument"):
        _catalog((generic_instrument,), (decision,))

    specific_instrument = _instrument_for(
        rights_instrument,
        SourceSystem.ECOS,
        ContentClass.ECOS_OTHER_AUTHORED,
        terms_kind=RightsEvidenceKind.PRODUCER_SPECIFIC_TERMS,
    )
    assert _catalog((specific_instrument,), (decision,)).decisions == (decision,)


def test_kosis_publication_requires_licensed_dataset_terms_instrument(
    rights_instrument: RightsInstrument,
    series_rights_decision: SeriesRightsDecision,
) -> None:
    payload = _kosis_payload(
        series_rights_decision,
        ContentClass.KOSIS_PUBLICATION,
        KosisContentCategory.PUBLICATION,
    )
    payload["evidence"] = (
        *payload["evidence"],
        _terms_evidence(RightsEvidenceKind.DATASET_TERMS),
    )
    decision = SeriesRightsDecision.model_validate(payload)
    generic_instrument = _instrument_for(
        rights_instrument,
        SourceSystem.KOSIS,
        ContentClass.KOSIS_PUBLICATION,
    )
    with pytest.raises(ValidationError, match="licensed dataset-terms"):
        _catalog((generic_instrument,), (decision,))

    dataset_instrument = _instrument_for(
        rights_instrument,
        SourceSystem.KOSIS,
        ContentClass.KOSIS_PUBLICATION,
        terms_kind=RightsEvidenceKind.DATASET_TERMS,
        license_identifier="KOGL-Type-1",
    )
    assert _catalog((dataset_instrument,), (decision,)).decisions == (decision,)


def _decision_payload(decision: SeriesRightsDecision) -> dict[str, object]:
    return decision.model_dump(mode="python")


def _base_decision_payload() -> dict[str, object]:
    return {
        "table_id": "TABLE_001",
        "item_id": "ITEM_001",
        "table_title": "Synthetic Statistics Table",
        "item_title": "Synthetic Index",
        "producer_mapping_title": "Synthetic Statistics Table",
        "frequency": "monthly",
        "original_producer": "Example Public Institution",
    }


def _scope_observation(
    payload: dict[str, object],
    source_system: SourceSystem,
    category: KosisContentCategory | None = None,
) -> dict[str, object]:
    return EvidenceObservation(
        source_system=source_system,
        table_id=payload["table_id"],
        item_id=payload["item_id"],
        table_title=payload["table_title"],
        item_title=payload["item_title"],
        mapping_title=payload["producer_mapping_title"],
        frequency=payload["frequency"],
        original_producer=payload["original_producer"],
        kosis_content_category=category,
    ).model_dump(mode="python")


def _scope_evidence(
    payload: dict[str, object],
    source_system: SourceSystem,
    category: KosisContentCategory | None = None,
) -> dict[str, object]:
    claims = [
        EvidenceClaim.SERIES_SCOPE,
        EvidenceClaim.ORIGINAL_PRODUCER,
        EvidenceClaim.TITLE_FREQUENCY,
    ]
    if category is not None:
        claims.append(EvidenceClaim.CONTENT_CATEGORY)
    return RightsEvidence(
        kind=RightsEvidenceKind.SOURCE_METADATA,
        official_url="https://example.org/evidence/source-metadata",
        accessed_on=date(2026, 7, 16),
        claims=tuple(claims),
        assertion="Synthetic exact source metadata.",
        observed=EvidenceObservation.model_validate(
            _scope_observation(payload, source_system, category)
        ),
    ).model_dump(mode="python")


def _producer_evidence(
    payload: dict[str, object],
    kind: RightsEvidenceKind,
    source_system: SourceSystem = SourceSystem.ECOS,
) -> dict[str, object]:
    return RightsEvidence(
        kind=kind,
        official_url=f"https://example.org/evidence/{kind.value}",
        accessed_on=date(2026, 7, 16),
        claims=(EvidenceClaim.ORIGINAL_PRODUCER, EvidenceClaim.TITLE_FREQUENCY),
        assertion="Synthetic exact producer/title/frequency mapping.",
        observed=EvidenceObservation(
            source_system=source_system,
            original_producer=payload["original_producer"],
            mapping_title=payload["producer_mapping_title"],
            frequency=payload["frequency"],
        ),
    ).model_dump(mode="python")


def _terms_evidence(kind: RightsEvidenceKind) -> dict[str, object]:
    return RightsEvidence(
        kind=kind,
        official_url=f"https://example.org/evidence/{kind.value}",
        accessed_on=date(2026, 7, 16),
        claims=(EvidenceClaim.RIGHTS_TERMS,),
        assertion="Synthetic terms evidence.",
    ).model_dump(mode="python")


def _cross_payload(decision: SeriesRightsDecision) -> dict[str, object]:
    payload = _decision_payload(decision)
    payload["producer_mapping_basis"] = (
        ProducerMappingBasis.OWNER_APPROVED_OFFICIAL_CROSS_SOURCE_TITLE_FREQUENCY_MAPPING
    )
    payload["evidence"] = (
        _scope_evidence(payload, SourceSystem.OTHER_OFFICIAL),
        _producer_evidence(
            payload,
            RightsEvidenceKind.OFFICIAL_CROSS_SOURCE_CATALOG,
            SourceSystem.KOSIS,
        ),
    )
    return payload


def _other_source_payload(
    decision: SeriesRightsDecision,
    source_system: SourceSystem,
    content_class: ContentClass,
) -> dict[str, object]:
    payload = _decision_payload(decision)
    payload.update(source_system=source_system, content_class=content_class)
    payload["evidence"] = (_scope_evidence(payload, source_system),)
    return payload


def _ecos_payload(
    decision: SeriesRightsDecision,
    content_class: ContentClass,
) -> dict[str, object]:
    payload = _decision_payload(decision)
    producer = "한국은행" if content_class is ContentClass.ECOS_BOK_AUTHORED else "Example Agency"
    status = (
        ThirdPartyStatus.FIRST_PARTY
        if content_class is ContentClass.ECOS_BOK_AUTHORED
        else ThirdPartyStatus.THIRD_PARTY
    )
    payload.update(
        source_system=SourceSystem.ECOS,
        content_class=content_class,
        original_producer=producer,
        third_party_status=status,
    )
    payload["evidence"] = (_scope_evidence(payload, SourceSystem.ECOS),)
    return payload


def _kosis_payload(
    decision: SeriesRightsDecision,
    content_class: ContentClass,
    category: KosisContentCategory,
) -> dict[str, object]:
    payload = _decision_payload(decision)
    payload.update(
        source_system=SourceSystem.KOSIS,
        content_class=content_class,
        kosis_content_category=category,
    )
    payload["evidence"] = (_scope_evidence(payload, SourceSystem.KOSIS, category),)
    payload["operation_rules"] = (
        *payload["operation_rules"],
        _rule(RightsOperation.SELL_UNCHANGED, OperationStatus.PROHIBITED),
    )
    payload["attribution"] = _attribution((*COMMON_ATTRIBUTION, *KOSIS_DETAIL_ATTRIBUTION))
    return payload


def _attribution(fields: tuple[AttributionField, ...]) -> dict[str, object]:
    return AttributionRequirement(
        fields=fields,
        template=" | ".join(f"{{{field.value}}}" for field in fields),
    ).model_dump(mode="python")


def _rule(operation: RightsOperation, status: OperationStatus) -> dict[str, object]:
    return OperationRule(
        operation=operation,
        status=status,
        notes=None if status is OperationStatus.PERMITTED else "Synthetic restriction.",
    ).model_dump(mode="python")


def _set_rule(
    payload: dict[str, object],
    operation: RightsOperation,
    status: OperationStatus,
) -> None:
    for rule in payload["operation_rules"]:
        if rule["operation"] is operation:
            rule.update(
                status=status,
                notes=None if status is OperationStatus.PERMITTED else "Synthetic restriction.",
            )


def _instrument_for(
    instrument: RightsInstrument,
    source_system: SourceSystem,
    content_class: ContentClass,
    *,
    terms_kind: RightsEvidenceKind = RightsEvidenceKind.PUBLISHER_USE_GUIDE,
    license_identifier: str | None = None,
) -> RightsInstrument:
    payload = instrument.model_dump(mode="python")
    payload.update(
        applicable_source_systems=(source_system,),
        applicable_content_classes=(content_class,),
        license_identifier=license_identifier,
    )
    payload["terms_evidence"]["kind"] = terms_kind
    return RightsInstrument.model_validate(payload)


def _catalog(
    instruments: tuple[RightsInstrument, ...],
    decisions: tuple[SeriesRightsDecision, ...],
    *,
    recorded_at: datetime = CATALOG_RECORDED_AT,
) -> RightsCatalog:
    return RightsCatalog(
        catalog_id="example-rights-catalog-test",
        recorded_at=recorded_at,
        project_use_profile=ProjectUseProfile.NONCOMMERCIAL_PUBLIC_RESEARCH,
        instruments=instruments,
        decisions=decisions,
    )
