"""Twelve architecture expectations used to validate composition scoring."""

from __future__ import annotations

from dataclasses import dataclass

from .models import SiteDNA
from .composition import composition_report


@dataclass(frozen=True)
class GoldenCompositionCase:
    id: str
    expected_family_terms: tuple[str, ...]
    preferred_patterns: tuple[str, ...]
    media_direction: str
    conversion_behavior: str
    forbidden_repetitions: tuple[str, ...]


GOLDEN_COMPOSITION_CASES = (
    GoldenCompositionCase("local_emergency_plumber", ("conversion", "contact", "phone"), ("conversion_problem_solution", "phone_action"), "balanced", "phone_first", ("monumental", "cinematic")),
    GoldenCompositionCase("premium_residential_plumber", ("split_photo", "project", "quote"), ("split_editorial", "project_grid"), "media_led", "quote_first", ("technical_explainer",)),
    GoldenCompositionCase("technical_electrician", ("technical", "matrix"), ("technical_explainer", "capability_matrix"), "supporting", "diagnostic", ("cinematic_scene",)),
    GoldenCompositionCase("warm_craft_carpenter", ("material", "documentary"), ("material_study", "documentary_process"), "media_led", "consultation", ("emergency_phone",)),
    GoldenCompositionCase("editorial_painter", ("collage", "rows", "editorial"), ("asymmetric_editorial_collage", "editorial_rows"), "media_led", "quiet_contact", ("capability_matrix",)),
    GoldenCompositionCase("architectural_mason", ("project", "rail", "technical"), ("project_evidence_intro", "horizontal_rail"), "media_led", "project_brief", ("soft_residential",)),
    GoldenCompositionCase("luxury_renovation", ("cinematic", "project"), ("cinematic_scene", "editorial_casebook"), "cinematic", "project_brief", ("emergency_phone",)),
    GoldenCompositionCase("family_trust_local", ("local", "facts", "contact"), ("local_information", "verified_fact_index"), "supporting", "contact", ("monumental_action",)),
    GoldenCompositionCase("technical_b2b", ("technical", "matrix", "business"), ("technical_explainer", "capability_matrix"), "supporting", "diagnostic", ("warm_craft",)),
    GoldenCompositionCase("quiet_luxury", ("typographic", "minimal", "editorial"), ("typographic_statement", "quiet_statement"), "quiet", "quiet_contact", ("three_monumental",)),
    GoldenCompositionCase("documentary_craft", ("documentary", "material", "project"), ("documentary_work_log", "material_study"), "media_led", "consultation", ("stock_as_project",)),
    GoldenCompositionCase("project_portfolio", ("project", "gallery", "rail"), ("project_evidence_intro", "project_grid"), "media_led", "project_brief", ("ambient_only",)),
)


def score_golden_composition(dna: SiteDNA, case: GoldenCompositionCase) -> tuple[float, tuple[str, ...]]:
    report = composition_report(dna)
    families = tuple(item.family_id for item in report.components)
    family_matches = sum(any(term in family for family in families) for term in case.expected_family_terms)
    pattern_matches = sum(pattern in report.layout_rhythm for pattern in case.preferred_patterns)
    forbidden = sum(
        1 for marker in case.forbidden_repetitions
        if marker in report.layout_rhythm or marker in report.type_rhythm
    )
    score = family_matches / max(1, len(case.expected_family_terms)) * .55
    score += pattern_matches / max(1, len(case.preferred_patterns)) * .30
    score += .15 if forbidden == 0 else 0.0
    reasons = (
        f"family_matches:{family_matches}/{len(case.expected_family_terms)}",
        f"pattern_matches:{pattern_matches}/{len(case.preferred_patterns)}",
        f"forbidden_hits:{forbidden}",
        f"media_direction:{case.media_direction}",
        f"conversion_behavior:{case.conversion_behavior}",
    )
    return round(score, 4), reasons
