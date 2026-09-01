"""Audit exact and near structural collisions across all component categories."""

from __future__ import annotations

from pathlib import Path

from ..blueprints import blueprint_structural_distance, differentiation_summary
from ..data.components import ALL_COMPONENTS, COMPONENT_REGISTRIES


BASELINE_UNIQUE_FINGERPRINTS = {
    "header": 10, "hero": 12, "services": 13, "gallery": 9, "about": 10,
    "trust": 17, "cta": 9, "contact": 11, "footer": 10, "form": 6,
}

REVIEWED_NEAR_PAIRS = (
    ("local_info_strip", "phone_first_compact", "retained: horizontal local facts versus phone-priority action"),
    ("mega_contact_header", "residential_project_header", "retained: contact matrix versus calm project navigation"),
    ("two_row_local", "utility_contact_bar", "retained: locality-led hierarchy versus generic verified utility"),
    ("centered_image_frame", "framed_luxury_scene", "retained: artwork-like centered canvas versus luxury scene and external copy"),
    ("cinematic_overlay_story", "full_bleed_photo_cover", "retained: chapter-led cinematic narrative versus environmental cover"),
    ("layered_material_scene", "photo_right_residential_intro", "retained: overlapping material depth versus conventional residential split"),
    ("material_macro_title", "photo_left_service_intro", "retained: texture-scale study versus service-led split"),
    ("panorama_architectural", "quiet_luxury_window", "retained: horizon band versus small image window and intentional void"),
)


def audit() -> dict[str, dict]:
    return {
        category: differentiation_summary(registry.values())
        for category, registry in COMPONENT_REGISTRIES.items()
    }


def markdown(payload: dict[str, dict]) -> str:
    lines = [
        "# Blueprint differentiation audit", "",
        "Distances are pure renderer-structure comparisons: `0.00` is exact, `<0.15` is near-duplicate, `0.15-0.40` is a related family variant, and `>0.40` is meaningfully different.", "",
        "## Before and after", "",
        "| Category | Components | Families | V1.1 unique | V1.2.1 explicit unique | Exact duplicates | Near pairs | Minimum intra-family |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for category, summary in payload.items():
        minimums = [value for value in summary["minimum_intra_family_distance"].values() if value is not None]
        lines.append(
            f"| {category} | {summary['components']} | {summary['families']} | {BASELINE_UNIQUE_FINGERPRINTS[category]} | "
            f"{summary['unique_fingerprints']} | {len(summary['exact_duplicates'])} | {len(summary['near_duplicates'])} | "
            f"{min(minimums) if minimums else '-'} |"
        )
    lines.extend((
        "", "## V1.2 POSITIONAL SYSTEM REMOVED", "",
        "Before: V1.2 selected one of ten structural variants from each component's tuple position by `enumerate()` and modulo.", "",
        "After: V1.2.1 resolves every component through an explicit `StructuralVariantSpec` keyed by component ID. Reordering a family or registry leaves variant IDs, structural specs and fingerprints unchanged.", "",
        "`design_intent` and identity labels remain outside the fingerprint. Only merged renderer instructions create structural novelty.", "",
        "V1.1 had 107 unique structural blueprints for 260 IDs. V1.2.1 reports the honest explicit count below; no alias is currently necessary.", "",
        "## Reviewed V1.2 near pairs", "",
        "| Left | Right | V1.2.1 distance | Decision |", "|---|---|---:|---|",
    ))
    for left_id, right_id, decision in REVIEWED_NEAR_PAIRS:
        distance = blueprint_structural_distance(ALL_COMPONENTS[left_id], ALL_COMPONENTS[right_id]).distance
        lines.append(f"| `{left_id}` | `{right_id}` | {distance:.4f} | {decision} |")
    lines.extend(("", "No reviewed pair is an alias or merge: each now carries a useful renderer-visible difference and an explicit design intent.", ""))
    for category, summary in payload.items():
        lines.extend((f"## {category.title()}", "", "### Closest structural pairs", "", "| Component | Closest | Distance |", "|---|---|---:|"))
        seen = set()
        for component_id, (closest_id, distance) in sorted(summary["closest"].items(), key=lambda item: (item[1][1], item[0])):
            pair = tuple(sorted((component_id, closest_id)))
            if pair in seen:
                continue
            seen.add(pair)
            lines.append(f"| `{component_id}` | `{closest_id}` | {distance:.4f} |")
        if summary["near_duplicates"]:
            lines.extend(("", "Near pairs remain explicitly visible for renderer review; they are not hidden by identity labels."))
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    output = Path("docs/design-encyclopedia/blueprint-differentiation-audit.md")
    output.write_text(markdown(audit()) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
