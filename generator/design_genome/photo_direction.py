"""Deterministic Photo Director that never labels stock imagery as artisan work."""

from __future__ import annotations

from .models import PhotoDirection


TRADE_SUBJECTS = {
    "plombier": ("contemporary bathroom", "plumbing installation detail", "fixture material detail"),
    "peintre": ("painted interior architecture", "pigment material texture", "wall finish detail"),
    "macon": ("masonry construction detail", "stone and concrete architecture", "structural material"),
    "electricien": ("architectural lighting", "electrical installation detail", "smart home controls"),
    "menuisier": ("custom joinery interior", "wood material detail", "workshop craftsmanship"),
    "renovateur": ("residential renovation interior", "architectural transformation", "material palette interior"),
}

DIRECTION_MODIFIERS = {
    "editorial_luxury": ("editorial natural light", "warm", "bright", "muted", "clean"),
    "conversion_premium": ("professional residential", "neutral", "balanced", "natural", "clean"),
    "technical_spatial": ("technical architectural detail", "cold", "balanced", "muted", "clean"),
    "architectural_brutalist": ("raw monumental architecture", "neutral", "dark", "muted", "raw"),
    "warm_craft": ("warm workshop craft", "warm", "balanced", "natural", "tactile"),
    "cinematic_luxury": ("cinematic luxury interior", "warm", "dark", "muted", "clean"),
    "minimal_architecture": ("minimal contemporary architecture", "neutral", "bright", "muted", "clean"),
    "material_editorial": ("material texture editorial", "warm", "balanced", "natural", "tactile"),
}

SECTION_RULES = {
    "hero": ("wide establishing image", "landscape", frozenset({"ambient", "illustration"})),
    "gallery": ("visual sequence", "mixed", frozenset({"ambient", "illustration"})),
    "about": ("workshop or process context", "portrait", frozenset({"ambient", "illustration"})),
    "ambient": ("material atmosphere", "mixed", frozenset({"ambient", "illustration"})),
}

UNIVERSAL_AVOID = (
    "staged worker smiling at camera", "isolated tools on white", "clipart", "text embedded in image",
    "visible third-party logo", "stock image presented as our project", "stock before-and-after",
)


def get_photo_direction(trade: str, art_direction: str, section: str) -> PhotoDirection:
    if trade not in TRADE_SUBJECTS:
        raise ValueError(f"Unsupported trade: {trade}")
    if art_direction not in DIRECTION_MODIFIERS:
        raise ValueError(f"Unsupported art direction: {art_direction}")
    if section not in SECTION_RULES:
        raise ValueError(f"Unsupported photo section: {section}")
    modifier, temperature, brightness, saturation, texture = DIRECTION_MODIFIERS[art_direction]
    role, orientation, allowed_roles = SECTION_RULES[section]
    queries = tuple(f"{subject} {modifier} {role}" for subject in TRADE_SUBJECTS[trade])
    return PhotoDirection(
        id=f"{trade}:{art_direction}:{section}",
        trade=trade,
        art_direction=art_direction,
        section=section,
        queries=queries,
        avoid=UNIVERSAL_AVOID,
        orientation=orientation,
        temperature=temperature,
        brightness=brightness,
        saturation=saturation,
        texture=texture,
        allowed_roles=allowed_roles,
    )


PHOTO_DIRECTIONS = {
    f"{trade}:{direction}:{section}": get_photo_direction(trade, direction, section)
    for trade in TRADE_SUBJECTS
    for direction in DIRECTION_MODIFIERS
    for section in SECTION_RULES
}

assert len(PHOTO_DIRECTIONS) == 192
