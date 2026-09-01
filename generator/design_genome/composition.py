"""Structural site signatures, readable composition reports and diversity metrics."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from functools import lru_cache
from typing import Any, Iterable, Mapping

from .blueprints import blueprint_fingerprint
from .component_relationships import component_pair_affinity
from .data.components import ALL_COMPONENTS
from .models import CompositionComponentEntry, SiteDNA, SiteDNACompositionReport


COMPONENT_FIELDS_BY_SECTION = {
    "header": "header_component", "hero": "hero_component", "services": "services_component",
    "gallery": "gallery_component", "about": "about_component", "trust": "trust_component",
    "cta": "cta_component", "contact": "contact_component", "footer": "footer_component",
}


@lru_cache(maxsize=None)
def _component_entry(section: str, component_id: str) -> CompositionComponentEntry:
    component = ALL_COMPONENTS[component_id]
    spec = component.blueprint_spec
    assert spec is not None
    return CompositionComponentEntry(
        section, component.id, component.family_id, component.variant_id,
        spec.layout_pattern, spec.edge_behavior, spec.media_intensity,
        spec.type_scale_role, blueprint_fingerprint(component),
    )


def component_entries_from_payload(payload: Mapping[str, Any]) -> tuple[CompositionComponentEntry, ...]:
    entries: list[CompositionComponentEntry] = []
    for section in payload["section_order"]:
        field = COMPONENT_FIELDS_BY_SECTION.get(section)
        component_id = payload.get(field) if field else None
        if component_id:
            entries.append(_component_entry(section, component_id))
        if section == "contact" and payload.get("form_component"):
            entries.append(_component_entry("form", payload["form_component"]))
    return tuple(entries)


def composition_signature_for(payload: Mapping[str, Any]) -> str:
    entries = component_entries_from_payload(payload)
    canonical = {
        "components": [
            {
                "section": item.section, "family": item.family_id, "variant": item.variant_id,
                "fingerprint": item.fingerprint, "pattern": item.layout_pattern,
                "edge": item.edge_behavior, "media": item.media_intensity, "type": item.type_scale_role,
            }
            for item in entries
        ],
        "section_order": list(payload["section_order"]),
        "grid": payload["grid_system"],
        "spacing": payload["spacing_system"],
        "geometry": payload["geometry_system"],
    }
    raw = json.dumps(canonical, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def composition_report(dna: SiteDNA) -> SiteDNACompositionReport:
    entries = component_entries_from_payload(dna.to_dict())
    transitions = tuple(
        {
            "from": left.section, "to": right.section,
            "score": component_pair_affinity(ALL_COMPONENTS[left.component_id], ALL_COMPONENTS[right.component_id]).score,
        }
        for left, right in zip(entries, entries[1:])
    )
    return SiteDNACompositionReport(
        composition_signature=dna.composition_signature,
        components=entries,
        transitions=transitions,
        layout_rhythm=tuple(item.layout_pattern for item in entries),
        edge_rhythm=tuple(item.edge_behavior for item in entries),
        media_rhythm=tuple(item.media_intensity for item in entries),
        type_rhythm=tuple(item.type_scale_role for item in entries),
    )


def composition_report_markdown(dna: SiteDNA) -> str:
    report = composition_report(dna)
    lines = [f"# SiteDNA composition `{report.composition_signature}`", ""]
    for item in report.components:
        lines.extend((
            f"## {item.section.upper()}", "",
            f"- id: `{item.component_id}`", f"- family: `{item.family_id}`",
            f"- variant: `{item.variant_id}`", f"- pattern: `{item.layout_pattern}`",
            f"- edge: `{item.edge_behavior}`", f"- media intensity: {item.media_intensity}",
            f"- type scale: `{item.type_scale_role}`", f"- fingerprint: `{item.fingerprint}`", "",
        ))
    lines.extend(("## Transitions", ""))
    lines.extend(f"- {item['from']} -> {item['to']}: {item['score']:.4f}" for item in report.transitions)
    lines.extend((
        "", "## Page rhythm", "",
        f"- patterns: {' -> '.join(report.layout_rhythm)}",
        f"- edges: {' -> '.join(report.edge_rhythm)}",
        f"- media: {' -> '.join(str(value) for value in report.media_rhythm)}",
        f"- type: {' -> '.join(report.type_rhythm)}",
    ))
    return "\n".join(lines) + "\n"


def visual_diversity_report(dnas: Iterable[SiteDNA]) -> dict[str, Any]:
    items = tuple(dnas)
    reports = tuple(composition_report(item) for item in items)
    entries = tuple(entry for report in reports for entry in report.components)
    by_section = Counter(entry.section for entry in entries)
    return {
        "requested": len(items),
        "unique_design_signatures": len({item.design_signature for item in items}),
        "unique_composition_signatures": len({item.composition_signature for item in items}),
        "unique_component_ids": len({entry.component_id for entry in entries}),
        "unique_families": len({entry.family_id for entry in entries}),
        "unique_variants": len({(entry.family_id, entry.variant_id) for entry in entries}),
        "unique_blueprint_fingerprints": len({entry.fingerprint for entry in entries}),
        "unique_layout_rhythms": len({report.layout_rhythm for report in reports}),
        "unique_edge_rhythms": len({report.edge_rhythm for report in reports}),
        "unique_media_rhythms": len({report.media_rhythm for report in reports}),
        "unique_type_rhythms": len({report.type_rhythm for report in reports}),
        "unique_section_orders": len({item.section_order for item in items}),
        "unique_grids": len({item.grid_system for item in items}),
        "unique_colors": len({item.color_system for item in items}),
        "unique_typography": len({item.typography_system for item in items}),
        "component_occurrences_by_section": dict(sorted(by_section.items())),
    }
