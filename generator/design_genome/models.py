"""Serializable contracts shared by the experimental Design Genome modules."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any, Mapping


VISUAL_SIGNATURE_FIELDS = (
    "site_archetype", "art_direction", "page_silhouette", "color_system",
    "typography_system", "grid_system", "spacing_system", "geometry_system",
    "photo_direction", "header_component", "hero_component", "services_component",
    "gallery_component", "about_component", "trust_component", "cta_component",
    "contact_component", "footer_component", "form_component", "motion_system",
    "spatial_system", "mobile_personality", "section_order", "density",
    "conversion_intensity",
)


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
class ComponentBlueprintSpec:
    """Resolved structural contract consumed by a future renderer."""

    schema_version: str
    layout_model: str
    layout_pattern: str
    edge_behavior: str
    media_intensity: int
    type_scale_role: str
    content_alignment: str
    desktop_spec: Mapping[str, Any]
    mobile_spec: Mapping[str, Any]
    media_spec: Mapping[str, Any]
    content_spec: Mapping[str, Any]
    behavior_spec: Mapping[str, Any]
    fallback_strategy: str


@dataclass(frozen=True)
class StructuralVariantSpec:
    """Explicit component-level composition layered over a family blueprint."""

    variant_id: str
    design_intent: str
    flow_direction: str
    alignment_anchor: str
    frame_behavior: str
    collapse_strategy: str
    priority_anchor: str
    focus_progression: str
    variant_source: str = "explicit"
    desktop_overrides: Mapping[str, Any] = field(default_factory=dict)
    mobile_overrides: Mapping[str, Any] = field(default_factory=dict)
    media_overrides: Mapping[str, Any] = field(default_factory=dict)
    content_overrides: Mapping[str, Any] = field(default_factory=dict)
    behavior_overrides: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ComponentDefinition:
    id: str
    category: str
    traits: frozenset[str]
    family_id: str
    variant_id: str
    design_intent: str = ""
    variant_source: str = "explicit"
    is_alias: bool = False
    alias_of: str | None = None
    profile: str = ""
    compatible_archetypes: frozenset[str] = frozenset()
    compatible_directions: frozenset[str] = frozenset()
    required_data: frozenset[str] = frozenset()
    required_any_data: frozenset[str] = frozenset()
    required_media: frozenset[str] = frozenset()
    required_any_media: frozenset[str] = frozenset()
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
    blueprint_spec: ComponentBlueprintSpec | None = None


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
    material_inspiration: str = "neutral architectural material"
    temperature: str = "neutral"
    contrast_personality: str = "balanced"
    dominant_behavior: str = "canvas-led"
    accent_behavior: str = "measured"
    surface_philosophy: str = "surfaces follow material hierarchy"
    border_philosophy: str = "borders clarify structure"
    image_treatment_preference: str = "natural"
    recommended_typography_categories: tuple[str, ...] = ()
    recommended_archetypes: tuple[str, ...] = ()
    bad_combinations: tuple[str, ...] = ()


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
    personality: str = "neutral"
    display_behavior: str = "measured"
    heading_behavior: str = "clear hierarchy"
    body_behavior: str = "readable"
    accent_behavior: str = "restrained"
    title_proportions: str = "balanced"
    uppercase_policy: str = "labels_only"
    numeric_style: str = "lining"
    hero_wrapping_policy: str = "balanced_lines"
    section_wrapping: str = "two_lines_max"
    dense_mode_behavior: str = "reduce display scale"
    airy_mode_behavior: str = "increase whitespace, not tracking"
    availability: str = "system_safe"
    fallback_stack: tuple[str, ...] = ("Arial", "sans-serif")
    max_font_count: int = 2


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
    tablet_columns: int = 8
    mobile_columns: int = 4
    outer_margins: tuple[int, int, int] = (24, 20, 16)
    nested_content_width: str = "readable"
    media_overflow_policy: str = "clip_to_grid"
    full_bleed_policy: str = "explicit_sections_only"
    alignment_lines: tuple[str, ...] = ("outer", "content", "media")


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
    business_story: str = "establish, explain, reassure, convert"
    opening_goal: str = "establish identity and relevance"
    middle_goal: str = "explain services and evidence"
    closing_goal: str = "remove objections and offer contact"
    section_roles: Mapping[str, str] = field(default_factory=dict)
    ideal_content_level: str = "balanced"
    recommended_media: tuple[str, ...] = ()
    trust_dependency: str = "optional_when_verified"
    conversion_mode: str = "balanced"
    mobile_narrative: str = "preserve decision order"
    substitutable_sections: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    fixed_sections: tuple[str, ...] = ("header", "hero", "footer")


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
    business_purpose: str = "clarify offer and support a decision"
    visual_purpose: str = "create a coherent non-template identity"
    content_needs: tuple[str, ...] = ("services", "identity")
    media_needs: tuple[str, ...] = ()
    trust_needs: tuple[str, ...] = ()
    recommended_narrative: str = "identity -> services -> evidence -> contact"


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
    positive_queries: tuple[str, ...] = ()
    negative_queries: tuple[str, ...] = ()
    subject_priority: tuple[str, ...] = ()
    composition_priority: tuple[str, ...] = ()
    people_policy: str = "people only when contextually credible"
    tool_policy: str = "tools support the work; never isolated cliché"
    environment_policy: str = "realistic trade context"
    camera_feel: str = "natural documentary"
    material_focus: tuple[str, ...] = ()
    crop: str = "preserve subject and material context"
    stock_cliche_risk: str = "medium"


@dataclass(frozen=True)
class MotionSystem:
    id: str
    intensity: int
    techniques: tuple[str, ...]
    performance_cost: int
    reduced_motion_fallback: str
    traits: frozenset[str]
    entry_behavior: str = "none"
    scroll_behavior: str = "native"
    image_reveal: str = "none"
    text_reveal: str = "none"
    stagger: str = "none"
    hover_behavior: str = "state_only"
    navigation_behavior: str = "instant"
    performance_budget_ms: int = 0


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
    header_height: int = 64
    image_crop: str = "subject_safe"
    type_scale: float = .72
    section_spacing: int = 64


@dataclass(frozen=True)
class SpacingSystem:
    id: str
    section_padding: tuple[int, int]
    component_gap: int
    text_gap: int
    grid_gap: int
    hero_padding: tuple[int, int]
    mobile_multiplier: float
    density: int
    traits: frozenset[str] = frozenset()
    compatible_archetypes: frozenset[str] = frozenset()
    compatible_directions: frozenset[str] = frozenset()
    density_range: tuple[int, int] = (1, 5)


@dataclass(frozen=True)
class GeometrySystem:
    id: str
    radius: int
    border_behavior: str
    line_behavior: str
    shape_language: str
    image_corner_behavior: str
    button_shape: str
    card_shape: str
    traits: frozenset[str] = frozenset()
    compatible_archetypes: frozenset[str] = frozenset()
    compatible_directions: frozenset[str] = frozenset()


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
    composition_signature: str
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
        values.setdefault("composition_signature", "")
        return cls(**values)

    @staticmethod
    def signature_for(payload: Mapping[str, Any]) -> str:
        canonical = json.dumps(
            {key: payload[key] for key in VISUAL_SIGNATURE_FIELDS},
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
class PairAffinityResult:
    score: float
    hard_failure: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class SimilarityReport:
    structural_distance: float
    typographic_distance: float
    chromatic_distance: float
    component_distance: float
    narrative_distance: float
    photo_strategy_distance: float
    overall_visual_similarity: float
    blueprint_distance: float = 0.0
    family_distance: float = 0.0
    layout_rhythm_distance: float = 0.0


@dataclass(frozen=True)
class RhythmReport:
    score: float
    weights: tuple[int, ...]
    energies: tuple[str, ...]
    issues: tuple[str, ...]
    pair_affinity: float = 0.0
    patterns: tuple[str, ...] = ()
    edges: tuple[str, ...] = ()
    media_intensities: tuple[int, ...] = ()
    type_scale_roles: tuple[str, ...] = ()


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


@dataclass(frozen=True)
class DecisionRecord:
    field: str
    selected: str
    reasons: tuple[str, ...]
    rejected: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class DesignDecisionTrace:
    seed: str
    attempts: int
    decisions: tuple[DecisionRecord, ...]
    rejected_candidates: tuple[Mapping[str, Any], ...]
    linter_rejections: int = 0
    similarity_rejections: int = 0
    quality_rejections: int = 0
    structural_duplicate_rejections: int = 0


@dataclass(frozen=True)
class StructuralDistanceReport:
    distance: float
    layout_distance: float
    content_distance: float
    media_distance: float
    mobile_distance: float
    behavior_distance: float
    rhythm_distance: float
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class CompositionComponentEntry:
    section: str
    component_id: str
    family_id: str
    variant_id: str
    layout_pattern: str
    edge_behavior: str
    media_intensity: int
    type_scale_role: str
    fingerprint: str


@dataclass(frozen=True)
class SiteDNACompositionReport:
    composition_signature: str
    components: tuple[CompositionComponentEntry, ...]
    transitions: tuple[Mapping[str, Any], ...]
    layout_rhythm: tuple[str, ...]
    edge_rhythm: tuple[str, ...]
    media_rhythm: tuple[int, ...]
    type_rhythm: tuple[str, ...]


@dataclass(frozen=True)
class GenerationResult:
    dna: SiteDNA
    trace: DesignDecisionTrace


@dataclass(frozen=True)
class ClaimRequirement:
    claim_type: str
    required_field: str
    expected_value: Any | None = None
    description: str = ""
