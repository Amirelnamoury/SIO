# Design Genome Renderer Visual Lab

Static, portable review package containing 12 explicitly synthetic fixtures, rendered by both the preserved V0.1 baseline (`sites-v0.1/`, `review/v0.1/`) and the current V0.2 engine (`sites/`, `review/v0.2/`). Run `python -m generator.genome_renderer.lab.build` from the repository root to rebuild the V0.2 side; V0.1 is a frozen historical snapshot and is never regenerated.

All aesthetic statuses start at `NOT_REVIEWED`. The forms are disabled, no provider is called at runtime, and this directory can be selected as an isolated Vercel project root.
