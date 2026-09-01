"""Pure structural analysis for renderer-oriented component blueprints."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from typing import Any, Iterable, Mapping

from .models import ComponentDefinition, StructuralDistanceReport


EXACT_DUPLICATE_THRESHOLD = 0.0
NEAR_DUPLICATE_THRESHOLD = 0.15
SAME_FAMILY_VARIANT_MAX = 0.40


def _canonical(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted(_canonical(item) for item in value)
    return value


def blueprint_structural_payload(component: ComponentDefinition) -> dict[str, Any]:
    """Return renderer-visible structure, deliberately excluding all identity labels."""
    if component.blueprint_spec is None:
        raise ValueError(f"Component {component.id} has no blueprint spec")
    spec = component.blueprint_spec
    return _canonical({
        "category": component.category,
        "layout_model": spec.layout_model,
        "layout_pattern": spec.layout_pattern,
        "edge_behavior": spec.edge_behavior,
        "media_intensity": spec.media_intensity,
        "type_scale_role": spec.type_scale_role,
        "content_alignment": spec.content_alignment,
        "desktop_spec": spec.desktop_spec,
        "mobile_spec": spec.mobile_spec,
        "media_spec": spec.media_spec,
        "content_spec": spec.content_spec,
        "behavior_spec": spec.behavior_spec,
        "fallback_strategy": spec.fallback_strategy,
        "density": component.density,
        "visual_weight": component.visual_weight,
        "section_energy": component.section_energy,
        "mobile_variant": component.mobile_variant,
    })


def blueprint_fingerprint(component: ComponentDefinition) -> str:
    canonical = json.dumps(
        blueprint_structural_payload(component),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            result.update(_flatten(item, child))
        return result
    if isinstance(value, list):
        return {prefix: tuple(json.dumps(_canonical(item), sort_keys=True) for item in value)}
    return {prefix: value}


def _mapping_distance(left: Mapping[str, Any], right: Mapping[str, Any]) -> tuple[float, tuple[str, ...]]:
    left_flat = _flatten(_canonical(left))
    right_flat = _flatten(_canonical(right))
    keys = sorted(set(left_flat) | set(right_flat))
    changed = tuple(key for key in keys if left_flat.get(key) != right_flat.get(key))
    return (len(changed) / max(1, len(keys)), changed)


def blueprint_structural_distance(left: ComponentDefinition, right: ComponentDefinition) -> StructuralDistanceReport:
    """Return a weighted 0..1 distance and its renderer-visible causes."""
    left_payload = blueprint_structural_payload(left)
    right_payload = blueprint_structural_payload(right)
    layout_left = {key: left_payload[key] for key in ("category", "layout_model", "layout_pattern", "edge_behavior", "content_alignment", "desktop_spec")}
    layout_right = {key: right_payload[key] for key in layout_left}
    content_left = {key: left_payload[key] for key in ("content_spec", "type_scale_role", "density")}
    content_right = {key: right_payload[key] for key in content_left}
    media_left = {key: left_payload[key] for key in ("media_spec", "media_intensity")}
    media_right = {key: right_payload[key] for key in media_left}
    mobile_left = {"mobile_spec": left_payload["mobile_spec"], "mobile_variant": left_payload["mobile_variant"]}
    mobile_right = {key: right_payload[key] for key in mobile_left}
    behavior_left = {"behavior_spec": left_payload["behavior_spec"], "fallback_strategy": left_payload["fallback_strategy"]}
    behavior_right = {key: right_payload[key] for key in behavior_left}
    rhythm_left = {key: left_payload[key] for key in ("visual_weight", "section_energy", "density", "layout_pattern", "edge_behavior", "media_intensity", "type_scale_role")}
    rhythm_right = {key: right_payload[key] for key in rhythm_left}

    groups = (
        ("layout", *_mapping_distance(layout_left, layout_right), .30),
        ("content", *_mapping_distance(content_left, content_right), .15),
        ("media", *_mapping_distance(media_left, media_right), .18),
        ("mobile", *_mapping_distance(mobile_left, mobile_right), .16),
        ("behavior", *_mapping_distance(behavior_left, behavior_right), .09),
        ("rhythm", *_mapping_distance(rhythm_left, rhythm_right), .12),
    )
    variant_keys = (
        ("desktop_spec", "flow_direction"), ("desktop_spec", "alignment_anchor"),
        ("desktop_spec", "frame_behavior"), ("mobile_spec", "collapse_strategy"),
        ("mobile_spec", "priority_anchor"), ("behavior_spec", "focus_progression"),
    )
    variant_changes = sum(
        left_payload[section].get(key) != right_payload[section].get(key)
        for section, key in variant_keys
    ) / len(variant_keys)
    distance = sum(value * weight for _, value, _, weight in groups) * .78 + variant_changes * .22
    reasons = tuple(f"{name}:{key}" for name, _, changed, _ in groups for key in changed)
    values = {name: value for name, value, _, _ in groups}
    return StructuralDistanceReport(
        distance=round(distance, 4),
        layout_distance=round(values["layout"], 4),
        content_distance=round(values["content"], 4),
        media_distance=round(values["media"], 4),
        mobile_distance=round(values["mobile"], 4),
        behavior_distance=round(values["behavior"], 4),
        rhythm_distance=round(values["rhythm"], 4),
        reasons=reasons,
    )


def differentiation_summary(components: Iterable[ComponentDefinition]) -> dict[str, Any]:
    items = tuple(components)
    by_fingerprint: dict[str, list[str]] = defaultdict(list)
    by_family: dict[str, list[ComponentDefinition]] = defaultdict(list)
    for component in items:
        by_fingerprint[blueprint_fingerprint(component)].append(component.id)
        by_family[component.family_id].append(component)

    exact = tuple(tuple(ids) for ids in by_fingerprint.values() if len(ids) > 1)
    near: list[tuple[str, str, float]] = []
    closest: dict[str, tuple[str, float]] = {}
    for index, left in enumerate(items):
        candidates: list[tuple[float, str]] = []
        for right in items[index + 1:]:
            distance = blueprint_structural_distance(left, right).distance
            candidates.append((distance, right.id))
            previous = closest.get(right.id)
            if previous is None or distance < previous[1]:
                closest[right.id] = (left.id, distance)
            if 0.0 < distance < NEAR_DUPLICATE_THRESHOLD:
                near.append((left.id, right.id, distance))
        if candidates:
            distance, component_id = min(candidates)
            previous = closest.get(left.id)
            if previous is None or distance < previous[1]:
                closest[left.id] = (component_id, distance)

    family_minimums = {}
    for family, members in by_family.items():
        distances = [
            blueprint_structural_distance(left, right).distance
            for index, left in enumerate(members)
            for right in members[index + 1:]
        ]
        family_minimums[family] = min(distances) if distances else None
    return {
        "components": len(items),
        "families": len(by_family),
        "variants": len({(item.family_id, item.variant_id) for item in items}),
        "unique_fingerprints": len(by_fingerprint),
        "exact_duplicates": exact,
        "near_duplicates": tuple(sorted(near, key=lambda item: (item[2], item[0], item[1]))),
        "family_distribution": {key: len(value) for key, value in sorted(by_family.items())},
        "minimum_intra_family_distance": family_minimums,
        "closest": closest,
    }
