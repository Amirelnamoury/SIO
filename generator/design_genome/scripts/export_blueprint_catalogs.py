"""Export family grammar and the complete hero blueprint catalogue."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from ..blueprints import blueprint_fingerprint, blueprint_structural_distance
from ..data.components import ALL_COMPONENTS, COMPONENT_REGISTRIES


DOCS = Path("docs/design-encyclopedia")


def family_markdown() -> str:
    families = defaultdict(list)
    for component in ALL_COMPONENTS.values():
        families[component.family_id].append(component)
    lines = ["# Component families", "", "A family is a shared visual grammar. A variant is a renderer-visible structural decision, never a synonym or an ID-derived guess.", ""]
    for family_id, members in sorted(families.items()):
        first = members[0]
        spec = first.blueprint_spec
        distances = [blueprint_structural_distance(left, right).distance for index, left in enumerate(members) for right in members[index + 1:]]
        lines.extend((
            f"## `{family_id}`", "",
            f"- Purpose: {first.category} composition using `{spec.layout_model}`.",
            f"- Visual grammar: `{spec.layout_pattern}`; `{spec.edge_behavior}` edge; media intensity {spec.media_intensity}; `{spec.type_scale_role}` type role.",
            f"- Members: {', '.join(f'`{item.id}`' for item in members)}.",
            f"- Variants: {', '.join(f'`{item.variant_id}`' for item in members)}.",
            f"- Design intents: {'; '.join(item.design_intent for item in members)}",
            f"- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance {min(distances):.4f}." if distances else "- Explicit differences: single-member family.",
            f"- Ideal transitions: change pattern, edge or media intensity after `{spec.layout_pattern}`.",
            f"- Poor transitions: repeat `{spec.layout_pattern}` with the same `{spec.edge_behavior}` edge and media intensity {spec.media_intensity}.",
            f"- Mobile behavior: `{spec.mobile_spec.get('transformation', spec.mobile_spec.get('collapse_strategy', 'explicit mobile spec'))}`.", "",
        ))
    return "\n".join(lines)


def hero_markdown() -> str:
    lines = ["# Hero blueprint catalog", "", "All 50 heroes declare their own composition and design intent. Distinction is measured from renderer-visible instructions, never registry position or the component ID.", ""]
    for hero in COMPONENT_REGISTRIES["hero"].values():
        spec = hero.blueprint_spec
        lines.extend((
            f"## `{hero.id}`", "",
            f"- Family / variant: `{hero.family_id}` / `{hero.variant_id}`",
            f"- Variant source: `{hero.variant_source}`",
            f"- Design intent: {hero.design_intent}",
            f"- Fingerprint: `{blueprint_fingerprint(hero)}`",
            f"- Layout pattern: `{spec.layout_pattern}`",
            f"- Desktop composition: `{spec.layout_model}`; order `{spec.desktop_spec.get('desktop_order')}`; flow `{spec.desktop_spec['flow_direction']}`; anchor `{spec.desktop_spec['alignment_anchor']}`; frame `{spec.desktop_spec['frame_behavior']}`.",
            f"- Mobile composition: order `{spec.mobile_spec.get('mobile_order')}`; collapse `{spec.mobile_spec['collapse_strategy']}`; priority `{spec.mobile_spec['priority_anchor']}`.",
            f"- Media: `{spec.media_spec.get('media_layout')}`; intensity {spec.media_intensity}; crop `{spec.media_spec.get('image_crop_behavior')}`.",
            f"- Edge / type scale: `{spec.edge_behavior}` / `{spec.type_scale_role}`.",
            f"- Explicit architecture: `{spec.desktop_spec['flow_direction']}`, `{spec.desktop_spec['frame_behavior']}`, `{spec.mobile_spec['collapse_strategy']}` and `{spec.behavior_spec['focus_progression']}`.", "",
        ))
    return "\n".join(lines)


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "component-families.md").write_text(family_markdown() + "\n", encoding="utf-8")
    (DOCS / "hero-blueprint-catalog.md").write_text(hero_markdown() + "\n", encoding="utf-8")
    print(DOCS / "component-families.md")
    print(DOCS / "hero-blueprint-catalog.md")


if __name__ == "__main__":
    main()
