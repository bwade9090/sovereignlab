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
- `SourceManifest` 2.0.0 links each `allowed` data snapshot to one catalog decision via the typed
  `rights_decision` reference, and bundle validation cross-checks scope, state, and expiry. The
  catalog itself still authorizes nothing without that validated link.

The 2026-07-16 catalog records the first two approved Bank of Korea-produced ECOS scopes. The
append-only 2026-07-17 catalog supersedes it with two narrowly approved additions: KOSIS national
monthly total CPI `101/DT_1J22003/T/T10` and OECD Korea monthly amplitude-adjusted CLI revision
series `DSD_STES_REVISIONS@DF_STES_REVISIONS/KOR.M.LI_AA.IX._T`. Catalog files contain rights
metadata only; observation responses live separately under manifest control.
