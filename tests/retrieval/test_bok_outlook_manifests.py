"""Offline contract checks for the first real bilingual document manifests."""

from datetime import date
from pathlib import Path

from sovereignlab.retrieval import (
    DocumentChunk,
    TemporalDocumentCorpus,
    TemporalDocumentQuery,
    retrieve_temporal_documents,
)
from sovereignlab.schemas import (
    EvidenceLocator,
    LanguageCode,
    RedistributionStatus,
    SourceKind,
    SourceManifest,
)

MANIFEST_DIRECTORY = Path(__file__).parents[2] / "data" / "manifests"
KOREAN_MANIFEST_PATH = MANIFEST_DIRECTORY / "bok-outlook-2026-05-ko.json"
ENGLISH_MANIFEST_PATH = MANIFEST_DIRECTORY / "bok-outlook-2026-05-en.json"


def _load_manifest(path: Path) -> SourceManifest:
    return SourceManifest.model_validate_json(path.read_text(encoding="utf-8"))


def test_bok_outlook_manifests_preserve_independent_publication_facts() -> None:
    korean = _load_manifest(KOREAN_MANIFEST_PATH)
    english = _load_manifest(ENGLISH_MANIFEST_PATH)

    assert korean.source_id == "bok-outlook-2026-05-ko"
    assert korean.source_kind is SourceKind.DOCUMENT
    assert korean.language is LanguageCode.KOREAN
    assert korean.published_on == date(2026, 5, 28)
    assert korean.byte_size == 10_711_393
    assert korean.content_sha256 == (
        "71f78145d30190ea6bb7e2eb3bdb919c1ae4730973d1f63bed641ec12660fd97"
    )

    assert english.source_id == "bok-outlook-2026-05-en"
    assert english.source_kind is SourceKind.DOCUMENT
    assert english.language is LanguageCode.ENGLISH
    assert english.published_on == date(2026, 6, 30)
    assert english.byte_size == 3_711_417
    assert english.content_sha256 == (
        "c30dd8fae88ba62db18b38484985aad457f658a22a899de58918d7581465986d"
    )

    assert korean.canonical_url != english.canonical_url
    assert korean.content_sha256 != english.content_sha256
    assert korean.published_on < english.published_on


def test_bok_outlook_manifests_record_owner_approved_public_data_rights() -> None:
    manifests = (_load_manifest(KOREAN_MANIFEST_PATH), _load_manifest(ENGLISH_MANIFEST_PATH))

    assert all(
        manifest.redistribution.status is RedistributionStatus.ALLOWED for manifest in manifests
    )
    assert all(manifest.rights_decision is None for manifest in manifests)
    assert all(
        manifest.redistribution.license_name
        == "Bank of Korea Copyright Policy (Public Data Act Article 19 public-data branch)"
        for manifest in manifests
    )
    assert all(
        str(manifest.redistribution.license_url)
        == "https://www.bok.or.kr/portal/main/contents.do?menuNo=200228"
        for manifest in manifests
    )
    assert all(
        "attribute the Bank of Korea" in manifest.redistribution.notes for manifest in manifests
    )
    assert all("ADR 0009" in manifest.redistribution.notes for manifest in manifests)


def test_manifests_without_committed_chunks_do_not_create_searchable_content() -> None:
    manifests = (_load_manifest(KOREAN_MANIFEST_PATH), _load_manifest(ENGLISH_MANIFEST_PATH))
    corpus = TemporalDocumentCorpus(sources=manifests, chunks=())

    result = retrieve_temporal_documents(
        corpus=corpus,
        query=TemporalDocumentQuery(
            question="경제전망 보고서",
            language=LanguageCode.KOREAN,
            as_of=date(2026, 7, 1),
        ),
    )

    assert result.matches == ()


def test_retrieval_uses_each_language_editions_own_publication_date() -> None:
    korean = _load_manifest(KOREAN_MANIFEST_PATH)
    english = _load_manifest(ENGLISH_MANIFEST_PATH)
    # These are synthetic in-memory sentinels, not extracted provider text or committed chunks.
    corpus = TemporalDocumentCorpus(
        sources=(korean, english),
        chunks=(
            DocumentChunk(
                chunk_id="test-only-bok-outlook-2026-05-ko",
                source_id=korean.source_id,
                source_sha256=korean.content_sha256,
                language=korean.language,
                locator=EvidenceLocator(page=1),
                text="검증경계표식",
            ),
            DocumentChunk(
                chunk_id="test-only-bok-outlook-2026-05-en",
                source_id=english.source_id,
                source_sha256=english.content_sha256,
                language=english.language,
                locator=EvidenceLocator(page=1),
                text="publication boundary sentinel",
            ),
        ),
    )

    korean_result = retrieve_temporal_documents(
        corpus=corpus,
        query=TemporalDocumentQuery(
            question="검증경계표식",
            language=LanguageCode.KOREAN,
            as_of=date(2026, 5, 28),
        ),
    )
    english_before_release = retrieve_temporal_documents(
        corpus=corpus,
        query=TemporalDocumentQuery(
            question="publication boundary sentinel",
            language=LanguageCode.ENGLISH,
            as_of=date(2026, 5, 28),
        ),
    )
    english_on_release = retrieve_temporal_documents(
        corpus=corpus,
        query=TemporalDocumentQuery(
            question="publication boundary sentinel",
            language=LanguageCode.ENGLISH,
            as_of=date(2026, 6, 30),
        ),
    )

    assert [match.source_id for match in korean_result.matches] == [korean.source_id]
    assert english_before_release.matches == ()
    assert [match.source_id for match in english_on_release.matches] == [english.source_id]
