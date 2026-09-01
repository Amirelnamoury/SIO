"""Explainable technical quality scoring; never an aesthetic certification."""

from __future__ import annotations

from .data.color_systems import COLOR_SYSTEMS
from .data.systems import MOBILE_PERSONALITIES, MOTION_SYSTEMS, SPATIAL_SYSTEMS
from .data.typography_systems import TYPOGRAPHY_SYSTEMS
from .models import DesignInput, DesignQualityReport, SiteDNA
from .rhythm import evaluate_rhythm
from .data.components import ALL_COMPONENTS


def evaluate_quality(dna: SiteDNA, design_input: DesignInput, originality: float = 1.0) -> DesignQualityReport:
    color = COLOR_SYSTEMS[dna.color_system]
    typography = TYPOGRAPHY_SYSTEMS[dna.typography_system]
    motion = MOTION_SYSTEMS[dna.motion_system]
    spatial = SPATIAL_SYSTEMS[dna.spatial_system]
    mobile = MOBILE_PERSONALITIES[dna.mobile_personality]
    components = tuple(
        ALL_COMPONENTS[value]
        for value in (
            dna.header_component, dna.hero_component, dna.services_component,
            dna.gallery_component, dna.about_component, dna.trust_component,
            dna.cta_component, dna.contact_component, dna.footer_component, dna.form_component,
        ) if value
    )
    rhythm = evaluate_rhythm(components)
    contrast = min(1.0, color.contrast_score / 7.0)
    readability = typography.readability_score
    media_need = sum(component.image_dependency for component in components) / max(1, len(components))
    media_supply = min(1.0, (design_input.media.artisan_photos + design_input.media.stock_photos) / 6)
    media_fit = 1.0 - max(0.0, media_need - media_supply)
    conversion = 1.0 - abs(dna.conversion_intensity - (
        .85 if design_input.business_intent in {"emergency", "quote", "phone"} else .5
    ))
    mobile_fit = 1.0 - max(0, motion.performance_cost - 2) * .08 - max(0, spatial.performance_cost - 2) * .08
    mobile_fit += .05 if mobile.motion_policy in {"none", "static", "reduced", "micro_only"} else 0
    mobile_fit = max(0.0, min(1.0, mobile_fit))
    coherence = .82 if dna.art_direction in dna.photo_direction else .68
    hierarchy = min(1.0, .6 + rhythm.score * .4)
    content_fit = .9 if "services" in design_input.available_data else .55
    business_fit = max(.0, min(1.0, conversion))
    overdesign = min(1.0, (motion.intensity + spatial.level) / 10 + max(0, dna.density - 4) * .12)
    underdesign = .55 if len(dna.section_order) < 5 else .12
    total = (
        coherence * .12 + hierarchy * .10 + readability * .10 + contrast * .10
        + rhythm.score * .10 + conversion * .10 + content_fit * .10 + media_fit * .08
        + business_fit * .08 + mobile_fit * .07 + originality * .05
    ) * 100
    notes = tuple(rhythm.issues)
    return DesignQualityReport(
        round(total, 2), round(coherence, 3), round(hierarchy, 3), round(readability, 3),
        round(contrast, 3), round(rhythm.score, 3), round(conversion, 3), round(content_fit, 3),
        round(media_fit, 3), round(business_fit, 3), round(mobile_fit, 3), round(originality, 3),
        round(overdesign, 3), round(underdesign, 3), notes,
    )
