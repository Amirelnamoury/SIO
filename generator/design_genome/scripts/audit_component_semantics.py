"""Audit all component definitions for known semantic contradictions."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from ..data.components import ALL_COMPONENTS
from ..models import ComponentDefinition
from ..taxonomy import ENERGY_LEVELS


VALID_CATEGORIES = {"header", "hero", "services", "gallery", "about", "trust", "cta", "contact", "footer", "form"}
REQUIRED_SPEC_KEYS = {
    "header": ({"brand_placement", "nav_placement", "cta_placement"}, {"navigation_behavior"}),
    "hero": ({"grid_columns", "content_span", "media_span", "desktop_order"}, {"mobile_order", "media_behavior", "title_behavior"}),
    "services": ({"item_layout", "columns", "item_density"}, {"transformation"}),
    "gallery": ({"layout_behavior", "item_count_min", "item_count_max"}, {"transformation"}),
    "about": ({"narrative_zones", "image_placement", "facts_placement"}, {"order"}),
    "trust": ({"visual_structure", "maximum_facts"}, {"transformation"}),
    "cta": ({"section_scale", "primary_action"}, {"transformation"}),
    "contact": ({"details_form_balance", "cta_hierarchy"}, {"order"}),
    "footer": ({"columns", "brand_placement", "legal"}, {"order"}),
    "form": ({"field_layout", "steps", "label_position"}, {"transformation"}),
}


@dataclass(frozen=True)
class AuditRow:
    component: str
    category: str
    issues: tuple[str, ...]
    resolution: str


def audit_component(component: ComponentDefinition) -> AuditRow:
    issues: list[str] = []
    spec = component.blueprint_spec
    if component.category not in VALID_CATEGORIES:
        issues.append("invalid_category")
    if not component.id or component.id.lower() != component.id:
        issues.append("invalid_id")
    if not component.traits:
        issues.append("missing_traits")
    if not 1 <= component.density <= 5:
        issues.append("invalid_density")
    if not 1 <= component.visual_weight <= 5:
        issues.append("invalid_visual_weight")
    if component.section_energy not in ENERGY_LEVELS:
        issues.append("invalid_section_energy")
    if not component.mobile_variant:
        issues.append("missing_mobile_variant")
    if not component.content_zones:
        issues.append("missing_content_zones")
    if spec is None:
        issues.append("missing_blueprint_spec")
    else:
        desktop_keys, mobile_keys = REQUIRED_SPEC_KEYS[component.category]
        if not desktop_keys <= set(spec.desktop_spec):
            issues.append("incomplete_desktop_spec")
        if not mobile_keys <= set(spec.mobile_spec):
            issues.append("incomplete_mobile_spec")
        if not spec.fallback_strategy:
            issues.append("missing_fallback")
    if component.required_data & component.required_any_data:
        issues.append("impossible_duplicate_data_requirement")
    if component.required_media & component.required_any_media:
        issues.append("impossible_duplicate_media_requirement")

    identifier = component.id
    media_spec = spec.media_spec if spec else {}
    if identifier.startswith("no_image_") and (
        component.required_media or component.required_any_media or component.image_dependency > 0
        or not media_spec.get("supports_no_media")
    ):
        issues.append("no_image_requires_image")
    if "before_after" in identifier and (
        "before_after" not in component.required_media or "stock" in component.allowed_media_sources
    ):
        issues.append("before_after_allows_stock")
    project_evidence_categories = {"hero", "gallery", "about", "trust"}
    if component.category in project_evidence_categories and any(token in identifier for token in ("artisan_project", "project_grid", "project_cards", "project_folio", "casebook", "work_log", "progress_ledger")):
        if "artisan_project" not in component.required_media or "stock" in component.allowed_media_sources:
            issues.append("project_evidence_allows_stock")
    if "phone" in identifier and component.category in {"header", "hero", "cta", "contact"}:
        if "phone" not in component.required_data:
            issues.append("phone_without_requirement")
    if any(token in identifier for token in ("testimonial", "review_")) and component.category == "trust" and "reviews" not in component.required_data:
        issues.append("testimonial_without_reviews")
    if "insurance" in identifier and "insurance" not in component.required_data:
        issues.append("insurance_without_requirement")
    if "certification" in identifier and "certifications" not in component.required_data:
        issues.append("certification_without_requirement")
    if "statistics" in identifier and "statistics" not in component.required_data:
        issues.append("statistics_without_facts")
    if component.category == "contact" and not (component.required_data & {"phone", "email"} or component.required_any_data & {"phone", "email"}):
        issues.append("contact_without_channel")
    if component.category == "trust" and "trust_led" not in component.traits:
        issues.append("trust_category_without_trait")
    if component.category in {"cta", "contact", "form"} and "conversion_led" not in component.traits and component.category != "form":
        issues.append("conversion_category_without_trait")

    resolution = "explicit profile and blueprint validated" if not issues else "requires semantic profile correction"
    return AuditRow(component.id, component.category, tuple(issues), resolution)


def audit_all() -> tuple[AuditRow, ...]:
    return tuple(audit_component(component) for component in ALL_COMPONENTS.values())


def render_report(rows: tuple[AuditRow, ...]) -> str:
    failing = [row for row in rows if row.issues]
    lines = [
        "# Component semantic audit", "",
        "Generated by `python -m generator.design_genome.scripts.audit_component_semantics`.", "",
        f"- Components audited: {len(rows)}",
        f"- Known semantic errors: {len(failing)}",
        "- Runtime semantic inference from component IDs: 0", "",
        "The ID checks below are audit assertions only. Runtime metadata comes exclusively from explicit profile assignments.", "",
        "| Component | Category | Issues | Resolution |", "|---|---|---|---|",
    ]
    for row in sorted(rows, key=lambda item: (item.category, item.component)):
        lines.append(f"| `{row.component}` | {row.category} | {', '.join(row.issues) or 'none'} | {row.resolution} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("docs/design-encyclopedia/component-semantic-audit.md"))
    args = parser.parse_args()
    rows = audit_all()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_report(rows), encoding="utf-8")
    failing = [row for row in rows if row.issues]
    print(f"audited={len(rows)} errors={len(failing)}")
    if failing:
        for row in failing:
            print(row.component, ",".join(row.issues))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
