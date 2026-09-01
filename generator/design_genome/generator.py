"""Deterministic, data-aware SiteDNA generation for knowledge experiments."""

from __future__ import annotations

import hashlib
from typing import Iterable, Mapping, TypeVar

from .archetypes import ARCHETYPES
from .compatibility import evaluate_component
from .data.color_systems import COLOR_SYSTEMS
from .data.components import COMPONENT_REGISTRIES
from .data.grids import GRID_SYSTEMS
from .data.page_silhouettes import PAGE_SILHOUETTES
from .data.systems import MOBILE_PERSONALITIES, MOTION_SYSTEMS, SPATIAL_SYSTEMS
from .data.trade_grammar import TRADE_GRAMMARS
from .data.typography_systems import TYPOGRAPHY_SYSTEMS
from .linter import lint_dna
from .models import ComponentDefinition, DesignInput, SiteArchetype, SiteDNA
from .quality import evaluate_quality
from .similarity import maximum_similarity


T = TypeVar("T")
SPACING_SYSTEMS = ("compact_technical", "balanced_operational", "generous_editorial", "cinematic_pause", "material_breathing")
GEOMETRY_SYSTEMS = ("square_precise", "soft_residential", "framed_architectural", "offset_editorial", "material_organic")


def _noise(seed: str, value: str) -> float:
    digest = hashlib.sha256(f"{seed}|{value}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") / (2**64 - 1)


def _best(seed: str, values: Iterable[T], identity, score) -> T:
    candidates = list(values)
    if not candidates:
        raise RuntimeError("Design Genome has no compatible candidate for this input.")
    return max(candidates, key=lambda item: (score(item) + _noise(seed, identity(item)) * .19, identity(item)))


def _select_archetype(design_input: DesignInput, seed: str) -> SiteArchetype:
    grammar = TRADE_GRAMMARS.get(design_input.trade)
    if grammar is None:
        raise ValueError(f"Unsupported trade: {design_input.trade}")
    values = [item for item in ARCHETYPES.values() if design_input.trade in item.compatible_trades]
    return _best(
        seed,
        values,
        lambda item: item.id,
        lambda item: (
            (1.0 if item.id in grammar.preferred_archetypes else 0.0)
            + (1.0 if design_input.business_intent in item.business_intents else 0.0)
            + (1.0 - abs(item.conversion_intensity - grammar.conversion_need)) * .55
        ),
    )


def _select_direction(design_input: DesignInput, archetype: SiteArchetype, seed: str) -> str:
    grammar = TRADE_GRAMMARS[design_input.trade]
    return _best(
        seed,
        grammar.compatible_directions,
        str,
        lambda direction: (
            (1.0 if direction in archetype.preferred_directions else 0.0)
            - (2.0 if direction in grammar.discouraged_directions else 0.0)
        ),
    )


def _select_silhouette(design_input: DesignInput, archetype: SiteArchetype, seed: str):
    available = set(design_input.available_data)
    if design_input.media.project_photos:
        available.add("project_media")
    if design_input.media.before_after_pairs:
        available.add("before_after")
    values = [item for item in PAGE_SILHOUETTES.values() if item.minimum_data <= available]
    return _best(
        seed,
        values,
        lambda item: item.id,
        lambda item: (
            (1.2 if item.id in archetype.preferred_silhouettes else 0.0)
            + (0.5 if archetype.id in item.target_archetypes else 0.0)
            + len(item.traits & archetype.traits) * .14
            - abs(item.maximum_density - archetype.target_density) * .08
        ),
    )


def _select_component(
    category: str,
    design_input: DesignInput,
    archetype: SiteArchetype,
    art_direction: str,
    seed: str,
    selected: tuple[str, ...],
) -> ComponentDefinition:
    scored = []
    for component in COMPONENT_REGISTRIES[category].values():
        result = evaluate_component(component, design_input, archetype, art_direction, selected)
        if result.allowed:
            scored.append((component, result.score))
    scores_by_id = {component.id: score for component, score in scored}
    return _best(
        seed,
        (item[0] for item in scored),
        lambda item: item.id,
        lambda item: scores_by_id[item.id],
    )


def _optional_component(
    category: str,
    enabled: bool,
    design_input: DesignInput,
    archetype: SiteArchetype,
    art_direction: str,
    seed: str,
    selected: tuple[str, ...],
) -> ComponentDefinition | None:
    if not enabled:
        return None
    try:
        return _select_component(category, design_input, archetype, art_direction, seed, selected)
    except RuntimeError:
        return None


def _section_order(silhouette_sections: tuple[str, ...], selected: Mapping[str, ComponentDefinition | None]) -> tuple[str, ...]:
    aliases = {
        "header": ("header",),
        "hero": ("hero",),
        "services": ("service", "capabil", "specification", "issue", "scope"),
        "gallery": ("gallery", "project", "before_after", "material", "image", "casebook", "reveal"),
        "about": ("about", "story", "narrative", "manifesto", "process", "people", "essay", "heritage", "introduction", "brief", "design", "build"),
        "trust": ("trust", "proof", "review", "testimonial", "certification", "stat"),
        "cta": ("action", "quote"),
        "contact": ("contact", "form"),
        "footer": ("footer",),
    }
    positions: dict[str, int] = {}
    fallback_positions = {
        "header": -20, "hero": -10, "services": 30, "gallery": 40,
        "about": 50, "trust": 60, "cta": 70, "contact": 80, "footer": 1000,
    }
    for category, needles in aliases.items():
        if not selected.get(category):
            continue
        positions[category] = min(
            (index for index, section in enumerate(silhouette_sections) if any(needle in section for needle in needles)),
            default=fallback_positions[category],
        )
    positions["header"] = -20
    positions["hero"] = -10
    positions["footer"] = 1000
    return tuple(category for category, _ in sorted(positions.items(), key=lambda item: (item[1], item[0])))


def _build_candidate(design_input: DesignInput, seed: str) -> SiteDNA:
    archetype = _select_archetype(design_input, seed)
    direction = _select_direction(design_input, archetype, seed)
    silhouette = _select_silhouette(design_input, archetype, seed)

    color = _best(
        seed,
        COLOR_SYSTEMS.values(),
        lambda item: item.id,
        lambda item: item.trade_affinities.get(design_input.trade, 0.0)
        + (item.luxury_score if "luxurious" in archetype.traits else 0.0)
        + (item.technical_score if "technical" in archetype.traits else 0.0)
        + (item.craft_score if archetype.traits & {"warm", "material_led", "tactile"} else 0.0),
    )
    typography = _best(
        seed,
        TYPOGRAPHY_SYSTEMS.values(),
        lambda item: item.id,
        lambda item: (
            (1.0 if item.id in color.compatible_typography else 0.0)
            + len(item.traits & archetype.traits) * .18 + item.readability_score * .35
        ),
    )
    grid = _best(seed, GRID_SYSTEMS.values(), lambda item: item.id, lambda item: len(item.traits & (archetype.traits | silhouette.traits)) * .35)

    selected_ids: list[str] = []
    selected: dict[str, ComponentDefinition | None] = {}
    for category in ("header", "hero", "services"):
        component = _select_component(category, design_input, archetype, direction, f"{seed}:{category}", tuple(selected_ids))
        selected[category] = component
        selected_ids.append(component.id)

    has_images = bool(design_input.media.artisan_photos or design_input.media.stock_photos)
    has_project_media = bool(design_input.media.project_photos or design_input.media.before_after_pairs)
    has_truth = bool(design_input.available_data & {
        "reviews", "insurance", "certifications", "statistics", "team", "service_areas",
        "partners", "brands", "awards", "guarantee", "opening_hours", "emergency_service",
        "response_delay", "process", "verified_facts",
    }) or has_project_media
    has_contact = bool(design_input.available_data & {"phone", "email"})
    conditions = {
        "gallery": has_images,
        "about": True,
        "trust": has_truth,
        "cta": has_contact,
        "contact": has_contact,
        "form": has_contact,
    }
    for category in ("gallery", "about", "trust", "cta", "contact", "form"):
        component = _optional_component(category, conditions[category], design_input, archetype, direction, f"{seed}:{category}", tuple(selected_ids))
        selected[category] = component
        if component:
            selected_ids.append(component.id)
    footer = _select_component("footer", design_input, archetype, direction, f"{seed}:footer", tuple(selected_ids))
    selected["footer"] = footer

    traits = archetype.traits | silhouette.traits
    motion = _best(seed, MOTION_SYSTEMS.values(), lambda item: item.id, lambda item: len(item.traits & traits) * .45 - item.performance_cost * .08)
    spatial = _best(seed, SPATIAL_SYSTEMS.values(), lambda item: item.id, lambda item: (.7 if "spatial" in traits and item.level in {2, 3} else 0.0) - item.performance_cost * .11)
    mobile = _best(seed, MOBILE_PERSONALITIES.values(), lambda item: item.id, lambda item: len(item.traits & traits) * .5)
    spacing = _best(seed, SPACING_SYSTEMS, str, lambda item: .5 if ("editorial" in item and "editorial" in traits) or ("technical" in item and "technical" in traits) else 0.0)
    geometry = _best(seed, GEOMETRY_SYSTEMS, str, lambda item: .5 if ("material" in item and traits & {"material", "material_led"}) or ("architectural" in item and "architectural" in traits) else 0.0)

    order = _section_order(silhouette.sections, selected)
    payload = {
        "version": "design-genome-1",
        "site_archetype": archetype.id,
        "art_direction": direction,
        "page_silhouette": silhouette.id,
        "color_system": color.id,
        "typography_system": typography.id,
        "grid_system": grid.id,
        "spacing_system": spacing,
        "geometry_system": geometry,
        "photo_direction": f"{design_input.trade}:{direction}:hero",
        "header_component": selected["header"].id,
        "hero_component": selected["hero"].id,
        "services_component": selected["services"].id,
        "gallery_component": selected["gallery"].id if selected["gallery"] else None,
        "about_component": selected["about"].id if selected["about"] else None,
        "trust_component": selected["trust"].id if selected["trust"] else None,
        "cta_component": selected["cta"].id if selected["cta"] else None,
        "contact_component": selected["contact"].id if selected["contact"] else None,
        "footer_component": footer.id,
        "form_component": selected["form"].id if selected["form"] else None,
        "motion_system": motion.id,
        "spatial_system": spatial.id,
        "mobile_personality": mobile.id,
        "section_order": order,
        "density": archetype.target_density,
        "conversion_intensity": round(archetype.conversion_intensity, 3),
        "design_signature": "",
        "seed": seed,
    }
    payload["design_signature"] = SiteDNA.signature_for(payload)
    return SiteDNA.from_dict(payload)


class DesignGenome:
    """Generate inspectable DNA while enforcing data truth and anti-clone limits."""

    def __init__(self, reject_similarity: float = .84, candidate_count: int = 24):
        self.reject_similarity = reject_similarity
        self.candidate_count = candidate_count

    def generate(self, design_input: DesignInput, history: tuple[SiteDNA, ...] = ()) -> SiteDNA:
        accepted: list[tuple[float, SiteDNA]] = []
        for index in range(self.candidate_count):
            candidate = _build_candidate(design_input, f"{design_input.seed}:{index}")
            similarity = maximum_similarity(candidate, history)
            errors = [issue for issue in lint_dna(candidate, design_input) if issue.severity == "error"]
            if errors or similarity >= self.reject_similarity:
                continue
            quality = evaluate_quality(candidate, design_input, originality=1.0 - similarity)
            accepted.append((quality.total, candidate))
        if not accepted:
            raise RuntimeError("No honest, compatible and sufficiently distinct SiteDNA candidate was found.")
        return max(accepted, key=lambda item: (item[0], item[1].design_signature))[1]


def generate_site_dna(design_input: DesignInput, history: tuple[SiteDNA, ...] = ()) -> SiteDNA:
    return DesignGenome().generate(design_input, history)
