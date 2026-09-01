# Design Genome Renderer: Figma visual review plan

Status: `NOT_REVIEWED`

This board is a human review surface for the 12 synthetic Visual Lab sites. It is not a production approval and no aesthetic status is inferred from automated tests.

## Source package

- Static lab: `artifacts/genome-renderer-lab/`
- Review manifest: `artifacts/genome-renderer-lab/review/manifest.json`
- DNA summaries: `artifacts/genome-renderer-lab/review/dna/`
- Desktop captures: `artifacts/genome-renderer-lab/review/desktop/`
- Mobile captures: `artifacts/genome-renderer-lab/review/mobile/`

The builder emits a `SCREENSHOTS_UNAVAILABLE` marker until real browser captures succeed. Once both 12-image cohorts exist, it records them as `CAPTURED`; this changes no aesthetic status and must never be treated as a pass.

## Board structure

Create 12 numbered columns, one per fixture. Each column contains:

1. One desktop frame at 1440 px width.
2. One mobile frame at 390 px width.
3. A compact DNA summary linked by `fixture_id` and `design_signature`.
4. One review table with the dimensions below.

Review dimensions: Identity, Composition, Typography, Color, Media, Hierarchy, Conversion, Mobile, Originality, and Coherence.

## Review protocol

Keep each dimension at `NOT_REVIEWED` until a human inspects the rendered page at desktop and mobile sizes. Record observable issues, not automated quality claims. Compare related pairs, especially the three plumbers, the two painters, the two masons, the two electricians, and the two renovators.

The final board may recommend `GO` or `NO GO` for replacing V3, but that decision must not be written back automatically by the renderer or its tests.
