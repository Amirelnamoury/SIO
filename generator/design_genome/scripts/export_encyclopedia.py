"""Export human-readable encyclopedia documents from the source registries."""

from __future__ import annotations

import json
import re
from pathlib import Path

from ..archetypes import ARCHETYPES
from ..data.color_systems import COLOR_SYSTEMS
from ..data.components import COMPONENT_REGISTRIES
from ..data.grids import GRID_SYSTEMS
from ..data.page_silhouettes import PAGE_SILHOUETTES
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
"""

ARCHITECTURE = """# Design Genome architecture

## Contract

`SiteDNA` is a frozen, JSON-serializable contract. It records archetype, art direction, page silhouette, semantic color and type systems, grid, spacing, geometry, photo direction, component blueprints, motion, spatial fallback, mobile personality, section order and a stable signature. The seed is retained for reproducibility but excluded from the signature.

## Compatibility before randomness

Selection uses hard constraints first: required business data, required artisan media, allowed provenance and component conflicts. Soft scoring then considers trade affinity, archetype, art direction, density and conversion intent. Seeded variation only breaks ties inside the compatible set. If no eligible candidate remains, generation fails explicitly.

## Narrative and rhythm

Thirty silhouettes describe narrative order rather than interchangeable stacks. The rhythm evaluator inspects visual weight and energy, rejects runs of three heavy sections, warns about flat pages, and rewards measured transitions. Sections absent for lack of evidence are removed before the final order is serialized.

## Anti-clone model

Similarity is computed across six explainable distances: structure, typography, color, components, narrative and photo strategy. Candidate generation compares against history and rejects high similarity. The default threshold is intentionally stricter than exact signature uniqueness.

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

## Missing information

A missing section is valid. An invented section is not. Galleries may disappear when no usable image exists; trust strips disappear when no verified fact exists; contact/form/CTA components disappear without a verified contact channel.

## Photo Director

The 192 photo profiles cover six trades, eight art directions and four section roles. Stock is permitted for ambient or illustrative roles only. Project evidence, before/after and artisan casebooks require artisan-owned media. Provider choice and downloading remain outside this package and outside public pages.
"""


def write(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def export_components() -> None:
    for category, registry in COMPONENT_REGISTRIES.items():
        lines = [f"# {category.title()} component blueprints", "", f"Count: {len(registry)}", "", "| ID | Traits | Required data | Required media | Density | Weight | Mobile |", "|---|---|---|---|---:|---:|---|"]
        for item in registry.values():
            lines.append(
                f"| `{item.id}` | {', '.join(sorted(item.traits))} | {', '.join(sorted(item.required_data)) or '-'} | "
                f"{', '.join(sorted(item.required_media)) or '-'} | {item.density} | {item.visual_weight} | `{item.mobile_variant}` |"
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
    lines = ["# 30 Gold Standards", "", "These references received manual visual review. The transferable unit is a constraint or pattern, never a copied page.", "", "| # | Reference | Sector | Observed strength |", "|---:|---|---|---|"]
    for number, name, url, sector, observation in rows[:30]:
        lines.append(f"| {number} | [{name}]({url}) | {sector.strip()} | {observation.strip()} |")
    lines.extend(("", "## Promotion criteria", "", "A broad-atlas reference becomes Gold only after desktop/mobile visual inspection, identifiable transferable constraints, explicit cautions, and separation between observed fact and design interpretation."))
    write(DOCS / "gold-standards.md", "\n".join(lines))


def export_research_report() -> None:
    atlas = json.loads((DOCS / "reference-atlas.json").read_text(encoding="utf-8"))
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
        "The deep pass reused and expanded the 30 manually reviewed references documented in the V3 design bible. Markup signals such as viewport, headings, images and forms supplement visual notes but do not replace visual inspection.", "",
        "## Cross-corpus findings", "",
        "1. Distinctive sites begin with silhouette and narrative order, not palette swaps.",
        "2. Strong heroes vary by image role, crop, typography, entry motion and conversion intent.",
        "3. Trust is most credible when evidence sits next to the decision it supports.",
        "4. Mobile needs its own information priority and action behavior.",
        "5. Spatial and motion systems work best as explanatory capabilities with explicit fallbacks.",
        "6. Photography needs provenance and section roles; stock must never masquerade as completed work.",
    ]
    write(DOCS / "research-log.md", "\n".join(lines))


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    write(DOCS / "README.md", README)
    write(DOCS / "architecture.md", ARCHITECTURE)
    write(DOCS / "truth-model.md", TRUTH)
    export_components()
    export_systems()
    export_trades()
    export_archetypes_and_photo()
    export_gold()
    export_research_report()
    print(f"Exported encyclopedia to {DOCS}")


if __name__ == "__main__":
    main()
