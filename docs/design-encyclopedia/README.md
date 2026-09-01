# Suite Artisan Design Encyclopedia

## Status and boundary

This directory is the knowledge layer for a future generative design system. It does not render HTML, does not call media providers, and is not connected to the production V3 pipeline. **V3 remains the only active Site Vitrine engine.**

The encyclopedia turns research into typed registries, compatibility rules and serializable `SiteDNA`. Its purpose is to make future design generation varied, data-aware, explainable and resistant to cloning. Passing its tests is a technical filter, never a claim that an unreviewed design is premium.

## Index

### Research
- [Research method and deep-reference status](research-log.md)
- [30 Gold Standard dossiers](gold-standards.md)
- [Reference atlas](reference-atlas.json)

### Foundations
- [Color, typography, grid, spacing, geometry, motion and mobile](systems.md)
- [Architecture and similarity](architecture.md)

### Components
- [Header](components-header.md) · [Hero](components-hero.md) · [Services](components-services.md)
- [Gallery](components-gallery.md) · [About](components-about.md) · [Trust](components-trust.md)
- [CTA](components-cta.md) · [Contact](components-contact.md) · [Form](components-form.md) · [Footer](components-footer.md)
- [Semantic audit](component-semantic-audit.md)

### Composition and review
- [Archetypes and Photo Director](archetypes-photo-direction.md)
- [Human review guide](review-guide.md)
- [30 sample DNA cards](sample-dna/README.md)
- [10 plumber comparison](sample-plumbers.md)

### Trades, media, truth and quality
- [Trade grammars](trade-grammars.md)
- [Truth and provenance](truth-model.md)
- [Simulation evidence](genome-simulation.md)
- [Stable machine export](encyclopedia.json)

## Design Genome flow

`DesignInput -> TradeGrammar -> Archetype -> Direction -> Silhouette -> compatible systems/components -> SiteDNA -> linter/quality/anti-clone`

Missing facts or media remove incompatible sections. They are never replaced with fabricated claims or stock imagery presented as artisan work. A failed constraint produces an explicit error.

## Reproduce

```powershell
python -m generator.design_genome.scripts.design_genome_stats
python -m generator.design_genome.scripts.audit_component_semantics
python -m generator.design_genome.scripts.audit_genome_diversity
python -m generator.design_genome.scripts.export_encyclopedia
python -m generator.design_genome.scripts.export_sample_dna
```
