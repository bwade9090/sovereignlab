# Data policy

Only redistributable public benchmark records, schemas, source manifests, and small deterministic fixtures may be committed here.

Planned layout:

- `benchmark/` — reviewed task records and evidence-disjoint split manifests.
- `fixtures/` — synthetic examples and, later, small redistributable recorded responses used by offline tests.
- `manifests/` — source URL, publisher, publication date, retrieval time, checksum, language, and license notes.
- `schemas/` — generated public JSON Schema contracts; never edit these by hand.
- `raw/` — downloaded source material; ignored by Git.
- `interim/` — local extraction and transformation outputs; ignored by Git.

Do not commit a PDF, extracted full text, or API response until its redistribution basis is documented. Never place confidential, applicant, or institutional internal data in this repository.

Regenerate schemas with `python scripts/export_json_schemas.py`; tests fail if generated contracts drift from their Pydantic models.
