"""Explainable technical quality scoring; never an aesthetic certification."""

from __future__ import annotations

from .data.color_systems import COLOR_SYSTEMS
from .data.systems import MOBILE_PERSONALITIES, MOTION_SYSTEMS, SPATIAL_SYSTEMS
from .data.typography_systems import TYPOGRAPHY_SYSTEMS
from .models import DesignInput, DesignQualityReport, SiteDNA
from .rhythm import evaluate_rhythm, ordered_dna_components
from .taxonomy import normalize_business_intent


def evaluate_quality(dna: SiteDNA, design_input: DesignInput, originality: float = 1.0) -> DesignQualityReport:
    color = COLOR_SYSTEMS[dna.color_system]
    typography = TYPOGRAPHY_SYSTEMS[dna.typography_system]
    motion = MOTION_SYSTEMS[dna.motion_system]
    spatial = SPATIAL_SYSTEMS[dna.spatial_system]
    mobile = MOBILE_PERSONALITIES[dna.mobile_personality]
    components = ordered_dna_components(dna)
    rhythm = evaluate_rhythm(components)
    contrast = min(1.0, color.contrast_score / 7.0)
    readability = typography.readability_score
    media_need = sum(component.image_dependency for component in components) / max(1, len(components))
    media_supply = min(1.0, (design_input.media.artisan_photos + design_input.media.stock_photos) / 6)
    media_fit = 1.0 - max(0.0, media_need - media_supply)
    intent = normalize_business_intent(design_input.business_intent)
    target_conversion = .92 if intent in {"emergency", "local_quote"} else .68 if intent in {"trust_first", "technical_expertise"} else .42 if intent in {"portfolio", "craft"} else .55
    conversion = 1.0 - abs(dna.conversion_intensity - target_conversion)
    mobile_fit = 1.0 - max(0, motion.performance_cost - 2) * .08 - max(0, spatial.performance_cost - 2) * .08
    mobile_fit += .05 if mobile.motion_policy in {"none", "static", "reduced", "micro_only"} else 0
    mobile_fit = max(0.0, min(1.0, mobile_fit))
    profile_counts = {}
    for component in components:
        profile_counts[component.profile] = profile_counts.get(component.profile, 0) + 1
    repeated_profiles = sum(max(0, count - 2) for count in profile_counts.values())
    dense_sections = sum(component.density >= 4 for component in components)
    heavy_sections = sum(component.visual_weight >= 4 for component in components)
    coherence = .84 if dna.art_direction in dna.photo_direction else .62
    coherence -= repeated_profiles * .04
    hierarchy = min(1.0, .6 + rhythm.score * .4)
    content_fit = .9 if "services" in design_input.available_data else .55
    business_fit = max(.0, min(1.0, conversion - (0.08 if intent == "emergency" and not dna.cta_component else 0)))
    overdesign = min(1.0, (motion.intensity + spatial.level) / 10 + max(0, dense_sections - 3) * .08 + max(0, heavy_sections - 3) * .06)
    identity_dimensions = len({dna.page_silhouette, dna.hero_component, dna.typography_system, dna.grid_system, dna.geometry_system})
    underdesign = min(1.0, (.48 if len(dna.section_order) < 5 else .10) + (.25 if identity_dimensions < 4 else 0))
    total = (
        coherence * .12 + hierarchy * .10 + readability * .10 + contrast * .10
        + rhythm.score * .10 + conversion * .10 + content_fit * .10 + media_fit * .08
        + business_fit * .08 + mobile_fit * .07 + originality * .05
    ) * 100
    notes = tuple(rhythm.issues) + tuple(
        note for condition, note in (
            (dense_sections > 4, "too_many_dense_sections"),
            (heavy_sections > 4, "too_many_heavy_sections"),
            (repeated_profiles > 1, "too_many_similar_component_profiles"),
            (media_fit < .65, "wrong_media_strategy"),
            (mobile_fit < .7, "mobile_conflict"),
            (business_fit < .65, "wrong_business_or_conversion_fit"),
            (underdesign > .4, "insufficient_identity"),
        ) if condition
    )
    return DesignQualityReport(
        round(total, 2), round(coherence, 3), round(hierarchy, 3), round(readability, 3),
        round(contrast, 3), round(rhythm.score, 3), round(conversion, 3), round(content_fit, 3),
        round(media_fit, 3), round(business_fit, 3), round(mobile_fit, 3), round(originality, 3),
        round(overdesign, 3), round(underdesign, 3), notes,
    )
