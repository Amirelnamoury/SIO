"""Explainable visual similarity for anti-clone checks."""

from __future__ import annotations

from .models import SimilarityReport, SiteDNA


SIMILARITY_BANDS = (
    (0.00, 0.40, "clearly_distinct"),
    (0.40, 0.60, "related"),
    (0.60, 0.75, "visually_similar"),
    (0.75, 0.84, "near_clone"),
    (0.84, 1.01, "reject"),
)


def _different(left: str | None, right: str | None) -> float:
    return 0.0 if left == right else 1.0


def compare_dna(left: SiteDNA, right: SiteDNA) -> SimilarityReport:
    structural = (
        _different(left.page_silhouette, right.page_silhouette) * .38
        + _different(left.grid_system, right.grid_system) * .22
        + _different(left.spacing_system, right.spacing_system) * .14
        + _different(left.geometry_system, right.geometry_system) * .12
        + _different(left.site_archetype, right.site_archetype) * .14
    )
    typographic = _different(left.typography_system, right.typography_system)
    chromatic = _different(left.color_system, right.color_system)
    components = (
        _different(left.header_component, right.header_component) * .10
        + _different(left.hero_component, right.hero_component) * .25
        + _different(left.services_component, right.services_component) * .20
        + _different(left.gallery_component, right.gallery_component) * .10
        + _different(left.about_component, right.about_component) * .08
        + _different(left.trust_component, right.trust_component) * .07
        + _different(left.cta_component, right.cta_component) * .06
        + _different(left.contact_component, right.contact_component) * .07
        + _different(left.footer_component, right.footer_component) * .07
    )
    left_sections = set(left.section_order)
    right_sections = set(right.section_order)
    union = left_sections | right_sections
    narrative = 1.0 - len(left_sections & right_sections) / max(1, len(union))
    photo = _different(left.photo_direction, right.photo_direction)

    distance = (
        structural * .18 + typographic * .15 + chromatic * .05
        + components * .38 + narrative * .16 + photo * .08
    )
    return SimilarityReport(
        round(structural, 4), round(typographic, 4), round(chromatic, 4),
        round(components, 4), round(narrative, 4), round(photo, 4),
        round(1.0 - distance, 4),
    )


def maximum_similarity(candidate: SiteDNA, history: tuple[SiteDNA, ...]) -> float:
    return max((compare_dna(candidate, previous).overall_visual_similarity for previous in history), default=0.0)


def similarity_band(score: float) -> str:
    for minimum, maximum, label in SIMILARITY_BANDS:
        if minimum <= score < maximum:
            return label
    raise ValueError(f"Similarity score outside 0..1: {score}")
