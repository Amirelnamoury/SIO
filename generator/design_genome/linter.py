"""Static lint rules for a SiteDNA candidate and its factual inputs."""

from __future__ import annotations

from .data.color_systems import COLOR_SYSTEMS
from .data.components import ALL_COMPONENTS
from .data.systems import MOTION_SYSTEMS, SPATIAL_SYSTEMS
from .models import DesignInput, LintIssue, SiteDNA
from .rhythm import evaluate_rhythm


def lint_dna(dna: SiteDNA, design_input: DesignInput) -> tuple[LintIssue, ...]:
    issues: list[LintIssue] = []
    values = (
        dna.header_component, dna.hero_component, dna.services_component,
        dna.gallery_component, dna.about_component, dna.trust_component,
        dna.cta_component, dna.contact_component, dna.footer_component, dna.form_component,
    )
    components = tuple(ALL_COMPONENTS[value] for value in values if value)
    rhythm = evaluate_rhythm(components)
    for issue in rhythm.issues:
        issues.append(LintIssue("rhythm", "warning", issue, "section_order"))

    color = COLOR_SYSTEMS[dna.color_system]
    if color.contrast_score < 4.5:
        issues.append(LintIssue("contrast", "error", "Core text contrast is below WCAG AA.", "color_system"))
    if dna.gallery_component and not (design_input.media.artisan_photos or design_input.media.stock_photos):
        issues.append(LintIssue("empty_gallery", "error", "Gallery selected without usable media.", "gallery_component"))
    if dna.gallery_component:
        gallery = ALL_COMPONENTS[dna.gallery_component]
        if gallery.allowed_media_sources == frozenset({"artisan"}) and not design_input.media.project_photos:
            issues.append(LintIssue("stock_as_project", "error", "Project evidence requires artisan project media.", "gallery_component"))
    if dna.contact_component and not ({"phone", "email"} & design_input.available_data):
        issues.append(LintIssue("missing_contact", "error", "Contact component has no verified contact channel.", "contact_component"))
    if MOTION_SYSTEMS[dna.motion_system].intensity >= 4 and SPATIAL_SYSTEMS[dna.spatial_system].level >= 4:
        issues.append(LintIssue("overdesign", "warning", "Heavy motion and spatial systems are combined.", "motion_system"))
    if not dna.design_signature:
        issues.append(LintIssue("signature", "error", "SiteDNA must carry a stable design signature.", "design_signature"))
    return tuple(issues)
