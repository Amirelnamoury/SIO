"""Visual rhythm evaluation independent from markup and rendering."""

from __future__ import annotations

from .models import ComponentDefinition, RhythmReport


def evaluate_rhythm(components: tuple[ComponentDefinition, ...]) -> RhythmReport:
    if not components:
        return RhythmReport(0.0, (), (), ("empty_sequence",))

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

    transitions = [abs(left - right) for left, right in zip(weights, weights[1:])]
    useful_change = sum(1 for value in transitions if value in (1, 2))
    violent_change = sum(1 for value in transitions if value >= 3)
    transition_score = useful_change / max(1, len(transitions))
    score = 0.62 + transition_score * 0.30 - len(issues) * 0.12 - violent_change * 0.04
    return RhythmReport(round(max(0.0, min(1.0, score)), 4), weights, energies, tuple(issues))
