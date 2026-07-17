"""Run one append-only KOR-RTD weekly capture from the repository root."""

import argparse
import json
import sys
from pathlib import Path

import httpx


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    repository_root = args.repository_root.resolve()
    sys.path.insert(0, str(repository_root / "src"))

    from sovereignlab.config import Settings
    from sovereignlab.harvest.weekly import load_rights_catalog, run_weekly_capture

    settings = Settings()
    rights_catalog = (
        load_rights_catalog(repository_root) if settings.ecos_api_key is not None else None
    )
    with httpx.Client(follow_redirects=True, timeout=60.0) as client:
        summary = run_weekly_capture(
            repository_root,
            client=client,
            ecos_api_key=settings.ecos_api_key,
            rights_catalog=rights_catalog,
        )
    print(json.dumps(summary.__dict__, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
