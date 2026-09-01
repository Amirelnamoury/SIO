"""Visual rhythm evaluation independent from markup and rendering."""

from __future__ import annotations

from .component_relationships import sequence_affinity
from .data.components import ALL_COMPONENTS
from .models import ComponentDefinition, RhythmReport, SiteDNA


COMPONENT_FIELDS_BY_SECTION = {
    "header": "header_component", "hero": "hero_component", "services": "services_component",
    "gallery": "gallery_component", "about": "about_component", "trust": "trust_component",
    "cta": "cta_component", "contact": "contact_component", "footer": "footer_component",
}


def ordered_dna_components(dna: SiteDNA) -> tuple[ComponentDefinition, ...]:
    """Resolve components in their actual narrative order, including a nested form."""
    components: list[ComponentDefinition] = []
    for section in dna.section_order:
        field = COMPONENT_FIELDS_BY_SECTION.get(section)
        component_id = getattr(dna, field) if field else None
        if component_id:
            components.append(ALL_COMPONENTS[component_id])
        if section == "contact" and dna.form_component:
            components.append(ALL_COMPONENTS[dna.form_component])
    return tuple(components)


def evaluate_rhythm(components: tuple[ComponentDefinition, ...]) -> RhythmReport:
    if not components:
        return RhythmReport(0.0, (), (), ("empty_sequence",), 0.0)

    weights = tuple(component.visual_weight for component in components)
    energies = tuple(component.section_energy for component in components)
    issues: list[str] = []

    for index in range(len(weights) - 2):
        window = weights[index:index + 3]
        if min(window) >= 4:
            issues.append(f"three_heavy_sections:{index}")
        if max(window) <= 2:
            issues.append(f"three_quiet_sections:{index}")
    if max(weights) - min(weights) == 0 and len(weights) >= 4:
        issues.append("flat_visual_weight")
    if sum(weight >= 4 for weight in weights) > max(2, len(weights) // 2):
        issues.append("overweighted_page")
    for index, (left, right) in enumerate(zip(components, components[1:])):
        if left.profile == right.profile and left.category != right.category:
            issues.append(f"duplicate_component_pattern:{index}")

    transitions = [abs(left - right) for left, right in zip(weights, weights[1:])]
    useful_change = sum(1 for value in transitions if value in (1, 2))
    violent_change = sum(1 for value in transitions if value >= 3)
    transition_score = useful_change / max(1, len(transitions))
    relationships = sequence_affinity(components)
    score = .42 + transition_score * .24 + relationships.score * .34 - len(issues) * .10 - violent_change * .04
    return RhythmReport(round(max(0.0, min(1.0, score)), 4), weights, energies, tuple(issues), relationships.score)
