"""Explainable pair and sequence relationships between component blueprints."""

from __future__ import annotations

from .models import ComponentDefinition, PairAffinityResult


CATEGORY_TRANSITION_AFFINITY = {
    ("header", "hero"): .82,
    ("hero", "services"): .78,
    ("hero", "gallery"): .62,
    ("services", "gallery"): .72,
    ("services", "about"): .78,
    ("gallery", "about"): .76,
    ("about", "trust"): .84,
    ("services", "trust"): .83,
    ("trust", "cta"): .90,
    ("about", "cta"): .78,
    ("cta", "contact"): .88,
    ("contact", "footer"): .86,
}

TRAIT_PAIR_AFFINITY = {
    frozenset(("cinematic", "editorial")): .12,
    frozenset(("cinematic", "information_dense")): -.24,
    frozenset(("minimal", "quiet")): .18,
    frozenset(("minimal", "bold")): -.10,
    frozenset(("technical", "information_dense")): .14,
    frozenset(("technical", "material")): -.04,
    frozenset(("conversion_led", "trust_led")): .16,
    frozenset(("conversion_led", "editorial")): -.06,
    frozenset(("project_led", "documentary")): .14,
    frozenset(("warm", "material")): .16,
}


def component_pair_affinity(left: ComponentDefinition, right: ComponentDefinition, archetype_traits: frozenset[str] = frozenset()) -> PairAffinityResult:
    reasons: list[str] = []
    hard = bool(left.incompatible_components & {right.id} or right.incompatible_components & {left.id})
    if hard:
        return PairAffinityResult(0.0, True, ("explicit_component_conflict",))

    score = CATEGORY_TRANSITION_AFFINITY.get((left.category, right.category), .66)
    left_spec = left.blueprint_spec
    right_spec = right.blueprint_spec
    assert left_spec is not None and right_spec is not None
    shared = left.traits & right.traits
    if shared:
        score += min(.18, len(shared) * .06)
        reasons.append(f"shared_traits:{','.join(sorted(shared))}")
    if left.family_id == right.family_id:
        score += .08 if left.variant_id != right.variant_id else -.16
        reasons.append("same_family_related_variant" if left.variant_id != right.variant_id else "same_family_same_variant")
    if left_spec.layout_pattern == right_spec.layout_pattern:
        score -= .18
        reasons.append(f"repeated_layout_pattern:{left_spec.layout_pattern}")
    if left_spec.edge_behavior == right_spec.edge_behavior and left_spec.edge_behavior in {"full_bleed", "viewport_edge", "framed"}:
        score -= .12
        reasons.append(f"repeated_edge_behavior:{left_spec.edge_behavior}")
    if left_spec.media_intensity >= 3 and right_spec.media_intensity >= 3:
        score -= .14
        reasons.append("adjacent_media_led_sections")
    elif abs(left_spec.media_intensity - right_spec.media_intensity) in {1, 2}:
        score += .06
        reasons.append("useful_media_intensity_transition")
    if left_spec.type_scale_role == right_spec.type_scale_role and left_spec.type_scale_role in {"oversized", "monumental"}:
        score -= .14
        reasons.append(f"repeated_type_scale:{left_spec.type_scale_role}")
    elif left_spec.type_scale_role != right_spec.type_scale_role:
        score += .04
        reasons.append("type_scale_transition")
    for pair, value in TRAIT_PAIR_AFFINITY.items():
        if pair <= (left.traits | right.traits):
            score += value
            reasons.append(f"trait_pair:{'+'.join(sorted(pair))}:{value:+.2f}")

    if left.visual_weight >= 4 and right.visual_weight >= 4:
        score -= .22
        reasons.append("adjacent_heavy_components")
    if left.section_energy == "heroic" and right.section_energy == "heroic":
        score -= .20
        reasons.append("adjacent_heroic_energy")
    if "technical" in right.traits and "technical" not in left.traits and "technical" not in archetype_traits:
        score -= .16
        reasons.append("technical_language_break")
    if "conversion_led" in left.traits and right.category == "gallery" and "project_led" not in right.traits:
        score -= .12
        reasons.append("conversion_flow_delayed_by_ambient_gallery")
    if left.density <= 2 and right.density >= 5:
        score -= .12
        reasons.append("abrupt_density_increase")
    if left.image_dependency >= .8 and right.image_dependency >= .8 and left.visual_weight >= 4 and right.visual_weight >= 4:
        score -= .10
        reasons.append("competing_image_dominance")
    if "quiet" in archetype_traits and ("bold" in right.traits or right.visual_weight >= 5):
        score -= .25
        reasons.append("quiet_archetype_rejects_bold_stack")
    if abs(left.density - right.density) <= 1:
        score += .05
        reasons.append("density_continuity")

    return PairAffinityResult(round(max(0.0, min(1.0, score)), 4), False, tuple(reasons))


def sequence_affinity(components: tuple[ComponentDefinition, ...], archetype_traits: frozenset[str] = frozenset()) -> PairAffinityResult:
    if len(components) < 2:
        return PairAffinityResult(1.0, False, ("single_component",))
    pairs = [component_pair_affinity(left, right, archetype_traits) for left, right in zip(components, components[1:])]
    if any(item.hard_failure for item in pairs):
        return PairAffinityResult(0.0, True, tuple(reason for item in pairs for reason in item.reasons))
    score = sum(item.score for item in pairs) / len(pairs)
    heroic_runs = sum(
        all(component.section_energy in {"strong", "heroic"} for component in components[index:index + 3])
        for index in range(max(0, len(components) - 2))
    )
    score -= heroic_runs * .10
    pattern_runs = sum(
        len({component.blueprint_spec.layout_pattern for component in components[index:index + 3]}) == 1
        for index in range(max(0, len(components) - 2))
    )
    media_runs = sum(
        all(component.blueprint_spec.media_intensity >= 3 for component in components[index:index + 3])
        for index in range(max(0, len(components) - 2))
    )
    type_runs = sum(
        all(component.blueprint_spec.type_scale_role in {"oversized", "monumental"} for component in components[index:index + 3])
        for index in range(max(0, len(components) - 2))
    )
    score -= pattern_runs * .12 + media_runs * .10 + type_runs * .10
    reasons = [reason for item in pairs for reason in item.reasons]
    if heroic_runs:
        reasons.append(f"strong_energy_runs:{heroic_runs}")
    if pattern_runs:
        reasons.append(f"layout_pattern_runs:{pattern_runs}")
    if media_runs:
        reasons.append(f"media_intensity_runs:{media_runs}")
    if type_runs:
        reasons.append(f"type_scale_runs:{type_runs}")
    return PairAffinityResult(round(max(0.0, min(1.0, score)), 4), False, tuple(reasons))
