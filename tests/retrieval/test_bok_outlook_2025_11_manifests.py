"""Offline contract checks for the November 2025 bilingual outlook manifests."""

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
    PublicationDateBasis,
    RedistributionStatus,
    SourceKind,
    SourceManifest,
)

MANIFEST_DIRECTORY = Path(__file__).parents[2] / "data" / "manifests"
KOREAN_MANIFEST_PATH = MANIFEST_DIRECTORY / "bok-outlook-2025-11-ko.json"
ENGLISH_MANIFEST_PATH = MANIFEST_DIRECTORY / "bok-outlook-2025-11-en.json"
RULED_MANIFEST_PATHS = (
    MANIFEST_DIRECTORY / "bok-outlook-2026-05-ko.json",
    MANIFEST_DIRECTORY / "bok-outlook-2026-05-en.json",
)


def _load_manifest(path: Path) -> SourceManifest:
    return SourceManifest.model_validate_json(path.read_text(encoding="utf-8"))


def test_november_2025_manifests_preserve_independent_publication_facts() -> None:
    korean = _load_manifest(KOREAN_MANIFEST_PATH)
    english = _load_manifest(ENGLISH_MANIFEST_PATH)

    assert korean.source_id == "bok-outlook-2025-11-ko"
    assert korean.source_kind is SourceKind.DOCUMENT
    assert korean.language is LanguageCode.KOREAN
    assert korean.title == "경제전망보고서(2025년 11월)"
    assert korean.published_on == date(2026, 3, 31)
    assert korean.publication_date_basis is PublicationDateBasis.CONTENT_DATE
    assert korean.byte_size == 17_435_251
    assert korean.content_sha256 == (
        "7f51f0333ac16da57150cb32e05e5aa7dc7530ba96f389b47b604e19a872eb1b"
    )

    assert english.source_id == "bok-outlook-2025-11-en"
    assert english.source_kind is SourceKind.DOCUMENT
    assert english.language is LanguageCode.ENGLISH
    assert english.title == "Korea Economic Outlook (November 2025)"
    assert english.published_on == date(2026, 1, 22)
    assert english.publication_date_basis is PublicationDateBasis.PUBLISHER_METADATA
    assert english.byte_size == 7_033_792
    assert english.content_sha256 == (
        "d997c6a1f5853b434449a0322119fe3e9e2a3df3704e909afdfa9504a1e8eb78"
    )

    assert korean.canonical_url != english.canonical_url
    assert korean.content_sha256 != english.content_sha256
    # ADR 0011: the hashed Korean bytes were modified after the English translation appeared.
    assert english.published_on < korean.published_on


def test_november_2025_manifests_reuse_the_adr_0009_family_ruling() -> None:
    november = (_load_manifest(KOREAN_MANIFEST_PATH), _load_manifest(ENGLISH_MANIFEST_PATH))
    ruled = tuple(_load_manifest(path) for path in RULED_MANIFEST_PATHS)

    for manifest, ruled_manifest in zip(november, ruled, strict=True):
        assert manifest.document_family == ruled_manifest.document_family == "bok-economic-outlook"
        assert manifest.publisher == ruled_manifest.publisher == "Bank of Korea"
        assert manifest.language is ruled_manifest.language
        assert manifest.redistribution.status is RedistributionStatus.ALLOWED
        assert manifest.redistribution.license_name == ruled_manifest.redistribution.license_name
        assert manifest.redistribution.license_url == ruled_manifest.redistribution.license_url
        assert manifest.rights_decision is None
        assert "ADR 0009" in manifest.redistribution.notes
        assert "attribute the Bank of Korea" in manifest.redistribution.notes
        assert manifest.published_on < ruled_manifest.published_on
        assert manifest.content_sha256 != ruled_manifest.content_sha256


def test_retrieval_uses_each_november_2025_editions_own_publication_date() -> None:
    korean = _load_manifest(KOREAN_MANIFEST_PATH)
    english = _load_manifest(ENGLISH_MANIFEST_PATH)
    # These are synthetic in-memory sentinels, not extracted provider text or committed chunks.
    corpus = TemporalDocumentCorpus(
        sources=(korean, english),
        chunks=(
            DocumentChunk(
                chunk_id="test-only-bok-outlook-2025-11-ko",
                source_id=korean.source_id,
                source_sha256=korean.content_sha256,
                language=korean.language,
                locator=EvidenceLocator(page=1),
                text="검증경계표식",
            ),
            DocumentChunk(
                chunk_id="test-only-bok-outlook-2025-11-en",
                source_id=english.source_id,
                source_sha256=english.content_sha256,
                language=english.language,
                locator=EvidenceLocator(page=1),
                text="publication boundary sentinel",
            ),
        ),
    )

    def matches(question: str, language: LanguageCode, as_of: date) -> list[str]:
        result = retrieve_temporal_documents(
            corpus=corpus,
            query=TemporalDocumentQuery(question=question, language=language, as_of=as_of),
        )
        return [match.source_id for match in result.matches]

    assert matches("검증경계표식", LanguageCode.KOREAN, date(2026, 3, 30)) == []
    assert matches("검증경계표식", LanguageCode.KOREAN, date(2026, 3, 31)) == [korean.source_id]
    sentinel = "publication boundary sentinel"
    assert matches(sentinel, LanguageCode.ENGLISH, date(2026, 1, 21)) == []
    assert matches(sentinel, LanguageCode.ENGLISH, date(2026, 1, 22)) == [english.source_id]
