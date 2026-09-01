"""Declarative helpers for component blueprints.

Identifiers are opaque keys. This module never inspects an ID to infer business,
media, compatibility or layout semantics.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from ...models import ComponentBlueprintSpec, ComponentDefinition


CONTENT_ZONES = {
    "header": ("brand", "navigation", "primary_action", "secondary_information"),
    "hero": ("eyebrow", "title", "supporting_copy", "actions", "media"),
    "services": ("section_title", "service_items", "service_detail", "service_action"),
    "gallery": ("section_title", "media_items", "captions", "project_context"),
    "about": ("section_title", "narrative", "supporting_media", "verified_facts"),
    "trust": ("verified_facts", "fact_labels", "evidence_source"),
    "cta": ("prompt", "primary_action", "secondary_action", "supporting_context"),
    "contact": ("contact_details", "form", "context", "privacy"),
    "footer": ("brand", "navigation", "legal", "contact", "optional_action"),
    "form": ("fields", "consent", "submit", "status", "error_summary"),
}


def blueprint(
    layout_model: str,
    content_alignment: str,
    *,
    desktop: Mapping[str, Any],
    mobile: Mapping[str, Any],
    media: Mapping[str, Any],
    content: Mapping[str, Any],
    behavior: Mapping[str, Any],
    fallback: str,
) -> ComponentBlueprintSpec:
    return ComponentBlueprintSpec(
        schema_version="component-blueprint-1.1",
        layout_model=layout_model,
        content_alignment=content_alignment,
        desktop_spec=dict(desktop),
        mobile_spec=dict(mobile),
        media_spec=dict(media),
        content_spec=dict(content),
        behavior_spec=dict(behavior),
        fallback_strategy=fallback,
    )


def hero_blueprint(
    layout_model: str,
    *,
    alignment: str,
    media_layout: str,
    media_count: tuple[int, int],
    orientations: tuple[str, ...],
    crop: str,
    spans: tuple[int, int],
    desktop_order: tuple[str, ...],
    mobile_order: tuple[str, ...],
    title_scale: str = "display_l",
    max_title_width: int = 18,
    overlay: str = "none",
    background: str = "canvas",
    supports_no_media: bool = False,
    supports_stock: bool = True,
    supports_artisan: bool = True,
    mobile_media: str = "subject_safe_crop",
    mobile_title: str = "reduce_scale_preserve_hierarchy",
    motion: tuple[str, ...] = ("soft_fade",),
    fallback: str = "replace media with a neutral material or typographic composition",
) -> ComponentBlueprintSpec:
    return blueprint(
        layout_model,
        alignment,
        desktop={
            "grid_columns": 12,
            "content_span": spans[0],
            "media_span": spans[1],
            "desktop_order": desktop_order,
            "min_height_behavior": "min(82vh, 880px)",
            "section_padding_behavior": "spacing_system.hero_padding",
            "overlap_behavior": "controlled" if "layer" in layout_model or "collage" in layout_model else "none",
        },
        mobile={
            "mobile_order": mobile_order,
            "media_behavior": mobile_media,
            "title_behavior": mobile_title,
            "min_height_behavior": "content_driven_with_viewport_cap",
        },
        media={
            "media_layout": media_layout,
            "media_count_min": media_count[0],
            "media_count_max": media_count[1],
            "preferred_orientations": orientations,
            "image_crop_behavior": crop,
            "media_span": spans[1],
            "overlay_behavior": overlay,
            "background_behavior": background,
            "supports_no_media": supports_no_media,
            "supports_stock_media": supports_stock,
            "supports_artisan_media": supports_artisan,
        },
        content={
            "title_position": "primary_content_zone",
            "cta_position": "after_supporting_copy",
            "supporting_copy_position": "adjacent_to_title",
            "eyebrow_position": "before_title",
            "max_title_width_ch": max_title_width,
            "title_scale": title_scale,
        },
        behavior={"motion_capabilities": motion, "interaction_priority": "content_before_effect"},
        fallback=fallback,
    )


def component_profile(
    spec: ComponentBlueprintSpec,
    *,
    traits: Sequence[str],
    required_data: Sequence[str] = (),
    required_any_data: Sequence[str] = (),
    required_media: Sequence[str] = (),
    required_any_media: Sequence[str] = (),
    allowed_media_sources: Sequence[str] = ("artisan", "stock", "none"),
    compatible_archetypes: Sequence[str] = (),
    compatible_directions: Sequence[str] = (),
    incompatible_components: Sequence[str] = (),
    density: int = 3,
    visual_weight: int = 3,
    section_energy: str = "medium",
    mobile_variant: str = "stack_priority_order",
    trade_affinity: Mapping[str, float] | None = None,
    conversion_score: float = .5,
    editorial_score: float = .5,
    image_dependency: float = 0.0,
    notes: str = "",
) -> dict[str, Any]:
    return {
        "spec": spec,
        "traits": tuple(traits),
        "required_data": tuple(required_data),
        "required_any_data": tuple(required_any_data),
        "required_media": tuple(required_media),
        "required_any_media": tuple(required_any_media),
        "allowed_media_sources": tuple(allowed_media_sources),
        "compatible_archetypes": tuple(compatible_archetypes),
        "compatible_directions": tuple(compatible_directions),
        "incompatible_components": tuple(incompatible_components),
        "density": density,
        "visual_weight": visual_weight,
        "section_energy": section_energy,
        "mobile_variant": mobile_variant,
        "trade_affinity": dict(trade_affinity or {}),
        "conversion_score": conversion_score,
        "editorial_score": editorial_score,
        "image_dependency": image_dependency,
        "notes": notes,
    }


def make_component(category: str, component_id: str, profile_name: str, profiles: Mapping[str, Mapping[str, Any]], overrides: Mapping[str, Any] | None = None) -> ComponentDefinition:
    """Resolve an explicitly assigned profile without inspecting component_id."""
    if profile_name not in profiles:
        raise ValueError(f"Unknown explicit profile {category}.{profile_name}")
    data = deepcopy(dict(profiles[profile_name]))
    if overrides:
        data.update(overrides)
    return ComponentDefinition(
        id=component_id,
        category=category,
        traits=frozenset(data["traits"]),
        profile=profile_name,
        compatible_archetypes=frozenset(data["compatible_archetypes"]),
        compatible_directions=frozenset(data["compatible_directions"]),
        required_data=frozenset(data["required_data"]),
        required_any_data=frozenset(data["required_any_data"]),
        required_media=frozenset(data["required_media"]),
        required_any_media=frozenset(data["required_any_media"]),
        allowed_media_sources=frozenset(data["allowed_media_sources"]),
        incompatible_components=frozenset(data["incompatible_components"]),
        density=data["density"],
        visual_weight=data["visual_weight"],
        section_energy=data["section_energy"],
        mobile_variant=data["mobile_variant"],
        trade_affinity=data["trade_affinity"],
        conversion_score=data["conversion_score"],
        editorial_score=data["editorial_score"],
        image_dependency=data["image_dependency"],
        content_zones=CONTENT_ZONES[category],
        notes=data["notes"] or f"Explicit {category} profile: {profile_name}.",
        blueprint_spec=data["spec"],
    )


def registry(
    category: str,
    groups: Mapping[str, Sequence[str]],
    profiles: Mapping[str, Mapping[str, Any]],
    overrides: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, ComponentDefinition]:
    overrides = overrides or {}
    result: dict[str, ComponentDefinition] = {}
    for profile_name, component_ids in groups.items():
        for component_id in component_ids:
            if component_id in result:
                raise ValueError(f"Duplicate component id in {category}: {component_id}")
            result[component_id] = make_component(category, component_id, profile_name, profiles, overrides.get(component_id))
    return result
