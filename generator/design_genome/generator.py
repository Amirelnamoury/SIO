"""Deterministic, data-aware SiteDNA generation for knowledge experiments."""

from __future__ import annotations

import hashlib
from typing import Iterable, Mapping, TypeVar

from .archetypes import ARCHETYPES
from .compatibility import evaluate_component
from .component_relationships import component_pair_affinity
from .data.color_systems import COLOR_SYSTEMS
from .data.components import ALL_COMPONENTS, COMPONENT_REGISTRIES
from .data.grids import GRID_SYSTEMS
from .data.foundations import GEOMETRY_SYSTEMS, SPACING_SYSTEMS
from .data.page_silhouettes import PAGE_SILHOUETTES
from .data.systems import MOBILE_PERSONALITIES, MOTION_SYSTEMS, SPATIAL_SYSTEMS
from .data.trade_grammar import TRADE_GRAMMARS
from .data.typography_systems import TYPOGRAPHY_SYSTEMS
from .linter import lint_dna
from .models import (
    ComponentDefinition, DecisionRecord, DesignDecisionTrace, DesignInput,
    GenerationResult, SiteArchetype, SiteDNA,
)
from .quality import evaluate_quality
from .similarity import maximum_similarity
from .taxonomy import normalize_business_intent


T = TypeVar("T")

CATEGORY_SECTION_MARKERS = {
    "header": ("header",),
    "hero": ("hero",),
    "services": ("service", "capabil", "specification", "issue", "scope"),
    "gallery": ("gallery", "project", "before_after", "material", "image", "casebook", "reveal", "workshop"),
    "about": ("about", "story", "narrative", "manifesto", "process", "people", "essay", "heritage", "introduction", "brief", "design", "build"),
    "trust": ("trust", "proof", "review", "testimonial", "certification", "stat"),
    "cta": ("action", "quote", "urgent"),
    "contact": ("contact", "form"),
    "form": ("form",),
    "footer": ("footer",),
}


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
    business_intent = normalize_business_intent(design_input.business_intent)
    return _best(
        seed,
        values,
        lambda item: item.id,
        lambda item: (
            (1.0 if item.id in grammar.preferred_archetypes else 0.0)
            + (1.0 if business_intent in item.business_intents else 0.0)
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
    previous = ALL_COMPONENTS[selected[-1]] if selected else None
    for component in COMPONENT_REGISTRIES[category].values():
        result = evaluate_component(component, design_input, archetype, art_direction, selected)
        if result.allowed:
            relationship = component_pair_affinity(previous, component, archetype.traits).score if previous else 1.0
            scored.append((component, result.score * .72 + relationship * .28))
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
    positions: dict[str, int] = {}
    fallback_positions = {
        "header": -20, "hero": -10, "services": 30, "gallery": 40,
        "about": 50, "trust": 60, "cta": 70, "contact": 80, "footer": 1000,
    }
    for category, needles in CATEGORY_SECTION_MARKERS.items():
        if category == "form":
            continue
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
    silhouette_sections = silhouette.sections
    supports = {
        category: any(any(marker in section for marker in markers) for section in silhouette_sections)
        for category, markers in CATEGORY_SECTION_MARKERS.items()
    }
    conditions = {
        "gallery": has_images and supports["gallery"],
        "about": supports["about"],
        "trust": has_truth and supports["trust"],
        "cta": has_contact and supports["cta"],
        "contact": has_contact and supports["contact"],
        "form": has_contact and supports["form"],
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
    spacing = _best(seed, SPACING_SYSTEMS.values(), lambda item: item.id, lambda item: .5 if ("editorial" in item.id and "editorial" in traits) or ("technical" in item.id and "technical" in traits) else 0.0)
    geometry = _best(seed, GEOMETRY_SYSTEMS.values(), lambda item: item.id, lambda item: .5 if ("material" in item.id and traits & {"material", "material_led"}) or ("architectural" in item.id and "architectural" in traits) else 0.0)

    order = _section_order(silhouette.sections, selected)
    payload = {
        "version": "design-genome-1",
        "site_archetype": archetype.id,
        "art_direction": direction,
        "page_silhouette": silhouette.id,
        "color_system": color.id,
        "typography_system": typography.id,
        "grid_system": grid.id,
        "spacing_system": spacing.id,
        "geometry_system": geometry.id,
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


def _trace_decisions(dna: SiteDNA, design_input: DesignInput) -> tuple[DecisionRecord, ...]:
    component_fields = (
        "header_component", "hero_component", "services_component", "gallery_component",
        "about_component", "trust_component", "cta_component", "contact_component", "footer_component", "form_component",
    )
    decisions = [
        DecisionRecord("site_archetype", dna.site_archetype, (f"trade:{design_input.trade}", f"business_intent:{design_input.business_intent}", "trade grammar and conversion fit")),
        DecisionRecord("art_direction", dna.art_direction, ("compatible with trade grammar", f"archetype:{dna.site_archetype}")),
        DecisionRecord("page_silhouette", dna.page_silhouette, ("minimum data satisfied", "narrative affinity", f"business_intent:{design_input.business_intent}")),
        DecisionRecord("color_system", dna.color_system, (f"trade affinity:{design_input.trade}", "archetype tone fit", "accessible semantic tokens")),
        DecisionRecord("typography_system", dna.typography_system, ("color-system compatibility", "readability floor", "archetype personality")),
        DecisionRecord("grid_system", dna.grid_system, ("silhouette traits", "archetype density", "mobile transformation available")),
    ]
    for field in component_fields:
        component_id = getattr(dna, field)
        if not component_id:
            decisions.append(DecisionRecord(field, "omitted", ("no honest compatible evidence or channel required this section",)))
            continue
        component = ALL_COMPONENTS[component_id]
        decisions.append(DecisionRecord(
            field,
            component_id,
            (
                f"explicit_profile:{component.profile}",
                f"density:{component.density}",
                f"energy:{component.section_energy}",
                "hard data and media constraints satisfied",
                "pair affinity considered against previous section",
            ),
        ))
    decisions.extend((
        DecisionRecord("spacing_system", dna.spacing_system, ("density and narrative pacing",)),
        DecisionRecord("geometry_system", dna.geometry_system, ("shape language and art direction",)),
        DecisionRecord("motion_system", dna.motion_system, ("trait affinity", "performance cost penalty", "reduced-motion fallback")),
        DecisionRecord("mobile_personality", dna.mobile_personality, ("archetype content priority", "mobile-specific transformation")),
    ))
    return tuple(decisions)


class DesignGenome:
    """Generate inspectable DNA while enforcing data truth and anti-clone limits."""

    def __init__(self, reject_similarity: float = .84, candidate_count: int = 24, quality_floor: float = 58.0):
        self.reject_similarity = reject_similarity
        self.candidate_count = candidate_count
        self.quality_floor = quality_floor

    def generate(
        self,
        design_input: DesignInput,
        history: tuple[SiteDNA, ...] = (),
        audit_traces: list[DesignDecisionTrace] | None = None,
    ) -> SiteDNA:
        result = self.generate_with_trace(design_input, history)
        if audit_traces is not None:
            audit_traces.append(result.trace)
        return result.dna

    def generate_with_trace(self, design_input: DesignInput, history: tuple[SiteDNA, ...] = ()) -> GenerationResult:
        rejected: list[dict[str, object]] = []
        linter_rejections = 0
        similarity_rejections = 0
        quality_rejections = 0
        for index in range(self.candidate_count):
            candidate = _build_candidate(design_input, f"{design_input.seed}:{index}")
            similarity = maximum_similarity(candidate, history)
            errors = [issue for issue in lint_dna(candidate, design_input) if issue.severity == "error"]
            if errors:
                linter_rejections += 1
                rejected.append({"attempt": index + 1, "signature": candidate.design_signature, "reason": "linter", "issues": tuple(issue.code for issue in errors)})
                continue
            if similarity >= self.reject_similarity:
                similarity_rejections += 1
                rejected.append({"attempt": index + 1, "signature": candidate.design_signature, "reason": "similarity", "score": similarity})
                continue
            quality = evaluate_quality(candidate, design_input, originality=1.0 - similarity)
            if quality.total < self.quality_floor:
                quality_rejections += 1
                rejected.append({"attempt": index + 1, "signature": candidate.design_signature, "reason": "quality_floor", "score": quality.total})
                continue
            trace = DesignDecisionTrace(
                seed=design_input.seed,
                attempts=index + 1,
                decisions=_trace_decisions(candidate, design_input),
                rejected_candidates=tuple(rejected),
                linter_rejections=linter_rejections,
                similarity_rejections=similarity_rejections,
                quality_rejections=quality_rejections,
            )
            return GenerationResult(candidate, trace)
        raise RuntimeError(
            "No honest, compatible and sufficiently distinct SiteDNA candidate was found "
            f"after {self.candidate_count} attempts (linter={linter_rejections}, "
            f"similarity={similarity_rejections}, quality={quality_rejections})."
        )


def generate_site_dna(design_input: DesignInput, history: tuple[SiteDNA, ...] = ()) -> SiteDNA:
    return DesignGenome().generate(design_input, history)
