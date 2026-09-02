# Design Genome Renderer Visual Lab

Static, portable review package containing 12 explicitly synthetic fixtures, rendered by the preserved V0.1 baseline (`sites-v0.1/`, `review/v0.1/`), the preserved V0.2 baseline (`sites-v0.2/`, `review/v0.2/`) and the current V0.2.1 engine (`sites/`, `review/v0.2.1/`). Run `python -m generator.genome_renderer.lab.build` from the repository root to rebuild the current side; V0.1 and V0.2 are frozen historical snapshots and are never regenerated.

V0.2.1 adds `coherence-report.json` per site (does the resolved plan still read as one visual language -- see the V0.2.1 doc) alongside `dna.json`, `render-plan.json` and `visual-completeness.json`.

All aesthetic statuses start at `NOT_REVIEWED`. The forms are disabled, no provider is called at runtime, and this directory can be selected as an isolated Vercel project root.
