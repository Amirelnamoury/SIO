"""Serializable contracts shared by the experimental Design Genome modules."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any, Mapping


class TruthClass(StrEnum):
    FACT = "fact"
    DERIVED_FACT = "derived_fact"
    SAFE_GENERIC_COPY = "safe_generic_copy"
    FORBIDDEN_INVENTION = "forbidden_invention"


@dataclass(frozen=True)
class MediaInventory:
    artisan_photos: int = 0
    stock_photos: int = 0
    project_photos: int = 0
    before_after_pairs: int = 0
    portrait_photos: int = 0
    landscape_photos: int = 0
    has_logo: bool = False

    def available_roles(self) -> frozenset[str]:
        roles = set()
        if self.artisan_photos:
            roles.add("artisan_photo")
        if self.stock_photos:
            roles.add("stock_photo")
        if self.project_photos:
            roles.add("artisan_project")
        if self.before_after_pairs:
            roles.add("before_after")
        if self.portrait_photos:
            roles.add("portrait")
        if self.landscape_photos:
            roles.add("landscape")
        if self.has_logo:
            roles.add("logo")
        return frozenset(roles)


@dataclass(frozen=True)
class DesignInput:
    trade: str
    seed: str
    city: str = ""
    business_intent: str = "balanced"
    services: tuple[str, ...] = ()
    facts: Mapping[str, Any] = field(default_factory=dict)
    media: MediaInventory = field(default_factory=MediaInventory)
    preferences: Mapping[str, str] = field(default_factory=dict)

    @property
    def available_data(self) -> frozenset[str]:
        keys = {key for key, value in self.facts.items() if value not in (None, "", [], ())}
        if self.services:
            keys.add("services")
        if self.city:
            keys.add("city")
        return frozenset(keys)


@dataclass(frozen=True)
class ComponentDefinition:
    id: str
    category: str
    traits: frozenset[str]
    compatible_archetypes: frozenset[str] = frozenset()
    compatible_directions: frozenset[str] = frozenset()
    required_data: frozenset[str] = frozenset()
    required_media: frozenset[str] = frozenset()
    allowed_media_sources: frozenset[str] = frozenset({"artisan", "stock", "none"})
    incompatible_components: frozenset[str] = frozenset()
    density: int = 3
    visual_weight: int = 3
    section_energy: str = "medium"
    mobile_variant: str = "stack"
    trade_affinity: Mapping[str, float] = field(default_factory=dict)
    conversion_score: float = 0.5
    editorial_score: float = 0.5
    image_dependency: float = 0.0
    content_zones: tuple[str, ...] = ()
    notes: str = ""


@dataclass(frozen=True)
class ColorSystem:
    id: str
    family: str
    mode: str
    tokens: Mapping[str, str]
    contrast_score: float
    warmth_score: float
    luxury_score: float
    technical_score: float
    craft_score: float
    conversion_score: float
    trade_affinities: Mapping[str, float]
    compatible_typography: tuple[str, ...]
    compatible_image_strategies: tuple[str, ...]
    incompatible_traits: frozenset[str] = frozenset()


@dataclass(frozen=True)
class TypographySystem:
    id: str
    category: str
    display_family: str
    heading_family: str
    body_family: str
    accent_family: str
    weights: tuple[int, ...]
    size_scale: tuple[float, ...]
    line_height_scale: tuple[float, ...]
    letter_spacing_scale: tuple[float, ...]
    case_behavior: str
    max_title_width: int
    hero_size_range: tuple[int, int]
    section_title_range: tuple[int, int]
    body_measure: int
    mobile_scale: float
    editorial_score: float
    luxury_score: float
    technical_score: float
    warmth_score: float
    conversion_score: float
    readability_score: float
    traits: frozenset[str]


@dataclass(frozen=True)
class GridSystem:
    id: str
    columns: int
    max_width: int
    gutter: int
    content_widths: tuple[str, ...]
    section_spacing: tuple[int, int]
    breakpoints: tuple[int, ...]
    mobile_transformation: str
    traits: frozenset[str]


@dataclass(frozen=True)
class PageSilhouette:
    id: str
    sections: tuple[str, ...]
    target_archetypes: frozenset[str]
    optional_sections: frozenset[str]
    forbidden_sections: frozenset[str]
    minimum_data: frozenset[str]
    maximum_density: int
    expected_image_count: tuple[int, int]
    trust_requirements: frozenset[str]
    conversion_intensity: float
    mobile_transformation: str
    traits: frozenset[str]


@dataclass(frozen=True)
class SiteArchetype:
    id: str
    business_intents: frozenset[str]
    compatible_trades: frozenset[str]
    traits: frozenset[str]
    preferred_silhouettes: tuple[str, ...]
    preferred_directions: tuple[str, ...]
    conversion_intensity: float
    target_density: int
    trust_need: int
    image_need: int


@dataclass(frozen=True)
class TradeGrammar:
    trade: str
    business_intents: tuple[str, ...]
    customer_fears: tuple[str, ...]
    trust_signals: tuple[str, ...]
    photo_opportunities: tuple[str, ...]
    photo_risks: tuple[str, ...]
    visual_cliches: tuple[str, ...]
    preferred_archetypes: tuple[str, ...]
    compatible_directions: tuple[str, ...]
    discouraged_directions: tuple[str, ...]
    conversion_need: float
    typical_density: int


@dataclass(frozen=True)
class PhotoDirection:
    id: str
    trade: str
    art_direction: str
    section: str
    queries: tuple[str, ...]
    avoid: tuple[str, ...]
    orientation: str
    temperature: str
    brightness: str
    saturation: str
    texture: str
    allowed_roles: frozenset[str]


@dataclass(frozen=True)
class MotionSystem:
    id: str
    intensity: int
    techniques: tuple[str, ...]
    performance_cost: int
    reduced_motion_fallback: str
    traits: frozenset[str]


@dataclass(frozen=True)
class SpatialSystem:
    id: str
    level: int
    techniques: tuple[str, ...]
    mobile_fallback: str
    reduced_motion_fallback: str
    performance_cost: int
    explanatory_only: bool = True


@dataclass(frozen=True)
class MobilePersonality:
    id: str
    navigation: str
    hero_adaptation: str
    gallery_behavior: str
    cta_behavior: str
    spacing_scale: float
    motion_policy: str
    content_priority: tuple[str, ...]
    traits: frozenset[str]


@dataclass(frozen=True)
class SiteDNA:
    version: str
    site_archetype: str
    art_direction: str
    page_silhouette: str
    color_system: str
    typography_system: str
    grid_system: str
    spacing_system: str
    geometry_system: str
    photo_direction: str
    header_component: str
    hero_component: str
    services_component: str | None
    gallery_component: str | None
    about_component: str | None
    trust_component: str | None
    cta_component: str | None
    contact_component: str | None
    footer_component: str
    form_component: str | None
    motion_system: str
    spatial_system: str
    mobile_personality: str
    section_order: tuple[str, ...]
    density: int
    conversion_intensity: float
    design_signature: str
    seed: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SiteDNA":
        values = dict(payload)
        values["section_order"] = tuple(values["section_order"])
        return cls(**values)

    @staticmethod
    def signature_for(payload: Mapping[str, Any]) -> str:
        excluded = {"design_signature", "seed"}
        canonical = json.dumps(
            {key: payload[key] for key in sorted(payload) if key not in excluded},
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]


@dataclass(frozen=True)
class CompatibilityResult:
    allowed: bool
    score: float
    hard_failures: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class SimilarityReport:
    structural_distance: float
    typographic_distance: float
    chromatic_distance: float
    component_distance: float
    narrative_distance: float
    photo_strategy_distance: float
    overall_visual_similarity: float


@dataclass(frozen=True)
class RhythmReport:
    score: float
    weights: tuple[int, ...]
    energies: tuple[str, ...]
    issues: tuple[str, ...]


@dataclass(frozen=True)
class DesignQualityReport:
    total: float
    coherence: float
    hierarchy: float
    readability: float
    contrast: float
    rhythm: float
    conversion_clarity: float
    content_fit: float
    media_fit: float
    business_fit: float
    mobile_compatibility: float
    originality: float
    overdesign_risk: float
    underdesign_risk: float
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class LintIssue:
    code: str
    severity: str
    message: str
    field: str | None = None
