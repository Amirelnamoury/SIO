"""Explainable visual similarity for anti-clone checks."""

from __future__ import annotations

from .models import SimilarityReport, SiteDNA


def _different(left: str | None, right: str | None) -> float:
    return 0.0 if left == right else 1.0


def compare_dna(left: SiteDNA, right: SiteDNA) -> SimilarityReport:
    structural = sum((
        _different(left.page_silhouette, right.page_silhouette),
        _different(left.grid_system, right.grid_system),
        _different(left.spacing_system, right.spacing_system),
        _different(left.geometry_system, right.geometry_system),
    )) / 4
    typographic = _different(left.typography_system, right.typography_system)
    chromatic = _different(left.color_system, right.color_system)
    components = (
        _different(left.header_component, right.header_component)
        + _different(left.hero_component, right.hero_component)
        + _different(left.services_component, right.services_component)
        + _different(left.gallery_component, right.gallery_component)
        + _different(left.about_component, right.about_component)
        + _different(left.trust_component, right.trust_component)
        + _different(left.cta_component, right.cta_component)
        + _different(left.contact_component, right.contact_component)
        + _different(left.footer_component, right.footer_component)
    ) / 9
    left_sections = set(left.section_order)
    right_sections = set(right.section_order)
    union = left_sections | right_sections
    narrative = 1.0 - len(left_sections & right_sections) / max(1, len(union))
    photo = _different(left.photo_direction, right.photo_direction)

    distance = (
        structural * .24 + typographic * .14 + chromatic * .14
        + components * .28 + narrative * .12 + photo * .08
    )
    return SimilarityReport(
        round(structural, 4), round(typographic, 4), round(chromatic, 4),
        round(components, 4), round(narrative, 4), round(photo, 4),
        round(1.0 - distance, 4),
    )


def maximum_similarity(candidate: SiteDNA, history: tuple[SiteDNA, ...]) -> float:
    return max((compare_dna(candidate, previous).overall_visual_similarity for previous in history), default=0.0)
