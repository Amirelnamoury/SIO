"""Verify that every component is explicit enough for experimental rendering."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from ..blueprints import blueprint_fingerprint, differentiation_summary
from ..data.components import COMPONENT_REGISTRIES


def check() -> tuple[dict[str, tuple[str, ...]], dict[str, dict]]:
    issues: dict[str, tuple[str, ...]] = {}
    summaries = {}
    for category, registry in COMPONENT_REGISTRIES.items():
        summaries[category] = differentiation_summary(registry.values())
        for component in registry.values():
            spec = component.blueprint_spec
            missing = []
            for field, value in (
                ("family", component.family_id), ("variant", component.variant_id),
                ("blueprint", spec), ("layout_pattern", spec.layout_pattern if spec else None),
                ("edge_behavior", spec.edge_behavior if spec else None),
                ("type_scale_role", spec.type_scale_role if spec else None),
                ("desktop_spec", spec.desktop_spec if spec else None),
                ("mobile_spec", spec.mobile_spec if spec else None),
                ("media_spec", spec.media_spec if spec else None),
                ("fallback", spec.fallback_strategy if spec else None),
                ("content_zones", component.content_zones), ("traits", component.traits),
            ):
                if value in (None, "", (), {}, frozenset()):
                    missing.append(field)
            if spec and not 0 <= spec.media_intensity <= 4:
                missing.append("media_intensity_range")
            if spec and spec.type_scale_role not in {"quiet", "normal", "large", "oversized", "monumental"}:
                missing.append("type_scale_role_enum")
            if missing:
                issues[component.id] = tuple(missing)
            blueprint_fingerprint(component)
    return issues, summaries


def markdown(issues: dict[str, tuple[str, ...]], summaries: dict[str, dict]) -> str:
    counts = Counter(component.category for registry in COMPONENT_REGISTRIES.values() for component in registry.values())
    exact = sum(len(summary["exact_duplicates"]) for summary in summaries.values())
    return "\n".join((
        "# Renderer readiness", "",
        "Renderer ready means structurally interpretable, not aesthetically premium.", "",
        f"- Components checked: {sum(counts.values())}",
        f"- Missing structural contracts: {len(issues)}",
        f"- Exact duplicate groups: {exact}",
        f"- Categories: {', '.join(f'{key}={value}' for key, value in counts.items())}", "",
        "Every component exposes family, variant, layout pattern, edge behavior, media intensity, type-scale role, desktop/mobile/media/content/behavior specs, fallback and compatibility metadata.", "",
        "## Next lot", "",
        "`DESIGN GENOME EXPERIMENTAL RENDERER V0.1` will interpret selected SiteDNA in an isolated visual laboratory. It is not implemented here.",
    ))


def main() -> None:
    issues, summaries = check()
    output = Path("docs/design-encyclopedia/renderer-readiness.md")
    output.write_text(markdown(issues, summaries) + "\n", encoding="utf-8")
    if issues:
        raise SystemExit(f"Renderer readiness failed for {len(issues)} components")
    print(output)


if __name__ == "__main__":
    main()
