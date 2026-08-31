"""Deterministic, anti-clone selection for V3 design grammars."""

from __future__ import annotations

import hashlib
import json
import random

from .grammar import (
    AMBIENCES, CONTENT_DENSITIES, CTA_SYSTEMS, DECORATION_SYSTEMS, DESIGN_ENGINE_VERSION,
    DIRECTION_RULES, FOOTER_SYSTEMS, IMAGE_TREATMENTS, LAYOUT_GRIDS, MOTION_LEVELS,
    PHOTO_STRATEGIES, PROJECT_SHOWCASES, SECTION_TRANSITIONS, SPACING_RHYTHMS,
    SPATIAL_LEVELS, TRADE_DIRECTIONS,
)

PROFILE_AXES = (
    "art_direction", "page_silhouette", "header_system", "hero_system", "typography_system",
    "layout_grid", "spacing_rhythm", "surface_system", "photo_strategy", "image_treatment",
    "project_showcase", "services_composition", "content_density", "section_transitions",
    "cta_system", "motion_level", "spatial_level", "decoration_system", "footer_system",
    "mobile_personality", "ambience",
)


def build_design_signature(profile: dict) -> str:
    payload = "|".join(str(profile.get(axis) or "") for axis in PROFILE_AXES)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def similarity_score(left: dict, right: dict) -> float:
    weights = {
        "page_silhouette": 4, "hero_system": 4, "art_direction": 3,
        "typography_system": 2, "services_composition": 2, "project_showcase": 2,
        "header_system": 1.5, "photo_strategy": 1.5, "mobile_personality": 1.5,
    }
    total = sum(weights.get(axis, 1) for axis in PROFILE_AXES)
    same = sum(weights.get(axis, 1) for axis in PROFILE_AXES if left.get(axis) == right.get(axis))
    return same / total


def _pick(rng: random.Random, values):
    return values[rng.randrange(len(values))]


def _profile(seed: str, trade: str, direction: str, ambience: str | None, density: str | None, attempt: int) -> dict:
    digest = hashlib.sha256(f"{seed}|{direction}|{attempt}".encode("utf-8")).hexdigest()
    rng = random.Random(int(digest[:16], 16))
    rules = DIRECTION_RULES[direction]
    technical = direction == "technical_spatial"
    cinematic = direction == "cinematic_luxury"
    result = {
        "art_direction": direction,
        "page_silhouette": _pick(rng, rules["silhouettes"]),
        "header_system": _pick(rng, rules["headers"]),
        "hero_system": _pick(rng, rules["heroes"]),
        "typography_system": _pick(rng, rules["type"]),
        "layout_grid": _pick(rng, LAYOUT_GRIDS),
        "spacing_rhythm": {"compact": "compact", "balanced": "measured", "airy": "spacious"}.get(density or "", _pick(rng, SPACING_RHYTHMS)),
        "surface_system": _pick(rng, rules["surface"]),
        "photo_strategy": _pick(rng, PHOTO_STRATEGIES),
        "image_treatment": _pick(rng, IMAGE_TREATMENTS),
        "project_showcase": _pick(rng, PROJECT_SHOWCASES),
        "services_composition": _pick(rng, rules["services"]),
        "content_density": density or _pick(rng, CONTENT_DENSITIES),
        "section_transitions": _pick(rng, SECTION_TRANSITIONS),
        "cta_system": "sticky_conversion" if direction == "bold_conversion" else _pick(rng, CTA_SYSTEMS),
        "motion_level": "spatial" if technical and rng.random() > .4 else ("cinematic" if cinematic else _pick(rng, MOTION_LEVELS[:-1])),
        "spatial_level": _pick(rng, SPATIAL_LEVELS[1:]) if technical else _pick(rng, SPATIAL_LEVELS[:2]),
        "decoration_system": {"technical_spatial": "technical_grid", "architectural_brutalist": "brutalist_geometry", "warm_craft": "material_blocks", "cinematic_luxury": "cinematic_mask"}.get(direction, _pick(rng, DECORATION_SYSTEMS)),
        "footer_system": _pick(rng, FOOTER_SYSTEMS),
        "mobile_personality": _pick(rng, rules["mobile"]),
        "ambience": ambience or _pick(rng, AMBIENCES),
        "design_engine_version": DESIGN_ENGINE_VERSION,
    }
    result["design_signature"] = build_design_signature(result)
    return result


def select_design_grammar(artisan: dict, existing: list[dict] | None = None, *, direction: str | None = None, ambience: str | None = None, density: str | None = None, exclude_signatures: set[str] | None = None) -> tuple[dict, bool]:
    trade = str(artisan.get("metier") or "").lower()
    directions = TRADE_DIRECTIONS.get(trade, tuple(DIRECTION_RULES))
    if direction:
        if direction not in DIRECTION_RULES:
            raise ValueError("Direction artistique V3 inconnue")
        directions = (direction,)
    seed = str(artisan.get("slug") or artisan.get("siret") or artisan.get("nom_entreprise") or trade or "site")
    history = [item for item in (existing or []) if str(item.get("design_engine_version", "")).startswith("v3")]
    excluded = exclude_signatures or set()
    candidates = []
    for attempt in range(18):
        chosen_direction = directions[int(hashlib.sha256(f"{seed}|direction|{attempt}".encode()).hexdigest()[:8], 16) % len(directions)]
        candidate = _profile(seed, trade, chosen_direction, ambience, density, attempt)
        if candidate["design_signature"] in excluded:
            continue
        peak = max((similarity_score(candidate, item) for item in history), default=0.0)
        structural_repeats = sum(
            any(candidate[axis] == item.get(axis) for item in history)
            for axis in ("page_silhouette", "hero_system", "image_treatment", "typography_system")
        )
        candidates.append((structural_repeats, peak, candidate))
    if not candidates:
        candidate = _profile(seed, trade, directions[0], ambience, density, 99)
        return candidate, False
    _repeats, peak, best = min(candidates, key=lambda item: (item[0], item[1], item[2]["design_signature"]))
    return best, peak < .58


def profile_json(profile: dict) -> str:
    return json.dumps({axis: profile.get(axis) for axis in PROFILE_AXES}, sort_keys=True, ensure_ascii=True)
