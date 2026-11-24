"""Write or check the committed tier-2 probe set, and print its composition.

Every gold is computed by the resolver against an admitted evidence version, so the committed
file must equal a fresh generation. Run with ``--check`` to confirm that and with ``--write``
after changing the generator.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sovereignlab.probes import (  # noqa: E402
    EDITION_SPLITS,
    PROBE_SET_PATH,
    generate_probe_records,
    render_probe_set,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write the committed probe set")
    mode.add_argument("--check", action="store_true", help="fail if the committed set differs")
    arguments = parser.parse_args()

    records = generate_probe_records(ROOT)
    payload = render_probe_set(records)
    path = ROOT / PROBE_SET_PATH
    if arguments.write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    elif not path.is_file() or path.read_bytes() != payload:
        raise SystemExit(f"committed probe set drift: {PROBE_SET_PATH}")

    print(f"{PROBE_SET_PATH}: {len(records)} records ({len(records) // 2} Korean/English pairs)")
    print("edition  split  as-of value  revision trap  future period")
    for edition, split in sorted(EDITION_SPLITS.items()):
        # Each edition is the only one in its split.
        in_split = [record for record in records if record.split is split]
        values = [record for record in in_split if record.tool_expectations]
        traps = sum("revision-trap" in record.tags for record in values)
        futures = len(in_split) - len(values)
        print(f"{edition}   {split.value:<5}  {len(values):>11}  {traps:>13}  {futures:>13}")


if __name__ == "__main__":
    main()
