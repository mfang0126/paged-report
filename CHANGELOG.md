# Changelog

All notable changes to this project are documented here.

## [2.0.1] - 2026-11-24

### Fixed

- Playbook step images no longer carry `loading="lazy"`. Every step image is an inline base64 data URI, so lazy loading saved no request; late decoding grew the page during the first smooth scroll and the first search or contents jump landed off screen.
- The playbook search bar now renders before the cover (right after any superseded banner), so it is visible at `scrollY=0` on desktop and mobile and stays sticky while scrolling. It is still hidden in print. On narrow screens it no longer bleeds 4px past the cover card edges.

## [2.0.0] - 2026-11-24

### Added

- `playbook` template: business-intent opener, stable section anchors (explicit `id` or deterministic slug), one card per step (path, body, screenshot, warning, common mistakes, rollback), offline search bar with keyword/synonym matching, jump and highlight; search hidden in print.
- `portal` template: per-client document index grouped by status (current, draft, collapsed history), status and type badges, update dates; no script and no client-side password gate.
- `schemas/playbook.schema.json`, `schemas/portal.schema.json`, `templates/docs.css`, playbook/portal examples and `tests/test_templates_v2.py`.
- Shared `meta.robots` (default `noindex, nofollow` on every template) and `meta.superseded_by` (banner linking an old version to the current one).
- One CLI for all templates: `python3 -m generator.paged_report input.json -o out.html` dispatches on the `template` key (`report` when omitted). Local step images are inlined as base64.

### Changed

- Every output now includes a viewport meta tag and the robots meta tag.
- Narrow screens (≤860px) let table cells and tags wrap, and `.page` breaks long unbroken words, so 390px viewports have no horizontal overflow.
- Playbook/portal CSS goes through the same `_safe_css` check as reports; links starting with `//` or `\` are rejected; local step images must stay inside the input JSON folder.
- Collapsed portal history is included when printing.
- PDF guidance now uses native browser print, Chrome headless or Playwright.
- `examples/confirmation-generated.html` regenerated with the v2 head.

### Compatibility

- v1 report JSON renders unchanged apart from the added head meta tags; the v1 test suite passes unmodified.
- `qa/paged_report_qa.py` now accepts exactly one inline `<script>` in playbook output (the offline search bar); any other script, or a script in report/portal output, still fails self-containment.

## [1.2.1] - 2026-09-07 (unreleased; development/review-pending)

### Added

- Standard-library structured JSON renderer and schema-backed example input.
- Minimal PEP 621 project metadata with an explicit empty runtime dependency list.
- Release manifest defining the generic package allowlist and excluded evidence/local files.
- Minimal GitHub Actions CI workflow for pushes and pull requests; it uses the standard library for project checks and adds no `pypdf` or `jsonschema` dependency. This unreleased entry records configuration only, not a remote run.
- Review-pending appendix and delivery-contract specification covering optional data appendices, QA evidence manifests, and package handoffs; no runtime support is claimed by this entry.

### Changed

- Qualified A4, pagination, footer placement, and logical-page claims so browser/PDF output is verified rather than guaranteed.
- Documented Kimi WebBridge as the recommended interactive/PDF preview path and Playwright as a formal repeatable E2E option.
- Sanitized generic text examples and regenerated the structured HTML example from its fixture.
- Kept legacy binary preview artifacts outside the generic release allowlist until they are regenerated from sanitized fixtures.
- Hardened custom CSS checks against escaped and comment-spliced `@import`/`url()` tokens, and converted malformed grid column values into contract errors instead of raw type errors.