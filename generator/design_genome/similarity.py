"""Explainable, structure-first visual similarity for anti-clone checks."""

from __future__ import annotations

from functools import lru_cache

from .blueprints import blueprint_structural_distance
from .composition import component_entries_from_payload
from .data.components import ALL_COMPONENTS
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


def _sequence_distance(left: tuple[object, ...], right: tuple[object, ...]) -> float:
    size = max(len(left), len(right), 1)
    return sum(
        0.0 if index < len(left) and index < len(right) and left[index] == right[index] else 1.0
        for index in range(size)
    ) / size


@lru_cache(maxsize=None)
def _component_blueprint_distance(left_id: str, right_id: str) -> float:
    return blueprint_structural_distance(ALL_COMPONENTS[left_id], ALL_COMPONENTS[right_id]).distance


def compare_dna(left: SiteDNA, right: SiteDNA, *, include_color: bool = True, include_typography: bool = True) -> SimilarityReport:
    structural = (
        _different(left.page_silhouette, right.page_silhouette) * .38
        + _different(left.grid_system, right.grid_system) * .24
        + _different(left.spacing_system, right.spacing_system) * .18
        + _different(left.geometry_system, right.geometry_system) * .14
        + _different(left.site_archetype, right.site_archetype) * .06
    )
    typographic = _different(left.typography_system, right.typography_system)
    chromatic = _different(left.color_system, right.color_system)

    left_entries = component_entries_from_payload(left.to_dict())
    right_entries = component_entries_from_payload(right.to_dict())
    left_by_section = {entry.section: entry for entry in left_entries}
    right_by_section = {entry.section: entry for entry in right_entries}
    sections = sorted(set(left_by_section) | set(right_by_section))
    blueprint_distances = []
    family_distances = []
    id_distances = []
    for section in sections:
        left_entry = left_by_section.get(section)
        right_entry = right_by_section.get(section)
        if left_entry is None or right_entry is None:
            blueprint_distances.append(1.0)
            family_distances.append(1.0)
            id_distances.append(1.0)
            continue
        blueprint_distances.append(_component_blueprint_distance(left_entry.component_id, right_entry.component_id))
        family_distances.append(_different(left_entry.family_id, right_entry.family_id))
        id_distances.append(_different(left_entry.component_id, right_entry.component_id))
    blueprint_distance = sum(blueprint_distances) / max(1, len(blueprint_distances))
    family_distance = sum(family_distances) / max(1, len(family_distances))
    components = sum(id_distances) / max(1, len(id_distances))

    narrative = _sequence_distance(left.section_order, right.section_order)
    layout_rhythm = _sequence_distance(
        tuple(entry.layout_pattern for entry in left_entries),
        tuple(entry.layout_pattern for entry in right_entries),
    )
    edge_rhythm = _sequence_distance(
        tuple(entry.edge_behavior for entry in left_entries),
        tuple(entry.edge_behavior for entry in right_entries),
    )
    media_rhythm = _sequence_distance(
        tuple(entry.media_intensity for entry in left_entries),
        tuple(entry.media_intensity for entry in right_entries),
    )
    type_rhythm = _sequence_distance(
        tuple(entry.type_scale_role for entry in left_entries),
        tuple(entry.type_scale_role for entry in right_entries),
    )
    combined_rhythm = layout_rhythm * .40 + edge_rhythm * .20 + media_rhythm * .24 + type_rhythm * .16
    photo = _different(left.photo_direction, right.photo_direction)

    weights = {
        "structural": .13, "blueprint": .36, "family": .11, "component_id": .03,
        "rhythm": .14, "narrative": .08, "photo": .04,
        "typography": .08 if include_typography else 0.0,
        "color": .03 if include_color else 0.0,
    }
    total_weight = sum(weights.values())
    distance = (
        structural * weights["structural"] + blueprint_distance * weights["blueprint"]
        + family_distance * weights["family"] + components * weights["component_id"]
        + combined_rhythm * weights["rhythm"] + narrative * weights["narrative"]
        + photo * weights["photo"] + typographic * weights["typography"]
        + chromatic * weights["color"]
    ) / total_weight
    return SimilarityReport(
        round(structural, 4), round(typographic, 4), round(chromatic, 4),
        round(components, 4), round(narrative, 4), round(photo, 4),
        round(1.0 - distance, 4), round(blueprint_distance, 4),
        round(family_distance, 4), round(combined_rhythm, 4),
    )


def maximum_similarity(candidate: SiteDNA, history: tuple[SiteDNA, ...]) -> float:
    return max((compare_dna(candidate, previous).overall_visual_similarity for previous in history), default=0.0)


def similarity_band(score: float) -> str:
    for minimum, maximum, label in SIMILARITY_BANDS:
        if minimum <= score < maximum:
            return label
    raise ValueError(f"Similarity score outside 0..1: {score}")
