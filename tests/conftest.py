"""Repository-level offline fixtures shared across the test suite."""

import shutil
from datetime import timedelta
from pathlib import Path

import httpx
import pytest
from pydantic import SecretStr

from sovereignlab.harvest.weekly import HarvestSummary, load_rights_catalog, run_weekly_capture
from sovereignlab.schemas import EditionAvailabilityLedger

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_INPUT_DIRECTORIES = ("data/manifests", "data/archive", "data/availability", "data/rights")
_REPLAYED_ARCHIVE_PREFIXES = {
    "availableconstraint": "oecd-stes/oecd-stes-availableconstraint-",
    "contentconstraint": "oecd-stes/oecd-stes-contentconstraint-",
    "/200Y108/": "ecos/ecos-200y108-10601-",
    "/301Y017/": "ecos/ecos-301y017-sa000-",
    "statisticsParameterData.do": "kosis/kosis-101-dt-1j22003-t-t10-",
}


@pytest.fixture(scope="session")
def tool_registry():  # -> CallableToolRegistry
    """The three committed v1 evidence registries behind the offline tools."""

    # Imported here so the weekly capture gate, which runs only the data and harvester tests,
    # does not depend on the execution package importing cleanly.
    from sovereignlab.execution import load_committed_callable_tool_registry

    return load_committed_callable_tool_registry(REPOSITORY_ROOT)


@pytest.fixture
def committed_kor_rtd_inputs(tmp_path: Path) -> Path:
    """Copy the committed manifests, archives, ledgers, and rights catalogs."""

    for relative in _INPUT_DIRECTORIES:
        shutil.copytree(REPOSITORY_ROOT / relative, tmp_path / relative)
    return tmp_path


@pytest.fixture
def weekly_capture_after_v1(committed_kor_rtd_inputs: Path) -> tuple[Path, HarvestSummary]:
    """Append one real harvester capture a week after the newest capture in the repository.

    The mocked providers replay each source's newest archived response bytes, so the run observes
    no new edition while still writing every manifest, archive, and ledger offline. Anchoring to
    the newest capture keeps the fixture valid as real weekly captures accumulate.
    """

    root = committed_kor_rtd_inputs
    archive_root = root / "data" / "archive"
    responses = {
        marker: max(archive_root.glob(f"{prefix}*"))
        for marker, prefix in _REPLAYED_ARCHIVE_PREFIXES.items()
    }
    newest_ledger_at = max(
        EditionAvailabilityLedger.model_validate_json(path.read_bytes()).generated_at
        for path in (root / "data" / "availability").glob("oecd-stes-ledger-*.json")
    )
    captured_at = newest_ledger_at + timedelta(days=7)

    def handler(request: httpx.Request) -> httpx.Response:
        matches = [path for marker, path in responses.items() if marker in request.url.path]
        assert len(matches) == 1, request.url.host
        return httpx.Response(200, content=matches[0].read_bytes(), request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        summary = run_weekly_capture(
            root,
            client=client,
            ecos_api_key=SecretStr("offline-test-key"),
            kosis_api_key=SecretStr("offline-test-key"),
            rights_catalog=load_rights_catalog(root),
            now=lambda: captured_at,
        )
    return root, summary
