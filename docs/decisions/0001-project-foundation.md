# ADR 0001: project foundation and compute boundary

- Status: accepted
- Date: 2026-07-14

## Context

SovereignLab must deliver a public, reproducible MVP in four weeks on a Windows workstation without a training GPU. The local user-level Python installation is not reliable, Mistral's hosted fine-tuning documentation is deprecated, and the approved initial external-spend ceiling is USD 100.

## Decision

1. Standardize local development and CI on Python 3.12.
2. Maintain human-readable direct dependency ranges in `requirements.in` and an exact resolved environment in `requirements.txt`.
3. Keep offline tests, fixtures, retrieval, evaluation, and deterministic tools runnable without API credentials.
4. Wrap external model calls so responses can be recorded and replayed under documented data/licensing rules.
5. Use a short-lived rented GPU for the approved QLoRA spike; do not design around local GPU availability.
6. Test the current compact open-weight Ministral 3 3B path first, with a time-boxed fallback to supported Mistral 7B/Nemo weights.
7. License original project code under Apache-2.0, while documenting source-data and model licenses separately.

## Alternatives considered

- **Hosted fine-tuning API:** rejected as the primary path because current official documentation marks it deprecated and it provides weaker evidence of open-weight training competency.
- **Install a new system-wide Python runtime immediately:** deferred because the bundled Python 3.12 runtime can create a standard local `.venv` without changing the workstation globally.
- **Wait for local GPU access:** rejected because it conflicts with the four-week delivery window.
- **Commit downloaded documents for convenience:** rejected until source-by-source redistribution rights are documented.

## Consequences

- Contributors need Python 3.12 but no API key for normal checks.
- Training code and heavy ML dependencies will be isolated from the CPU foundation and added only when the compatibility spike begins.
- Windows is the first resolved environment; CI must verify at least one clean hosted environment before M1 closes.
- The exact fine-tuning checkpoint remains conditional on the Week-one compatibility gate.

## Revisit triggers

- The pinned environment cannot install on CI or another Python 3.12 machine.
- Ministral 3 3B QLoRA compatibility fails its time-boxed spike.
- A supported, non-deprecated Mistral fine-tuning service materially changes cost or reproducibility trade-offs.
