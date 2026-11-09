# Changelog

This repository keeps a lightweight manual changelog for catalogue and viewer releases.

## [Unreleased]

- No unreleased changes recorded yet.

## [v0.3.0] - 2026-11-10

### Data
- Refreshed the TfNSW catalogue snapshot (collected 10 November 2026): **1658 → 1671 signs** (+13 new; `W3-4` split into sub-variants).
- **260 worksite signs re-referenced** from `AS1742.3` to `TS 05492`, plus title casing cleanup and additional size options.
- Re-normalized the catalogue: total normalization issues **3179 → 2979** (no existing sign regressed; new Critical mismatches are all on brand-new signs).

### Added
- ADR 0002 — cross-authority canonical sign model, backed by an empirical NSW↔SA join (499 shared Australian Standards signs). See `docs/adr/0002-cross-authority-canonical-model.md`.

### Fixed
- Scraper HTTPS verification on macOS (`CERTIFICATE_VERIFY_FAILED`) via certifi, with a graceful fallback to the system default context.
- GitHub Pages root `404`: restored the `traffic_signs/index.html` redirect to the catalogue.
- Updated the viewer disclaimer's data-collection date to 10 November 2026.

## [v0.2.0] - 2026-05-25

- Added a visible release badge to the unified viewer.
- Added a GitHub Pages deployment workflow for publishing `traffic_signs/`.
- Documented the release workflow in the repository README.

## [v0.1.0] - 2026-05-25

- Initial release baseline for the NSW Traffic Signs Catalogue repository.
- Includes the published catalogue, processing scripts, datasets, and image assets.
