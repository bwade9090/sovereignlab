# Rights catalogs

This directory contains append-only, owner-approved metadata about source-specific rights. It does
not contain source observations.

- Each catalog validates against `data/schemas/rights-catalog-v1.schema.json` and the canonical
  Pydantic `RightsCatalog` model.
- A new ruling or changed source term creates a new catalog with a new `catalog_id` and a
  `supersedes_catalog_id`; never rewrite an already published catalog.
- An `allowed` decision records an exact series scope, official instrument, producer/category
  evidence, intended operations, attribution template, owner, aware approval-record timestamp, and
  ADR-backed approval reference.
- The catalog is independent of `SourceManifest` 1.0. It does not authorize a raw commit until a
  accepted manifest contract is implemented with typed linkage and cross-record validation.

The first catalog records only ECOS/KOSIS rights metadata and the two approved Bank of
Korea-produced ECOS candidates. No observation endpoint response is included.
