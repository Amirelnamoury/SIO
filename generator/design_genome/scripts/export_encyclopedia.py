"""Export human-readable encyclopedia documents from the source registries."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, is_dataclass
from pathlib import Path

from ..archetypes import ARCHETYPES
from ..component_relationships import CATEGORY_TRANSITION_AFFINITY, TRAIT_PAIR_AFFINITY
from ..data.color_systems import COLOR_SYSTEMS
from ..data.components import COMPONENT_REGISTRIES
from ..data.deep_references import ADDITIONAL_DEEP_REFERENCES, sector_guidance
from ..data.foundations import GEOMETRY_SYSTEMS, SPACING_SYSTEMS
from ..data.grids import GRID_SYSTEMS
from ..data.page_silhouettes import PAGE_SILHOUETTES
from ..data.research_seed import GOLD_REFERENCES
from ..data.systems import MOBILE_PERSONALITIES, MOTION_SYSTEMS, SPATIAL_SYSTEMS
from ..data.trade_grammar import TRADE_GRAMMARS
from ..data.typography_systems import TYPOGRAPHY_SYSTEMS
from ..photo_direction import PHOTO_DIRECTIONS


ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "docs" / "design-encyclopedia"


README = """# Suite Artisan Design Encyclopedia

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
- [Component families](component-families.md)
- [Hero blueprint catalog](hero-blueprint-catalog.md)

### Composition and review
- [Archetypes and Photo Director](archetypes-photo-direction.md)
- [Human review guide](review-guide.md)
- [30 sample DNA cards](sample-dna/README.md)
- [10 plumber comparison](sample-plumbers.md)
- [Blueprint differentiation audit](blueprint-differentiation-audit.md)
- [Renderer readiness](renderer-readiness.md)

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
python -m generator.design_genome.scripts.audit_blueprint_differentiation
python -m generator.design_genome.scripts.check_renderer_readiness
python -m generator.design_genome.scripts.audit_genome_diversity
python -m generator.design_genome.scripts.export_blueprint_catalogs
python -m generator.design_genome.scripts.export_encyclopedia
python -m generator.design_genome.scripts.export_sample_dna
```
"""

ARCHITECTURE = """# Design Genome architecture

## Contract

`SiteDNA` is a frozen, JSON-serializable contract. It records archetype, art direction, page silhouette, semantic color and type systems, grid, spacing, geometry, photo direction, component blueprints, motion, spatial fallback, mobile personality and section order. `design_signature` spans visual styling; `composition_signature` spans component family/variant/fingerprint, order, layout/edge/media/type rhythms and structural systems. The seed is retained for reproducibility but excluded from both signatures.

## Compatibility before randomness

Selection uses hard constraints first: required business data, required artisan media, allowed provenance and component conflicts. Soft scoring then considers trade affinity, archetype, art direction, density and conversion intent. Seeded variation only breaks ties inside the compatible set. If no eligible candidate remains, generation fails explicitly.

## Narrative and rhythm

Thirty silhouettes describe narrative order rather than interchangeable stacks. The rhythm evaluator inspects visual weight, energy, layout pattern, edge behavior, media intensity and type-scale role. It penalizes repeated structural runs and rewards measured transitions. Sections absent for lack of evidence are removed before the final order is serialized.

## Anti-clone model

Similarity is structure-first: blueprint distance, family relation and layout/edge/media/type rhythm carry most of the weight; component IDs and color carry little. A palette-only change therefore cannot disguise a structural clone, while two IDs with the same blueprint remain near-identical. Bands are: 0-.40 clearly distinct, .40-.60 related, .60-.75 visually similar, .75-.84 near clone and above .84 rejected. These engineering thresholds were calibrated through cohorts and remain subject to human rendered review.

## Blueprint differentiation

Every component declares a shared family and an explicit `StructuralVariantSpec` with design intent, desktop flow/anchor/frame, mobile collapse/priority and focus progression. Registry position, component-name inference, hashing and seeds never select a structure. `blueprint_fingerprint()` hashes only the merged renderer-visible structure; `design_intent`, identity labels and notes remain documentation metadata.

## Quality model

The score covers coherence, hierarchy, readability, contrast, rhythm, conversion clarity, content fit, media fit, business fit, mobile compatibility, originality and over/under-design risk. It is a preflight engineering score. Human desktop/mobile review remains mandatory before any production renderer integration.

## Isolation

No production module imports `generator.design_genome`. The package has no renderer, no route, no database migration, no provider call and no publishing action. A future integration should consume `SiteDNA` behind an explicit feature boundary and preserve the candidate/preview/adopt/publish workflow.
"""

TRUTH = """# Data truth and media provenance

## Four classes

1. `fact`: a claim backed by an explicit artisan field.
2. `derived_fact`: a transparent transformation of supplied data.
3. `safe_generic_copy`: a non-factual prompt such as “Parlons de votre projet”.
4. `forbidden_invention`: a factual assertion whose required source field is absent.

The classifier detects claims about experience, projects, clients, response time, ratings, RGE, insurance, guarantees, emergency service and certifications. The component registry independently requires the data behind reviews, statistics, badges, insurance, partners, brands, awards, delays, availability and service areas.

`ClaimRequirement` is the structured authority behind those decisions. A future copy layer must ask `can_render_claim(claim_type, facts)` before composing the sentence; text-pattern classification is a secondary audit guard, never the sole authorization.

## Missing information

A missing section is valid. An invented section is not. Galleries may disappear when no usable image exists; trust strips disappear when no verified fact exists; contact/form/CTA components disappear without a verified contact channel.

## Photo Director

The 192 photo profiles cover six trades, eight art directions and four section roles. Stock is permitted for ambient or illustrative roles only. Project evidence, before/after and artisan casebooks require artisan-owned media. Provider choice and downloading remain outside this package and outside public pages.

`can_use_media_wording(source, role, wording_role)` rejects stock paired with project, realization, worksite, before/after, team or selected-project wording.
"""


def write(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def export_components() -> None:
    for category, registry in COMPONENT_REGISTRIES.items():
        lines = [f"# {category.title()} component blueprints", "", f"Count: {len(registry)}", "", "Every ID is opaque: semantics come from the explicit profile, constraints and resolved blueprint spec.", "", "| ID | Profile / layout | Traits | Data (all / any) | Media (all / any) | Density | Weight | Mobile / fallback |", "|---|---|---|---|---|---:|---:|---|"]
        for item in registry.values():
            spec = item.blueprint_spec
            lines.append(
                f"| `{item.id}` | `{item.profile}` / `{spec.layout_model}` | {', '.join(sorted(item.traits))} | "
                f"{', '.join(sorted(item.required_data)) or '-'} / {', '.join(sorted(item.required_any_data)) or '-'} | "
                f"{', '.join(sorted(item.required_media)) or '-'} / {', '.join(sorted(item.required_any_media)) or '-'} | "
                f"{item.density} | {item.visual_weight} | `{item.mobile_variant}` / {spec.fallback_strategy} |"
            )
        write(DOCS / f"components-{category}.md", "\n".join(lines))


def export_systems() -> None:
    lines = ["# Design systems", "", "## Semantic color systems", "", "| ID | Mode | Contrast | Trade affinities | Type compatibility |", "|---|---|---:|---|---|"]
    for item in COLOR_SYSTEMS.values():
        trades = ", ".join(f"{key}:{value:.2f}" for key, value in sorted(item.trade_affinities.items()))
        lines.append(f"| `{item.id}` | {item.mode} | {item.contrast_score:.2f} | {trades} | {', '.join(item.compatible_typography)} |")
    lines.extend(("", "## Typography systems", "", "| ID | Category | Display / body | Hero px | Measure | Traits |", "|---|---|---|---|---:|---|"))
    for item in TYPOGRAPHY_SYSTEMS.values():
        lines.append(f"| `{item.id}` | {item.category} | {item.display_family} / {item.body_family} | {item.hero_size_range[0]}-{item.hero_size_range[1]} | {item.body_measure} | {', '.join(sorted(item.traits))} |")
    lines.extend(("", "## Grid systems", "", "| ID | Columns | Max width | Gutter | Mobile transformation | Traits |", "|---|---:|---:|---:|---|---|"))
    for item in GRID_SYSTEMS.values():
        lines.append(f"| `{item.id}` | {item.columns} | {item.max_width} | {item.gutter} | `{item.mobile_transformation}` | {', '.join(sorted(item.traits))} |")
    lines.extend(("", "## Page silhouettes", "", "| ID | Narrative | Minimum data | Images | Mobile transformation |", "|---|---|---|---|---|"))
    for item in PAGE_SILHOUETTES.values():
        lines.append(f"| `{item.id}` | {' -> '.join(item.sections)} | {', '.join(sorted(item.minimum_data)) or '-'} | {item.expected_image_count[0]}-{item.expected_image_count[1]} | `{item.mobile_transformation}` |")
    lines.extend(("", "## Spacing systems", "", "| ID | Section | Component | Text | Grid | Hero | Mobile |", "|---|---|---:|---:|---:|---|---:|"))
    for item in SPACING_SYSTEMS.values():
        lines.append(f"| `{item.id}` | {item.section_padding[0]}-{item.section_padding[1]} | {item.component_gap} | {item.text_gap} | {item.grid_gap} | {item.hero_padding[0]}-{item.hero_padding[1]} | {item.mobile_multiplier} |")
    lines.extend(("", "## Geometry systems", "", "| ID | Radius | Borders / lines | Shape language | Images | Buttons | Cards |", "|---|---:|---|---|---|---|---|"))
    for item in GEOMETRY_SYSTEMS.values():
        lines.append(f"| `{item.id}` | {item.radius} | {item.border_behavior} / {item.line_behavior} | {item.shape_language} | {item.image_corner_behavior} | {item.button_shape} | {item.card_shape} |")
    lines.extend(("", "## Motion systems", "", "| ID | Intensity | Cost | Techniques | Reduced-motion fallback |", "|---|---:|---:|---|---|"))
    for item in MOTION_SYSTEMS.values():
        lines.append(f"| `{item.id}` | {item.intensity} | {item.performance_cost} | {', '.join(item.techniques) or '-'} | `{item.reduced_motion_fallback}` |")
    lines.extend(("", "## Spatial systems", "", "| ID | Level | Cost | Techniques | Mobile fallback |", "|---|---:|---:|---|---|"))
    for item in SPATIAL_SYSTEMS.values():
        lines.append(f"| `{item.id}` | {item.level} | {item.performance_cost} | {', '.join(item.techniques) or '-'} | `{item.mobile_fallback}` |")
    lines.extend(("", "## Mobile personalities", "", "| ID | Navigation | Hero | Gallery | CTA | Motion |", "|---|---|---|---|---|---|"))
    for item in MOBILE_PERSONALITIES.values():
        lines.append(f"| `{item.id}` | {item.navigation} | {item.hero_adaptation} | {item.gallery_behavior} | {item.cta_behavior} | {item.motion_policy} |")
    write(DOCS / "systems.md", "\n".join(lines))


def export_trades() -> None:
    lines = ["# Trade grammars", "", "Each grammar combines user fears, evidence, photographic opportunity and cliché avoidance. It changes probabilities, never business facts.", ""]
    for item in TRADE_GRAMMARS.values():
        lines.extend((
            f"## {item.trade.title()}", "",
            f"- Business intents: {', '.join(item.business_intents)}",
            f"- Customer fears: {', '.join(item.customer_fears)}",
            f"- Trust signals: {', '.join(item.trust_signals)}",
            f"- Photo opportunities: {', '.join(item.photo_opportunities)}",
            f"- Photo risks: {', '.join(item.photo_risks)}",
            f"- Clichés to avoid: {', '.join(item.visual_cliches)}",
            f"- Preferred archetypes: {', '.join(item.preferred_archetypes)}",
            f"- Compatible directions: {', '.join(item.compatible_directions)}", "",
        ))
    write(DOCS / "trade-grammars.md", "\n".join(lines))


def export_archetypes_and_photo() -> None:
    lines = ["# Archetypes and Photo Director", "", "## Site archetypes", "", "| ID | Intents | Traits | Preferred silhouettes | Directions |", "|---|---|---|---|---|"]
    for item in ARCHETYPES.values():
        lines.append(f"| `{item.id}` | {', '.join(sorted(item.business_intents))} | {', '.join(sorted(item.traits))} | {', '.join(item.preferred_silhouettes)} | {', '.join(item.preferred_directions)} |")
    lines.extend(("", "## Photo Director matrix", "", f"Profiles: {len(PHOTO_DIRECTIONS)} = 6 trades x 8 directions x 4 sections.", "", "| Trade | Direction | Section | Orientation | Allowed roles | First query |", "|---|---|---|---|---|---|"))
    for item in PHOTO_DIRECTIONS.values():
        lines.append(f"| {item.trade} | `{item.art_direction}` | {item.section} | {item.orientation} | {', '.join(sorted(item.allowed_roles))} | {item.queries[0]} |")
    write(DOCS / "archetypes-photo-direction.md", "\n".join(lines))


def export_gold() -> None:
    bible = (ROOT / "docs" / "design-bible-v3.md").read_text(encoding="utf-8")
    rows = re.findall(r"^\|\s*(\d+)\s*\|\s*\[([^]]+)\]\(([^)]+)\)\s*\|\s*([^|]+)\|\s*([^|]+)\|", bible, re.M)
    observations_by_url = {url.rstrip("/"): observation.strip() for _number, _name, url, _sector, observation in rows}
    lines = ["# 30 Gold Standards", "", "These references received a manual desktop review recorded in the V3 design bible. Each dossier separates the recorded observation from interpretation. Mobile was not inspected and is never inferred.", ""]
    for number, (name, url, sector) in enumerate(GOLD_REFERENCES, 1):
        guide = sector_guidance(sector.strip())
        observed = observations_by_url.get(url.rstrip("/"), "Desktop review recorded, but the concise observation could not be matched; no additional visual detail is inferred.")
        lines.extend((
            f"## {number}. {name}", "",
            f"- **REFERENCE:** {name}", f"- **URL:** {url}", f"- **SECTOR:** {sector.strip()}",
            f"1. **FIRST IMPRESSION:** {observed}",
            f"2. **PAGE SILHOUETTE:** Interpretation from the desktop note: {observed.split(',')[0].strip().lower()}.",
            "3. **HEADER:** Use only the navigation behavior explicitly present in the recorded observation; other header details were not recorded.",
            "4. **HERO:** The opening device named in the observation is the transferable structural signal; exact proportions were not measured.",
            "5. **GRID:** Grid coordinates were not measured; retain only the observed split, catalogue, collage or full-frame behavior where stated.",
            "6. **TYPOGRAPHY:** Typography is described only where the desktop note explicitly names scale, serif/sans behavior or placement.",
            "7. **COLOR:** Exact tokens and contrast pairs were not sampled; no palette should be copied.",
            "8. **PHOTOGRAPHY:** Preserve the observed image role, not the source imagery or project claims.",
            "9. **CONTENT DENSITY:** Interpret density relative to the recorded opening and catalogue rhythm; no content count was measured.",
            "10. **SECTION RHYTHM:** Reuse the contrast between the observed dominant and quiet moments, not the original section order.",
            f"11. **CTA / BUSINESS CLARITY:** {guide['business_clarity']}",
            "12. **MOTION:** Motion details were not systematically recorded; do not infer an animation system from a static observation.",
            "13. **MOBILE OBSERVATIONS:** mobile not inspected.",
            f"14. **DISTINCTIVE DEVICES:** {observed}",
            "15. **WHAT SUITE ARTISAN CAN LEARN:** Translate the distinctive device into a constraint for silhouette, hierarchy or media role.",
            "16. **WHAT SUITE ARTISAN MUST NOT COPY:** Brand identity, source layout coordinates, imagery, wording, projects and claims.",
            f"17. **GOOD FIT FOR WHICH TRADES:** {guide['good_fit']}.",
            f"18. **POOR FIT FOR WHICH TRADES:** {guide['poor_fit']}.",
            "19. **REUSABLE PRINCIPLES:** A page should remain recognizable by hierarchy and rhythm before color is applied.",
            f"20. **CAUTIONS:** {guide['caution']}", "",
        ))
    lines.extend(("## Promotion criteria", "", "Gold means a recorded manual desktop observation, not complete responsive certification. A future promotion to mobile-inspected requires explicit viewport evidence and a dated review."))
    write(DOCS / "gold-standards.md", "\n".join(lines))


def export_research_report() -> None:
    atlas = json.loads((DOCS / "reference-atlas.json").read_text(encoding="utf-8"))
    deep_status_path = DOCS / "deep-reference-status.json"
    deep_status = json.loads(deep_status_path.read_text(encoding="utf-8")) if deep_status_path.exists() else {"references": []}
    counts = atlas["counts"]
    lines = [
        "# Research log", "",
        f"Research date: {atlas['researched_at']}", "",
        f"- Total references recorded: {counts['total']}",
        f"- Live target checks successful: {counts['accessible']}",
        f"- Broad directory-index observations: {counts['directory_indexed']}",
        f"- Current failures/inaccessible: {counts['failed_or_inaccessible']}",
        f"- Gold Standards: {counts['gold_standards']}", "",
        "## Method", "",
        "The broad pass used live editorial category results across architecture, construction, furniture, hospitality, property, commerce, technology, education and interactive work. Direct target URLs were checked where available. Rate limiting, robots rules and network failures are preserved in the atlas instead of being interpreted as design rejection.", "",
        "The deep pass expanded the 30 manually reviewed references documented in the V3 design bible and selected 20 additional official sites for focused HTML research. Markup signals supplement visual notes but never replace visual inspection.", "",
        "## Deep-reference status", "",
        "| Reference | Sector | Indexed | HTML inspected | Visual inspected | Mobile inspected | Gold | Focus |", "|---|---|---|---|---|---|---|---|",
    ]
    gold_names = {item[0] for item in GOLD_REFERENCES}
    for item in atlas["references"]:
        if item["name"] in gold_names:
            lines.append(f"| {item['name']} | {item['sector']} | yes | {'yes' if item['status'] == 'accessible' else 'previous check only'} | yes | no | yes | desktop observation dossier |")
    by_name = {item["name"]: item for item in deep_status["references"]}
    for name, url, sector, focus in ADDITIONAL_DEEP_REFERENCES:
        status = by_name.get(name, {})
        lines.append(f"| [{name}]({url}) | {sector} | yes | {'yes' if status.get('html_inspected') else 'no'} | no | no | no | {focus} |")
    lines.extend((
        "", "## Cross-corpus findings", "",
        "1. Distinctive sites begin with silhouette and narrative order, not palette swaps.",
        "2. Strong heroes vary by image role, crop, typography, entry motion and conversion intent.",
        "3. Trust is most credible when evidence sits next to the decision it supports.",
        "4. Mobile needs its own information priority and action behavior.",
        "5. Spatial and motion systems work best as explanatory capabilities with explicit fallbacks.",
        "6. Photography needs provenance and section roles; stock must never masquerade as completed work.",
    ))
    write(DOCS / "research-log.md", "\n".join(lines))


REVIEW_GUIDE = """# Human architecture review guide

This checklist evaluates knowledge contracts, not rendered beauty. Record evidence and mark unknowns instead of filling gaps.

## Palette
- Check primary, secondary, muted, inverse, brand-background, focus and CTA-state contrast.
- Inspect light/dark material logic, image compatibility and prohibited combinations.
- Reject a palette that is merely a hue swap without semantic token behavior.

## Typography
- Verify availability and fallbacks on target platforms.
- Review hero wrapping, body measure, mobile scale, numeric treatment and dense/airy modes.
- Reject negative tracking, unreadable body text or more than three active families.

## Hero blueprint
- Read its desktop, mobile, media, content, behavior and fallback specs.
- Confirm media provenance, orientation, crop, title width, CTA placement and no-media behavior.
- Compare the actual rendering to the blueprint rather than to the component ID.

## Silhouette
- Verify opening, middle and closing business goals.
- Check fixed/substitutable sections, evidence dependencies, mobile narrative and rhythm transitions.
- Reject repeated heroic weight or a sequence that delays the primary business task.

## SiteDNA
- Confirm facts and media satisfy every hard constraint.
- Read the decision trace and rejected candidates.
- Compare silhouette, hero, services, order, grid and type before judging palette novelty.
- Audit desktop and mobile separately; run reduced-motion and missing-data scenarios.
- Human verdict: accept, revise, or reject, with evidence. A quality score is never a beauty score.
"""


def _jsonable(value):
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_jsonable(item) for item in sorted(value) if isinstance(value, (set, frozenset))] if isinstance(value, (set, frozenset)) else [_jsonable(item) for item in value]
    return value


def export_machine_readable() -> None:
    payload = {
        "schema_version": "1.2",
        "status": "experimental_knowledge_layer_not_connected_to_production",
        "counts": {category: len(registry) for category, registry in COMPONENT_REGISTRIES.items()},
        "registries": {category: _jsonable(registry) for category, registry in COMPONENT_REGISTRIES.items()},
        "systems": {
            "colors": _jsonable(COLOR_SYSTEMS), "typography": _jsonable(TYPOGRAPHY_SYSTEMS),
            "grids": _jsonable(GRID_SYSTEMS), "spacing": _jsonable(SPACING_SYSTEMS),
            "geometry": _jsonable(GEOMETRY_SYSTEMS), "silhouettes": _jsonable(PAGE_SILHOUETTES),
            "motion": _jsonable(MOTION_SYSTEMS), "spatial": _jsonable(SPATIAL_SYSTEMS),
            "mobile": _jsonable(MOBILE_PERSONALITIES), "archetypes": _jsonable(ARCHETYPES),
            "trades": _jsonable(TRADE_GRAMMARS), "photo_directions": _jsonable(PHOTO_DIRECTIONS),
        },
        "compatibility": {
            "category_transition_affinity": {f"{left}->{right}": value for (left, right), value in sorted(CATEGORY_TRANSITION_AFFINITY.items())},
            "trait_pair_affinity": {"+".join(sorted(pair)): value for pair, value in TRAIT_PAIR_AFFINITY.items()},
        },
    }
    write(DOCS / "encyclopedia.json", json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    write(DOCS / "README.md", README)
    write(DOCS / "architecture.md", ARCHITECTURE)
    write(DOCS / "truth-model.md", TRUTH)
    write(DOCS / "review-guide.md", REVIEW_GUIDE)
    export_components()
    export_systems()
    export_trades()
    export_archetypes_and_photo()
    export_gold()
    export_research_report()
    export_machine_readable()
    print(f"Exported encyclopedia to {DOCS}")


if __name__ == "__main__":
    main()
