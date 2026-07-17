"""Offline tests for the append-only KOR-RTD weekly capture."""

import hashlib
import json
from datetime import UTC, date, datetime
from pathlib import Path

import httpx
import pytest
from pydantic import SecretStr

from sovereignlab.harvest import weekly
from sovereignlab.schemas import (
    AvailabilityAssertion,
    AvailabilityEvidenceBasis,
    BenchmarkBundle,
    EditionAvailabilityLedger,
    EditionResolutionStatus,
    RedistributionStatus,
    RightsCatalog,
    SourceManifest,
)

CAPTURED_AT = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
VALID_FROM = datetime(2026, 7, 8, 9, 33, 35, 737000, tzinfo=UTC)


def _constraint_xml(
    editions: tuple[str, ...] = ("202606", "202607"),
    *,
    content: bool,
    valid_from: datetime | None = VALID_FROM,
    agency: str = "OECD.SDD.STES",
    flow: str = "DSD_STES_REVISIONS@DF_STES_REVISIONS",
    flow_version: str = "4.0",
    constraint_id: str | None = None,
    constraint_version: str | None = None,
) -> bytes:
    resolved_id = constraint_id or (weekly.OECD_CONSTRAINT_ID if content else "CC")
    resolved_version = constraint_version or ("4.0" if content else "1.0")
    valid_from_attribute = (
        f' validFrom="{valid_from.isoformat().replace("+00:00", "Z")}"'
        if valid_from is not None
        else ""
    )
    values = "".join(f"<Value>{edition}</Value>" for edition in editions)
    return (
        f'<Structure><ContentConstraint id="{resolved_id}" version="{resolved_version}"'
        f'{valid_from_attribute}><Dataflow><Ref agencyID="{agency}" id="{flow}" '
        f'version="{flow_version}" /></Dataflow><CubeRegion><KeyValue id="EDITION">'
        f"{values}</KeyValue></CubeRegion></ContentConstraint></Structure>"
    ).encode()


def _ecos_response(table_id: str, item_id: str) -> bytes:
    return json.dumps(
        {
            "StatisticSearch": {
                "list_total_count": 1,
                "row": [
                    {
                        "STAT_CODE": table_id,
                        "ITEM_CODE1": item_id,
                        "TIME": "2026Q2" if table_id == "200Y108" else "202606",
                        "DATA_VALUE": "1.0",
                    }
                ],
            }
        }
    ).encode()


def _kosis_response() -> bytes:
    return json.dumps(
        [
            {
                "ORG_ID": "101",
                "TBL_ID": "DT_1J22003",
                "TBL_NM": "소비자물가지수(2020\uff1d100)",
                "ITM_ID": "T",
                "ITM_NM": "소비자물가지수(총지수)",
                "PRD_SE": "M",
                "PRD_DE": "202606",
                "UNIT_NM": "2020\uff1d100",
                "C1": "T10",
                "C1_NM": "전국",
                "DT": "116.3",
            }
        ],
        ensure_ascii=False,
    ).encode()


def _client(
    *,
    available: bytes | None = None,
    content: bytes | None = None,
    ecos_payloads: dict[str, bytes] | None = None,
    kosis_payload: bytes | None = None,
    status_code: int = 200,
) -> httpx.Client:
    available_body = _constraint_xml(content=False) if available is None else available
    content_body = _constraint_xml(content=True) if content is None else content
    payloads = ecos_payloads or {}

    def handler(request: httpx.Request) -> httpx.Response:
        if status_code != 200:
            return httpx.Response(status_code, request=request)
        url = str(request.url)
        if "availableconstraint" in url:
            return httpx.Response(200, content=available_body, request=request)
        if "contentconstraint" in url:
            return httpx.Response(200, content=content_body, request=request)
        for table_id, payload in payloads.items():
            if f"/{table_id}/" in url:
                return httpx.Response(200, content=payload, request=request)
        if "statisticsParameterData.do" in url and kosis_payload is not None:
            return httpx.Response(200, content=kosis_payload, request=request)
        raise AssertionError(f"unexpected request: {url}")

    return httpx.Client(transport=httpx.MockTransport(handler))


def _run(
    repository_root: Path,
    client: httpx.Client,
    *,
    captured_at: datetime = CAPTURED_AT,
    key: SecretStr | None = None,
    kosis_key: SecretStr | None = None,
    rights_catalog: RightsCatalog | None = None,
) -> weekly.HarvestSummary:
    with client:
        return weekly.run_weekly_capture(
            repository_root,
            client=client,
            ecos_api_key=key,
            kosis_api_key=kosis_key,
            rights_catalog=rights_catalog,
            now=lambda: captured_at,
        )


def _load_ledger(
    repository_root: Path,
    summary: weekly.HarvestSummary,
) -> EditionAvailabilityLedger:
    return EditionAvailabilityLedger.model_validate_json(
        (repository_root / summary.ledger_path).read_text(encoding="utf-8")
    )


def test_oecd_only_capture_writes_valid_manifest_backed_first_ledger(tmp_path: Path) -> None:
    summary = _run(tmp_path, _client())

    assert summary.ecos_skipped_missing_key
    assert summary.ecos_series_captured == ()
    assert summary.kosis_skipped_missing_key
    assert summary.kosis_series_captured == ()
    assert len(summary.archive_paths) == 2
    assert len(summary.manifest_paths) == 2
    ledger = _load_ledger(tmp_path, summary)
    assert ledger.dataflow_id == weekly.OECD_DATAFLOW_ID
    assert ledger.complete_through == CAPTURED_AT
    assert [record.edition for record in ledger.editions] == ["202606", "202607"]
    assert ledger.editions[0].status is EditionResolutionStatus.UNRESOLVED
    latest = ledger.editions[1]
    assert latest.status is EditionResolutionStatus.RESOLVED
    assert latest.available_by == VALID_FROM
    assert {item.basis for item in latest.evidence} == {
        AvailabilityEvidenceBasis.SDMX_CONSTRAINT_VALID_FROM,
        AvailabilityEvidenceBasis.FIRST_OBSERVED_AT,
    }

    manifests = tuple(
        SourceManifest.model_validate_json((tmp_path / path).read_text(encoding="utf-8"))
        for path in summary.manifest_paths
    )
    assert all(
        manifest.redistribution.status is RedistributionStatus.METADATA_ONLY
        for manifest in manifests
    )
    assert all(manifest.rights_decision is None for manifest in manifests)
    BenchmarkBundle(sources=manifests, records=(), availability_ledgers=(ledger,))
    for manifest, archive_path in zip(manifests, summary.archive_paths, strict=True):
        body = (tmp_path / archive_path).read_bytes()
        assert hashlib.sha256(body).hexdigest() == manifest.content_sha256
        assert len(body) == manifest.byte_size


def test_capture_refuses_to_rewrite_an_existing_timestamp(tmp_path: Path) -> None:
    _run(tmp_path, _client())

    with pytest.raises(FileExistsError, match="append-only capture refuses"):
        _run(tmp_path, _client())


def test_later_capture_resolves_only_newly_observed_editions(tmp_path: Path) -> None:
    first = _run(tmp_path, _client())
    first_ledger = _load_ledger(tmp_path, first)
    next_capture = datetime(2026, 8, 10, 1, 2, 3, tzinfo=UTC)
    new_valid_from = datetime(2026, 8, 5, 4, 0, tzinfo=UTC)
    second = _run(
        tmp_path,
        _client(
            available=_constraint_xml(("202606", "202607", "202608"), content=False),
            content=_constraint_xml(
                ("202606", "202607", "202608"),
                content=True,
                valid_from=new_valid_from,
            ),
        ),
        captured_at=next_capture,
    )

    ledger = _load_ledger(tmp_path, second)
    assert ledger.supersedes_ledger_id == first_ledger.ledger_id
    assert ledger.editions[:2] == first_ledger.editions
    newest = ledger.editions[2]
    assert newest.available_by == new_valid_from
    assert newest.last_absent_at == first_ledger.complete_through
    assert any(
        evidence.supports is AvailabilityAssertion.LAST_ABSENT_AT for evidence in newest.evidence
    )


def test_stale_valid_from_uses_first_observed_time_for_a_new_edition(tmp_path: Path) -> None:
    _run(tmp_path, _client())
    next_capture = datetime(2026, 8, 10, tzinfo=UTC)
    second = _run(
        tmp_path,
        _client(
            available=_constraint_xml(("202606", "202607", "202608"), content=False),
            content=_constraint_xml(
                ("202606", "202607", "202608"),
                content=True,
                valid_from=VALID_FROM,
            ),
        ),
        captured_at=next_capture,
    )

    newest = _load_ledger(tmp_path, second).editions[-1]
    assert newest.available_by == next_capture
    assert all(
        evidence.basis is not AvailabilityEvidenceBasis.SDMX_CONSTRAINT_VALID_FROM
        for evidence in newest.evidence
    )


def test_ecos_capture_is_rights_linked_and_never_persists_the_key(
    tmp_path: Path,
) -> None:
    key_value = "private-test-key"
    catalog = weekly.load_rights_catalog(Path.cwd())
    summary = _run(
        tmp_path,
        _client(
            ecos_payloads={
                "200Y108": _ecos_response("200Y108", "10601"),
                "301Y017": _ecos_response("301Y017", "SA000"),
            }
        ),
        key=SecretStr(key_value),
        rights_catalog=catalog,
    )

    assert not summary.ecos_skipped_missing_key
    assert summary.ecos_series_captured == ("200Y108/10601", "301Y017/SA000")
    assert len(summary.manifest_paths) == 4
    repository_bytes = b"".join(path.read_bytes() for path in tmp_path.rglob("*") if path.is_file())
    assert key_value.encode() not in repository_bytes
    ecos_manifests = [
        SourceManifest.model_validate_json((tmp_path / path).read_text(encoding="utf-8"))
        for path in summary.manifest_paths
        if Path(path).name.startswith("ecos-")
    ]
    BenchmarkBundle(sources=tuple(ecos_manifests), records=(), rights_catalogs=(catalog,))
    assert {manifest.rights_decision.decision_id for manifest in ecos_manifests} == {
        "ecos-200y108-10601-rights-v1",
        "ecos-301y017-sa000-rights-v1",
    }
    assert all("%7Bapi-key%7D" in str(manifest.canonical_url) for manifest in ecos_manifests)


def test_ecos_key_requires_a_rights_catalog(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="requires the committed rights catalog"):
        _run(tmp_path, _client(), key=SecretStr("test-key"))


def test_kosis_capture_is_rights_linked_and_never_persists_the_key(
    tmp_path: Path,
) -> None:
    key_value = "private-kosis-test-key"
    catalog = weekly.load_rights_catalog(Path.cwd())
    summary = _run(
        tmp_path,
        _client(kosis_payload=_kosis_response()),
        kosis_key=SecretStr(key_value),
        rights_catalog=catalog,
    )

    assert not summary.kosis_skipped_missing_key
    assert summary.kosis_series_captured == ("101/DT_1J22003/T/T10",)
    assert len(summary.manifest_paths) == 3
    repository_bytes = b"".join(path.read_bytes() for path in tmp_path.rglob("*") if path.is_file())
    assert key_value.encode() not in repository_bytes
    manifest_path = next(
        tmp_path / path for path in summary.manifest_paths if Path(path).name.startswith("kosis-")
    )
    manifest = SourceManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    BenchmarkBundle(sources=(manifest,), records=(), rights_catalogs=(catalog,))
    assert manifest.rights_decision is not None
    assert manifest.rights_decision.decision_id == "kosis-101-dt-1j22003-t-t10-rights-v1"
    assert manifest.rights_decision.item_id == "T/T10"
    assert "%7Bapi-key%7D" in str(manifest.canonical_url)


def test_kosis_key_requires_a_rights_catalog(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="requires the committed rights catalog"):
        _run(tmp_path, _client(), kosis_key=SecretStr("test-key"))


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (b"not-json", "invalid KOSIS"),
        (json.dumps({"error": "not-a-list"}).encode(), "empty, invalid"),
        (b"[]", "empty, invalid"),
        (json.dumps([{}] * 1001).encode(), "exceeds"),
        (
            _kosis_response().replace(b'"ORG_ID": "101"', b'"ORG_ID": "wrong"'),
            "outside",
        ),
        (_kosis_response().replace(b'"202606"', b'"202613"'), "invalid monthly"),
        (
            json.dumps(
                json.loads(_kosis_response()) + json.loads(_kosis_response()),
                ensure_ascii=False,
            ).encode(),
            "duplicate",
        ),
        (_kosis_response().replace(b'"116.3"', b'" "'), "blank"),
    ],
)
def test_invalid_kosis_responses_fail_closed(
    tmp_path: Path,
    payload: bytes,
    message: str,
) -> None:
    catalog = weekly.load_rights_catalog(Path.cwd())
    with pytest.raises(ValueError, match=message):
        _run(
            tmp_path,
            _client(kosis_payload=payload),
            kosis_key=SecretStr("test-key"),
            rights_catalog=catalog,
        )


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (b"not-json", "invalid ECOS"),
        (json.dumps({"StatisticSearch": {"list_total_count": 0, "row": []}}).encode(), "empty"),
        (
            json.dumps(
                {
                    "StatisticSearch": {
                        "list_total_count": 1001,
                        "row": [{"STAT_CODE": "200Y108", "ITEM_CODE1": "10601"}] * 1001,
                    }
                }
            ).encode(),
            "exceeds",
        ),
        (
            json.dumps(
                {
                    "StatisticSearch": {
                        "list_total_count": 1,
                        "row": [{"STAT_CODE": "wrong", "ITEM_CODE1": "10601"}],
                    }
                }
            ).encode(),
            "outside",
        ),
    ],
)
def test_invalid_ecos_responses_fail_closed(
    tmp_path: Path,
    payload: bytes,
    message: str,
) -> None:
    catalog = weekly.load_rights_catalog(Path.cwd())
    with pytest.raises(ValueError, match=message):
        _run(
            tmp_path,
            _client(ecos_payloads={"200Y108": payload}),
            key=SecretStr("test-key"),
            rights_catalog=catalog,
        )


@pytest.mark.parametrize(
    ("available", "content", "message"),
    [
        (b"not-xml", _constraint_xml(content=True), "invalid SDMX"),
        (b"<Structure />", _constraint_xml(content=True), "exactly one ContentConstraint"),
        (
            b"<Structure><ContentConstraint/><ContentConstraint/></Structure>",
            _constraint_xml(content=True),
            "exactly one ContentConstraint",
        ),
        (
            b'<Structure><ContentConstraint id="CC" version="1.0" /></Structure>',
            _constraint_xml(content=True),
            "exactly one dataflow Ref",
        ),
        (
            _constraint_xml(content=False, agency="OTHER"),
            _constraint_xml(content=True),
            "approved STES flow",
        ),
        (
            _constraint_xml(content=False, flow_version="3.0"),
            _constraint_xml(content=True),
            "approved STES version",
        ),
        (
            _constraint_xml(content=False),
            _constraint_xml(content=True, constraint_id="WRONG"),
            "approved STES constraint",
        ),
        (
            _constraint_xml(("202607",), content=False),
            _constraint_xml(("202606", "202607"), content=True),
            "inventories differ",
        ),
    ],
)
def test_invalid_constraint_responses_fail_closed(
    tmp_path: Path,
    available: bytes,
    content: bytes,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        _run(tmp_path, _client(available=available, content=content))


@pytest.mark.parametrize(
    ("payload", "require_valid_from", "message"),
    [
        (
            b'<Structure><ContentConstraint id="CC" version="1.0">'
            b'<Ref agencyID="A" id="B" version="1"/><Ref agencyID="A" id="B" '
            b'version="1"/></ContentConstraint></Structure>',
            False,
            "exactly one dataflow Ref",
        ),
        (
            b'<Structure><ContentConstraint id="CC" version="1.0"><Ref id="B" />'
            b'<KeyValue id="EDITION"><Value>202607</Value></KeyValue>'
            b"</ContentConstraint></Structure>",
            False,
            "identity is incomplete",
        ),
        (
            b'<Structure><ContentConstraint id="CC" version="1.0">'
            b'<Ref agencyID="A" id="B" version="1"/></ContentConstraint></Structure>',
            False,
            "exactly one EDITION region",
        ),
        (
            b'<Structure><ContentConstraint id="CC" version="1.0">'
            b'<Ref agencyID="A" id="B" version="1"/>'
            b'<KeyValue id="EDITION"><Value>202607</Value></KeyValue>'
            b'<KeyValue id="EDITION"><Value>202608</Value></KeyValue>'
            b"</ContentConstraint></Structure>",
            False,
            "exactly one EDITION region",
        ),
        (_constraint_xml((), content=False), False, "non-empty and unique"),
        (_constraint_xml(("202607", "202607"), content=False), False, "non-empty and unique"),
        (_constraint_xml(("202613",), content=False), False, "invalid edition code"),
        (_constraint_xml(content=True, valid_from=None), True, "requires validFrom"),
        (
            _constraint_xml(content=True).replace(
                b"2026-07-08T09:33:35.737000Z", b"not-a-timestamp"
            ),
            True,
            "invalid aware timestamp",
        ),
    ],
)
def test_constraint_parser_rejects_ambiguous_evidence(
    payload: bytes,
    require_valid_from: bool,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        weekly._parse_constraint(payload, require_valid_from=require_valid_from)


def test_capture_rejects_future_valid_from_and_inventory_deletion(tmp_path: Path) -> None:
    future = CAPTURED_AT.replace(year=2027)
    with pytest.raises(ValueError, match="cannot follow"):
        _run(
            tmp_path,
            _client(content=_constraint_xml(content=True, valid_from=future)),
        )

    _run(tmp_path, _client())
    with pytest.raises(ValueError, match="inventory deletion"):
        _run(
            tmp_path,
            _client(
                available=_constraint_xml(("202607",), content=False),
                content=_constraint_xml(("202607",), content=True),
            ),
            captured_at=datetime(2026, 8, 17, tzinfo=UTC),
        )


def test_previous_capture_must_match_its_manifest_and_bytes(tmp_path: Path) -> None:
    first = _run(tmp_path, _client())
    available_manifest_path = next(
        tmp_path / path for path in first.manifest_paths if "availableconstraint" in path
    )
    manifest_data = json.loads(available_manifest_path.read_text(encoding="utf-8"))
    manifest_data["retrieved_at"] = "2026-07-17T11:59:59Z"
    available_manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")
    with pytest.raises(ValueError, match="complete_through"):
        _run(
            tmp_path,
            _client(),
            captured_at=datetime(2026, 8, 17, tzinfo=UTC),
        )

    manifest_data["source_id"] = "wrong"
    available_manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")
    with pytest.raises(ValueError, match="identity"):
        _run(
            tmp_path,
            _client(),
            captured_at=datetime(2026, 8, 18, tzinfo=UTC),
        )


def test_previous_capture_rejects_changed_flow_and_archive_bytes(tmp_path: Path) -> None:
    first = _run(tmp_path, _client())
    ledger_path = tmp_path / first.ledger_path
    ledger_data = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger_data["dataflow_version"] = "3.0"
    ledger_path.write_text(json.dumps(ledger_data), encoding="utf-8")
    with pytest.raises(ValueError, match="different dataflow"):
        _run(
            tmp_path,
            _client(),
            captured_at=datetime(2026, 8, 17, tzinfo=UTC),
        )

    ledger_data["dataflow_version"] = "4.0"
    ledger_path.write_text(json.dumps(ledger_data), encoding="utf-8")
    available_archive = next(
        tmp_path / path for path in first.archive_paths if "availableconstraint" in path
    )
    available_archive.write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="archived bytes"):
        _run(
            tmp_path,
            _client(),
            captured_at=datetime(2026, 8, 18, tzinfo=UTC),
        )


def test_helpers_reject_invalid_clock_period_and_naming(tmp_path: Path) -> None:
    with _client() as client, pytest.raises(ValueError, match="timezone-aware"):
        weekly.run_weekly_capture(
            tmp_path,
            client=client,
            now=lambda: datetime(2026, 7, 17),
        )
    with pytest.raises(ValueError, match="unsupported ECOS cycle"):
        weekly._ecos_end_period("A", date(2026, 7, 17))

    summary = _run(tmp_path, _client())
    ledger = _load_ledger(tmp_path, summary)
    invalid = ledger.model_copy(update={"ledger_id": "not-a-capture-id"})
    with pytest.raises(ValueError, match="naming contract"):
        weekly._ledger_token(invalid)


def test_empty_and_http_error_responses_do_not_write_artifacts(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="empty response"):
        _run(tmp_path, _client(available=b""))
    with pytest.raises(httpx.HTTPStatusError):
        _run(tmp_path, _client(status_code=503))
    assert not any(tmp_path.rglob("*.json"))


def test_append_only_preflight_and_timestamp_parser_reject_ambiguous_input(
    tmp_path: Path,
) -> None:
    artifact = weekly._PendingArtifact(tmp_path / "artifact", b"content")
    with pytest.raises(ValueError, match="duplicate artifact path"):
        weekly._write_append_only([artifact, artifact])

    artifact.path.write_bytes(b"existing")
    with pytest.raises(FileExistsError, match="refuses existing path"):
        weekly._write_append_only([artifact])
    with pytest.raises(ValueError, match="invalid aware timestamp"):
        weekly._parse_instant("2026-07-17T12:00:00")
