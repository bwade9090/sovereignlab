"""Regenerate committed JSON Schema files from the Pydantic source models."""

import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))

    from sovereignlab.schemas.export import write_json_schemas

    for output_path in write_json_schemas(root / "data" / "schemas"):
        print(output_path.relative_to(root))


if __name__ == "__main__":
    main()
