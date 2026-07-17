"""Build the append-only rights catalog approved in ADR 0007."""

import json
import sys
from datetime import UTC, date, datetime
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))

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

    previous_path = root / "data" / "rights" / "kor-rtd-rights-2026-07-16.json"
    output_path = root / "data" / "rights" / "kor-rtd-rights-2026-07-17.json"
    previous = RightsCatalog.model_validate_json(previous_path.read_text(encoding="utf-8"))
    approved_at = datetime(2026, 7, 17, 11, 35, 6, tzinfo=UTC)

    kosis_terms = (
        "KOSIS 국내통계는 상세 출처를 표시하면 상업·비상업 목적으로 이용, 재이용, 가공 및 "
        "재배포할 수 있다. 왜곡, 재식별 및 변경하지 않은 원자료의 유료 단독 판매는 금지한다."
    )
    kosis_instrument = RightsInstrument(
        instrument_id="kosis-use-guide-2026-07-17",
        issuer="국가데이터처",
        title="KOSIS 통계정보 이용지침",
        official_url="https://kosis.kr/nsistN/kosisUseGuide.do",
        accessed_on=date(2026, 7, 17),
        applicable_source_systems=(SourceSystem.KOSIS,),
        applicable_content_classes=(
            ContentClass.KOSIS_DOMESTIC_STATISTICS,
            ContentClass.KOSIS_EASY_VIEW_STATISTICS,
        ),
        terms_summary=kosis_terms,
        terms_evidence=RightsEvidence(
            kind=RightsEvidenceKind.PUBLISHER_USE_GUIDE,
            official_url="https://kosis.kr/nsistN/kosisUseGuide.do",
            accessed_on=date(2026, 7, 17),
            claims=(EvidenceClaim.RIGHTS_TERMS,),
            assertion=kosis_terms,
        ),
    )

    oecd_terms = (
        "OECD Data는 추가적인 데이터별 제한이나 제3자 권리가 없는 경우 출처를 표시하여 추출, "
        "다운로드, 복사, 가공, 배포, 공유 및 임베드할 수 있다. 공유 시 동일한 OECD 출처표시 "
        "요건을 전달해야 한다."
    )
    oecd_instrument = RightsInstrument(
        instrument_id="oecd-data-terms-2026-07-17",
        issuer="OECD",
        title="OECD Terms & Conditions — Data",
        official_url="https://www.oecd.org/en/about/terms-conditions.html",
        accessed_on=date(2026, 7, 17),
        applicable_source_systems=(SourceSystem.OECD,),
        applicable_content_classes=(ContentClass.OECD_DATA,),
        terms_summary=oecd_terms,
        terms_evidence=RightsEvidence(
            kind=RightsEvidenceKind.PUBLISHER_USE_GUIDE,
            official_url="https://www.oecd.org/en/about/terms-conditions.html",
            accessed_on=date(2026, 7, 17),
            claims=(EvidenceClaim.RIGHTS_TERMS,),
            assertion=oecd_terms,
        ),
    )

    permitted = tuple(
        OperationRule(operation=operation, status=OperationStatus.PERMITTED)
        for operation in (
            RightsOperation.USE,
            RightsOperation.PROCESS,
            RightsOperation.REDISTRIBUTE,
            RightsOperation.COMMERCIAL_USE,
            RightsOperation.NONCOMMERCIAL_USE,
        )
    )
    intended = (
        RightsOperation.USE,
        RightsOperation.PROCESS,
        RightsOperation.REDISTRIBUTE,
        RightsOperation.NONCOMMERCIAL_USE,
    )
    approval_reference = "docs/decisions/0007-kosis-cpi-oecd-cli-rights.md#approval-record"

    kosis_decision = SeriesRightsDecision(
        decision_id="kosis-101-dt-1j22003-t-t10-rights-v1",
        publisher="국가데이터처",
        original_producer="국가데이터처",
        kosis_content_category=KosisContentCategory.DOMESTIC_STATISTICS,
        source_system=SourceSystem.KOSIS,
        table_id="DT_1J22003",
        item_id="T/T10",
        table_title="소비자물가지수(2020\uff1d100)",
        item_title="소비자물가지수(총지수), 전국",
        producer_mapping_title="소비자물가조사",
        frequency="M",
        unit="2020=100",
        content_class=ContentClass.KOSIS_DOMESTIC_STATISTICS,
        producer_mapping_basis=ProducerMappingBasis.OFFICIAL_PUBLISHER_DOCUMENTATION,
        evidence=(
            RightsEvidence(
                kind=RightsEvidenceKind.SOURCE_METADATA,
                official_url=("https://kosis.kr/statHtml/statHtml.do?orgId=101&tblId=DT_1J22003"),
                accessed_on=date(2026, 7, 17),
                claims=(
                    EvidenceClaim.SERIES_SCOPE,
                    EvidenceClaim.TITLE_FREQUENCY,
                    EvidenceClaim.CONTENT_CATEGORY,
                ),
                assertion=("KOSIS 국내통계 표 DT_1J22003의 월별 총지수 T와 전국 T10 범위이다."),
                observed=EvidenceObservation(
                    source_system=SourceSystem.KOSIS,
                    table_id="DT_1J22003",
                    item_id="T/T10",
                    table_title="소비자물가지수(2020\uff1d100)",
                    item_title="소비자물가지수(총지수), 전국",
                    frequency="M",
                    kosis_content_category=KosisContentCategory.DOMESTIC_STATISTICS,
                ),
            ),
            RightsEvidence(
                kind=RightsEvidenceKind.OFFICIAL_PUBLISHER_RELEASE,
                official_url=(
                    "https://mods.go.kr/statDesc.es?act=view&mid=a10501010000&sttr_cd=S003001"
                ),
                accessed_on=date(2026, 7, 17),
                claims=(EvidenceClaim.ORIGINAL_PRODUCER, EvidenceClaim.TITLE_FREQUENCY),
                assertion=(
                    "국가데이터처 소비자물가조사 설명은 소비자물가지수 작성기관과 월별 주기를 "
                    "확인한다."
                ),
                observed=EvidenceObservation(
                    source_system=SourceSystem.OTHER_OFFICIAL,
                    mapping_title="소비자물가조사",
                    frequency="M",
                    original_producer="국가데이터처",
                ),
            ),
        ),
        rights_instrument_id=kosis_instrument.instrument_id,
        rights_instrument_url=kosis_instrument.official_url,
        rights_instrument_accessed_on=kosis_instrument.accessed_on,
        third_party_status=ThirdPartyStatus.FIRST_PARTY,
        operation_rules=(
            *permitted,
            OperationRule(
                operation=RightsOperation.SELL_UNCHANGED,
                status=OperationStatus.PROHIBITED,
                notes="변경하지 않은 KOSIS 원자료의 유료 단독 판매를 금지한다.",
            ),
            OperationRule(
                operation=RightsOperation.DISTORT,
                status=OperationStatus.PROHIBITED,
                notes="KOSIS 통계정보를 임의로 왜곡하지 않는다.",
            ),
            OperationRule(
                operation=RightsOperation.REIDENTIFY,
                status=OperationStatus.PROHIBITED,
                notes="통계정보를 이용한 재식별을 금지한다.",
            ),
        ),
        intended_operations=intended,
        attribution=AttributionRequirement(
            fields=(
                AttributionField.PUBLISHER,
                AttributionField.ORIGINAL_PRODUCER,
                AttributionField.SURVEY_NAME,
                AttributionField.TABLE_NAME,
                AttributionField.STATISTIC_NAME,
                AttributionField.AUTHORING_DATE,
                AttributionField.REFERENCE_DATE,
                AttributionField.RETRIEVAL_DATE,
                AttributionField.SOURCE_URL,
            ),
            template=(
                "출처: KOSIS({publisher}; 작성기관: {original_producer}; 조사명: {survey_name}; "
                "통계표: {table_name}; {statistic_name}; 작성일: {authoring_date}; 기준시점: "
                "{reference_date}), 조회일 {retrieval_date}. KOR-RTD에서 빈티지 구조로 "
                "가공함. {source_url}"
            ),
        ),
        decision_state=RedistributionStatus.ALLOWED,
        decision_basis=(
            "Owner-approved exact national CPI scope. KOSIS identifies the domestic table/item/"
            "geography and 국가데이터처 documentation confirms the producer and monthly survey."
        ),
        approved_by="Hyungbae Cho",
        approval_recorded_at=approved_at,
        approval_record_reference=approval_reference,
    )

    oecd_decision = SeriesRightsDecision(
        decision_id="oecd-stes-revisions-kor-m-li-aa-rights-v1",
        publisher="OECD",
        original_producer="OECD",
        source_system=SourceSystem.OECD,
        table_id="DSD_STES_REVISIONS@DF_STES_REVISIONS",
        item_id="KOR.M.LI_AA.IX._T",
        table_title="Short-term economic statistics revisions",
        item_title="Composite leading indicator (CLI) amplitude adjusted — Korea",
        producer_mapping_title="Composite Leading Indicators (CLI)",
        frequency="M",
        unit="Index, amplitude adjusted",
        content_class=ContentClass.OECD_DATA,
        producer_mapping_basis=ProducerMappingBasis.DIRECT_SOURCE_METADATA,
        evidence=(
            RightsEvidence(
                kind=RightsEvidenceKind.SOURCE_METADATA,
                official_url=(
                    "https://sdmx.oecd.org/public/rest/data/"
                    "OECD.SDD.STES,DSD_STES_REVISIONS%40DF_STES_REVISIONS,4.0/"
                    "KOR.M.LI_AA...?format=csvfilewithlabels"
                ),
                accessed_on=date(2026, 7, 17),
                claims=(
                    EvidenceClaim.SERIES_SCOPE,
                    EvidenceClaim.ORIGINAL_PRODUCER,
                    EvidenceClaim.TITLE_FREQUENCY,
                ),
                assertion=(
                    "OECD.SDD.STES revision metadata identifies the exact Korea monthly "
                    "amplitude-adjusted CLI series and OECD first-party flow."
                ),
                observed=EvidenceObservation(
                    source_system=SourceSystem.OECD,
                    table_id="DSD_STES_REVISIONS@DF_STES_REVISIONS",
                    item_id="KOR.M.LI_AA.IX._T",
                    table_title="Short-term economic statistics revisions",
                    item_title="Composite leading indicator (CLI) amplitude adjusted — Korea",
                    mapping_title="Composite Leading Indicators (CLI)",
                    frequency="M",
                    original_producer="OECD",
                ),
            ),
        ),
        rights_instrument_id=oecd_instrument.instrument_id,
        rights_instrument_url=oecd_instrument.official_url,
        rights_instrument_accessed_on=oecd_instrument.accessed_on,
        third_party_status=ThirdPartyStatus.FIRST_PARTY,
        operation_rules=(
            *permitted,
            OperationRule(
                operation=RightsOperation.DISTORT,
                status=OperationStatus.PROHIBITED,
                notes=(
                    "KOR-RTD preserves source values and labels adaptations without implying "
                    "OECD endorsement."
                ),
            ),
        ),
        intended_operations=intended,
        attribution=AttributionRequirement(
            fields=(
                AttributionField.PUBLISHER,
                AttributionField.ORIGINAL_PRODUCER,
                AttributionField.STATISTIC_NAME,
                AttributionField.RETRIEVAL_DATE,
                AttributionField.SOURCE_URL,
            ),
            template=(
                "Source: {publisher}; original producer: {original_producer}; statistic: "
                "{statistic_name}; retrieved {retrieval_date}; {source_url}. KOR-RTD preserves "
                "the captured vintage; no OECD endorsement is implied."
            ),
        ),
        decision_state=RedistributionStatus.ALLOWED,
        decision_basis=(
            "Owner-approved exact OECD-produced Korea headline CLI scope after checking the OECD "
            "dataset page, SDMX agency/series metadata, and OECD Data terms."
        ),
        approved_by="Hyungbae Cho",
        approval_recorded_at=approved_at,
        approval_record_reference=approval_reference,
    )

    catalog = RightsCatalog(
        catalog_id="kor-rtd-rights-2026-07-17",
        recorded_at=approved_at,
        project_use_profile=previous.project_use_profile,
        supersedes_catalog_id=previous.catalog_id,
        instruments=(*previous.instruments, kosis_instrument, oecd_instrument),
        decisions=(*previous.decisions, kosis_decision, oecd_decision),
    )
    payload = json.dumps(
        catalog.model_dump(mode="json", exclude_none=True),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(f"{payload}\n")
    print(output_path.relative_to(root))


if __name__ == "__main__":
    main()
