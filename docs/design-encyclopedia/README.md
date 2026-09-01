# Suite Artisan Design Encyclopedia

## Status and boundary

This directory is the knowledge layer for a future generative design system. It does not render HTML, does not call media providers, and is not connected to the production V3 pipeline. **V3 remains the only active Site Vitrine engine.**

The encyclopedia turns research into typed registries, compatibility rules and serializable `SiteDNA`. Its purpose is to make future design generation varied, data-aware, explainable and resistant to cloning. Passing its tests is a technical filter, never a claim that an unreviewed design is premium.

## Contents

- `reference-atlas.json`: 150+ research references with access state and inspection scope.
- `gold-standards.md`: 30 deeply reviewed references and transferable constraints.
- `components-*.md`: 260 semantic component blueprints.
- `systems.md`: color, typography, grids, silhouettes, motion, spatial and mobile systems.
- `trade-grammars.md`: six métier-specific visual/business grammars.
- `architecture.md`: SiteDNA composition, compatibility, anti-clone and failure policy.
- `truth-model.md`: factual-content boundaries and media provenance rules.
- `genome-simulation.md`: deterministic diversity evidence.

## Design Genome flow

`DesignInput -> TradeGrammar -> Archetype -> Direction -> Silhouette -> compatible systems/components -> SiteDNA -> linter/quality/anti-clone`

Missing facts or media remove incompatible sections. They are never replaced with fabricated claims or stock imagery presented as artisan work. A failed constraint produces an explicit error.

## Reproduce

```powershell
python -m generator.design_genome.scripts.design_genome_stats
python -m generator.design_genome.scripts.audit_genome_diversity
python -m generator.design_genome.scripts.export_encyclopedia
```
