"""Capture the approved consolidated OECD Korea CLI revision archive once."""

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

    from sovereignlab.harvest.oecd_cli import (
        capture_oecd_cli_archive,
        load_latest_availability_ledger,
    )
    from sovereignlab.harvest.weekly import load_rights_catalog

    catalog = load_rights_catalog(repository_root)
    ledger = load_latest_availability_ledger(repository_root)
    with httpx.Client(follow_redirects=True, timeout=180.0) as client:
        summary = capture_oecd_cli_archive(
            repository_root,
            client=client,
            rights_catalog=catalog,
            availability_ledger=ledger,
        )
    print(json.dumps(summary.__dict__, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
