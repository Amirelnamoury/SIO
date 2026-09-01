"""Audit explicit component variants and their registry-order independence."""

from __future__ import annotations

import ast
import json
from pathlib import Path

from ..blueprints import blueprint_fingerprint
from ..data.components import COMPONENT_REGISTRIES
from ..data.components._factory import registry
from ..data.components.about import ABOUT_GROUPS
from ..data.components.contacts import CONTACT_GROUPS, FORM_GROUPS
from ..data.components.ctas import CTA_GROUPS
from ..data.components.footers import FOOTER_GROUPS
from ..data.components.galleries import GALLERY_GROUPS
from ..data.components.headers import HEADER_GROUPS
from ..data.components.heroes import HERO_GROUPS
from ..data.components.profiles import (
    ABOUT_PROFILES, CONTACT_PROFILES, CTA_PROFILES, FOOTER_PROFILES,
    FORM_PROFILES, GALLERY_PROFILES, HEADER_PROFILES, HERO_PROFILES,
    SERVICES_PROFILES, TRUST_PROFILES,
)
from ..data.components.services import SERVICE_GROUPS
from ..data.components.trust import TRUST_GROUPS
from ..data.components.variants import (
    ABOUT_VARIANTS, CONTACT_VARIANTS, CTA_VARIANTS, FOOTER_VARIANTS,
    FORM_VARIANTS, GALLERY_VARIANTS, HEADER_VARIANTS, HERO_VARIANTS,
    SERVICES_VARIANTS, TRUST_VARIANTS,
)


CASES = (
    ("header", HEADER_GROUPS, HEADER_PROFILES, HEADER_VARIANTS, {"phone_first_compact": {"required_data": ("phone",), "required_any_data": ()}}),
    ("hero", HERO_GROUPS, HERO_PROFILES, HERO_VARIANTS, {"phone_first_problem_solution": {"required_data": ("phone",), "required_any_data": ()}}),
    ("services", SERVICE_GROUPS, SERVICES_PROFILES, SERVICES_VARIANTS, {}),
    ("gallery", GALLERY_GROUPS, GALLERY_PROFILES, GALLERY_VARIANTS, {}),
    ("about", ABOUT_GROUPS, ABOUT_PROFILES, ABOUT_VARIANTS, {}),
    ("trust", TRUST_GROUPS, TRUST_PROFILES, TRUST_VARIANTS, {}),
    ("cta", CTA_GROUPS, CTA_PROFILES, CTA_VARIANTS, {}),
    ("contact", CONTACT_GROUPS, CONTACT_PROFILES, CONTACT_VARIANTS, {}),
    ("footer", FOOTER_GROUPS, FOOTER_PROFILES, FOOTER_VARIANTS, {}),
    ("form", FORM_GROUPS, FORM_PROFILES, FORM_VARIANTS, {}),
)


def audit() -> dict:
    issues: list[str] = []
    stable = 0
    for category, groups, profiles, variants, overrides in CASES:
        reversed_groups = {
            profile: tuple(reversed(component_ids))
            for profile, component_ids in reversed(tuple(groups.items()))
        }
        rebuilt = registry(category, reversed_groups, profiles, variants, overrides)
        for component_id, component in COMPONENT_REGISTRIES[category].items():
            if component.variant_source != "explicit":
                issues.append(f"{component_id}:variant_source={component.variant_source}")
            if not component.design_intent.strip():
                issues.append(f"{component_id}:missing_design_intent")
            if rebuilt[component_id].variant_id != component.variant_id:
                issues.append(f"{component_id}:variant_changed_after_reorder")
            if rebuilt[component_id].blueprint_spec != component.blueprint_spec:
                issues.append(f"{component_id}:structural_spec_changed_after_reorder")
            if blueprint_fingerprint(rebuilt[component_id]) != blueprint_fingerprint(component):
                issues.append(f"{component_id}:fingerprint_changed_after_reorder")
            stable += 1

    factory_path = Path(__file__).parents[1] / "data" / "components" / "_factory.py"
    source = factory_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    if "variant_index" in source or "STRUCTURAL_VARIANTS" in source:
        issues.append("factory:positional_variant_symbol")
    if any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "enumerate" for node in ast.walk(tree)):
        issues.append("factory:enumerate_call")
    if any(isinstance(node, ast.Mod) for node in ast.walk(tree)):
        issues.append("factory:modulo_operation")

    return {
        "components_checked": stable,
        "explicit_variants": sum(component.variant_source == "explicit" for registry_items in COMPONENT_REGISTRIES.values() for component in registry_items.values()),
        "order_independent": not any("reorder" in issue for issue in issues),
        "fingerprint_stable": not any("fingerprint" in issue for issue in issues),
        "positional_factory_constructs": [issue for issue in issues if issue.startswith("factory:")],
        "issues": issues,
    }


def main() -> None:
    result = audit()
    print(json.dumps(result, indent=2))
    if result["issues"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
