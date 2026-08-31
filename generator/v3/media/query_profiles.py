"""Contextual provider queries derived from trade, grammar and usage."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MediaQueryProfile:
    trade: str
    art_direction: str
    usage: str
    queries: tuple[str, ...]
    orientation: str = "landscape"


TRADE_QUERIES = {
    "peintre": ("haussmann interior textured wall", "limewash plaster finish", "warm residential interior", "interior wall pigment detail"),
    "peinture": ("haussmann interior textured wall", "limewash plaster finish", "warm residential interior", "interior wall pigment detail"),
    "plombier": ("contemporary bathroom architecture", "premium faucet detail", "bathroom renovation interior", "plumber installation detail"),
    "plomberie": ("contemporary bathroom architecture", "premium faucet detail", "bathroom renovation interior", "plumber installation detail"),
    "electricien": ("architectural lighting interior", "smart home interior", "electrical panel detail", "lighting design modern house"),
    "electricite": ("architectural lighting interior", "smart home interior", "electrical panel detail", "lighting design modern house"),
    "macon": ("concrete architecture house", "brutalist house exterior", "masonry stone detail", "contemporary construction detail"),
    "maconnerie": ("concrete architecture house", "brutalist house exterior", "masonry stone detail", "contemporary construction detail"),
    "menuisier": ("custom wood interior", "joinery detail", "carpenter workshop", "bespoke cabinetry detail"),
    "menuiserie": ("custom wood interior", "joinery detail", "carpenter workshop", "bespoke cabinetry detail"),
    "renovateur": ("luxury residential renovation", "haussmann apartment interior", "architectural renovation house", "modern residential transformation"),
    "renovation": ("luxury residential renovation", "haussmann apartment interior", "architectural renovation house", "modern residential transformation"),
}

DIRECTION_TERMS = {
    "editorial_luxury": "editorial natural light",
    "bold_conversion": "professional dramatic",
    "technical_spatial": "technical architectural detail",
    "architectural_brutalist": "monumental raw material",
    "warm_craft": "warm workshop craft detail",
    "cinematic_luxury": "cinematic luxury architecture",
    "minimal_architecture": "minimal contemporary architecture",
    "material_editorial": "material texture editorial",
}


def build_query_profile(trade: str, profile: dict, usage: str) -> MediaQueryProfile:
    normalized_trade = str(trade or "").lower()
    base = TRADE_QUERIES.get(normalized_trade, ("French artisan workshop", "residential renovation detail"))
    direction = str(profile.get("art_direction") or "minimal_architecture")
    usage_term = {"hero": "wide", "gallery": "project", "about": "workshop", "before_after": "renovation"}.get(usage, usage)
    modifier = DIRECTION_TERMS.get(direction, "architectural")
    queries = tuple(f"{query} {modifier} {usage_term}" for query in base)
    return MediaQueryProfile(normalized_trade, direction, usage, queries)
