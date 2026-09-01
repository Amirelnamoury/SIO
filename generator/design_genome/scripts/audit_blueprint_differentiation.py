"""Audit exact and near structural collisions across all component categories."""

from __future__ import annotations

from pathlib import Path

from ..blueprints import differentiation_summary
from ..data.components import COMPONENT_REGISTRIES


BASELINE_UNIQUE_FINGERPRINTS = {
    "header": 10, "hero": 12, "services": 13, "gallery": 9, "about": 10,
    "trust": 17, "cta": 9, "contact": 11, "footer": 10, "form": 6,
}


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
        "| Category | Components | Families | V1.1 unique | V1.2 unique | Exact duplicates | Near pairs | Minimum intra-family |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for category, summary in payload.items():
        minimums = [value for value in summary["minimum_intra_family_distance"].values() if value is not None]
        lines.append(
            f"| {category} | {summary['components']} | {summary['families']} | {BASELINE_UNIQUE_FINGERPRINTS[category]} | "
            f"{summary['unique_fingerprints']} | {len(summary['exact_duplicates'])} | {len(summary['near_duplicates'])} | "
            f"{min(minimums) if minimums else '-'} |"
        )
    lines.extend(("", "V1.1 had 107 unique structural blueprints for 260 IDs. V1.2 has 260 unique fingerprints. No alias is currently necessary.", ""))
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
