# Data policy

Only redistributable public benchmark records, schemas, source manifests, and small deterministic fixtures may be committed here.

Planned layout:

- `benchmark/` — reviewed task records and evidence-disjoint split manifests.
- `fixtures/` — small recorded responses used by offline tests.
- `manifests/` — source URL, publisher, publication date, retrieval time, checksum, language, and license notes.
- `raw/` — downloaded source material; ignored by Git.
- `interim/` — local extraction and transformation outputs; ignored by Git.

Do not commit a PDF, extracted full text, or API response until its redistribution basis is documented. Never place confidential, applicant, or institutional internal data in this repository.
