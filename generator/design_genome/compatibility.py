"""Hard constraints and soft affinity scoring for Design Genome choices."""

from __future__ import annotations

from .models import CompatibilityResult, ComponentDefinition, DesignInput, SiteArchetype


def evaluate_component(
    component: ComponentDefinition,
    design_input: DesignInput,
    archetype: SiteArchetype,
    art_direction: str,
    selected_ids: tuple[str, ...] = (),
) -> CompatibilityResult:
    failures: list[str] = []
    reasons: list[str] = []

    missing_data = component.required_data - design_input.available_data
    missing_media = component.required_media - design_input.media.available_roles()
    if missing_data:
        failures.append(f"missing_data:{','.join(sorted(missing_data))}")
    if missing_media:
        failures.append(f"missing_media:{','.join(sorted(missing_media))}")
    incompatible = component.incompatible_components.intersection(selected_ids)
    if incompatible:
        failures.append(f"incompatible_components:{','.join(sorted(incompatible))}")

    if component.allowed_media_sources == frozenset({"artisan"}) and not (
        design_input.media.artisan_photos or design_input.media.project_photos
    ):
        failures.append("artisan_media_required")

    score = 0.50
    if archetype.id in component.compatible_archetypes:
        score += 0.18
        reasons.append("archetype_affinity")
    elif component.compatible_archetypes:
        score -= 0.06
    if art_direction in component.compatible_directions:
        score += 0.16
        reasons.append("direction_affinity")
    elif component.compatible_directions:
        score -= 0.05
    score += component.trade_affinity.get(design_input.trade, 0.0) * 0.12
    score += (1.0 - abs(component.density - archetype.target_density) / 5.0) * 0.08
    score += (1.0 - abs(component.conversion_score - archetype.conversion_intensity)) * 0.08

    if failures:
        return CompatibilityResult(False, 0.0, tuple(failures), tuple(reasons))
    return CompatibilityResult(True, round(max(0.0, min(1.0, score)), 4), (), tuple(reasons))


def sequence_compatibility(components: tuple[ComponentDefinition, ...]) -> CompatibilityResult:
    failures: list[str] = []
    selected = {component.id for component in components}
    for component in components:
        conflicts = component.incompatible_components.intersection(selected)
        if conflicts:
            failures.append(f"{component.id}:{','.join(sorted(conflicts))}")
    allowed = not failures
    return CompatibilityResult(allowed, 1.0 if allowed else 0.0, tuple(failures))
