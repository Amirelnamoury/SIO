"""Static lint rules for a SiteDNA candidate and its factual inputs."""

from __future__ import annotations

from .data.color_systems import COLOR_SYSTEMS
from .data.color_systems import contrast_ratio
from .data.components import ALL_COMPONENTS
from .data.systems import MOTION_SYSTEMS, SPATIAL_SYSTEMS
from .data.typography_systems import TYPOGRAPHY_SYSTEMS
from .archetypes import ARCHETYPES
from .compatibility import evaluate_component
from .data_truth import TruthClass, validate_claims
from .models import DesignInput, LintIssue, SiteDNA
from .rhythm import evaluate_rhythm, ordered_dna_components
from .taxonomy import normalize_business_intent


def lint_dna(dna: SiteDNA, design_input: DesignInput) -> tuple[LintIssue, ...]:
    issues: list[LintIssue] = []
    components = ordered_dna_components(dna)
    rhythm = evaluate_rhythm(components)
    for issue in rhythm.issues:
        code = "heavy_section_sequence" if issue.startswith("three_heavy") else "duplicate_component_pattern" if issue.startswith("duplicate_component_pattern") else "rhythm"
        issues.append(LintIssue(code, "warning", issue, "section_order"))

    color = COLOR_SYSTEMS[dna.color_system]
    if color.contrast_score < 4.5:
        issues.append(LintIssue("contrast", "error", "Core text contrast is below WCAG AA.", "color_system"))
    if contrast_ratio(color.tokens["text_secondary"], color.tokens["canvas"]) < 4.5:
        issues.append(LintIssue("low_contrast_secondary", "error", "Secondary text contrast is below WCAG AA.", "color_system"))
    if dna.gallery_component and not (design_input.media.artisan_photos or design_input.media.stock_photos):
        issues.append(LintIssue("empty_gallery", "error", "Gallery selected without usable media.", "gallery_component"))
    if dna.gallery_component:
        gallery = ALL_COMPONENTS[dna.gallery_component]
        if gallery.allowed_media_sources == frozenset({"artisan"}) and not design_input.media.project_photos:
            issues.append(LintIssue("stock_as_project", "error", "Project evidence requires artisan project media.", "gallery_component"))
    hero = ALL_COMPONENTS[dna.hero_component]
    hero_media = hero.blueprint_spec.media_spec
    if hero_media.get("supports_no_media") and (hero.required_media or hero.required_any_media or hero.image_dependency > 0):
        issues.append(LintIssue("no_image_requires_image", "error", "No-media hero has a contradictory media requirement.", "hero_component"))
    orientations = set(hero_media.get("preferred_orientations", ()))
    if hero.required_any_media and "landscape" in orientations and not design_input.media.landscape_photos and not design_input.media.stock_photos:
        issues.append(LintIssue("hero_media_orientation", "warning", "Preferred landscape hero media is unavailable.", "hero_component"))
    if dna.contact_component and not ({"phone", "email"} & design_input.available_data):
        issues.append(LintIssue("missing_contact", "error", "Contact component has no verified contact channel.", "contact_component"))
    conversion_intents = {"emergency", "local_quote", "trust_first"}
    if normalize_business_intent(design_input.business_intent) in conversion_intents and not (dna.cta_component or dna.contact_component):
        has_contact_channel = bool({"phone", "email"} & design_input.available_data)
        issues.append(LintIssue(
            "missing_primary_action_for_conversion_site",
            "error" if has_contact_channel else "warning",
            "Conversion intent requires one viable primary action; no verified contact channel is available."
            if not has_contact_channel
            else "Conversion intent has a verified channel but no viable primary action.",
            "cta_component",
        ))
    action_count = sum(bool(value) for value in (dna.cta_component, dna.contact_component, dna.form_component))
    if action_count > 3:
        issues.append(LintIssue("too_many_ctas", "warning", "Too many competing conversion structures.", "cta_component"))
    typography = TYPOGRAPHY_SYSTEMS[dna.typography_system]
    if typography.max_font_count > 3:
        issues.append(LintIssue("too_many_type_styles", "error", "Typography system exceeds the three-family policy.", "typography_system"))
    if MOTION_SYSTEMS[dna.motion_system].intensity >= 4 and SPATIAL_SYSTEMS[dna.spatial_system].level >= 4:
        issues.append(LintIssue("overdesign", "warning", "Heavy motion and spatial systems are combined.", "motion_system"))
    if MOTION_SYSTEMS[dna.motion_system].intensity >= 3 and "static" not in hero.blueprint_spec.fallback_strategy.lower() and hero.profile == "spatial":
        issues.append(LintIssue("mobile_incompatibility", "warning", "Spatial hero needs an explicit static fallback.", "mobile_personality"))
    archetype = ARCHETYPES[dna.site_archetype]
    if design_input.trade not in archetype.compatible_trades:
        issues.append(LintIssue("archetype_mismatch", "error", "Archetype is incompatible with the trade grammar.", "site_archetype"))
    selected_ids: tuple[str, ...] = ()
    for component in components:
        result = evaluate_component(component, design_input, archetype, dna.art_direction, selected_ids)
        if not result.allowed:
            issues.append(LintIssue("component_constraint", "error", "; ".join(result.hard_failures), component.id))
        selected_ids += (component.id,)
    claims = tuple(design_input.facts.get("claims", ()))
    for assessment in validate_claims(claims, design_input.facts):
        if assessment.classification == TruthClass.FORBIDDEN_INVENTION:
            issues.append(LintIssue("unsupported_claim", "error", f"Unsupported claim: {assessment.claim}", "facts.claims"))
    if not dna.design_signature:
        issues.append(LintIssue("signature", "error", "SiteDNA must carry a stable design signature.", "design_signature"))
    return tuple(issues)
