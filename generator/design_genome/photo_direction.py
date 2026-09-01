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

TRADE_POLICIES = {
    "plombier": {
        "subjects": ("installed bathroom or heating context", "fixture connection detail", "clean documented intervention"),
        "composition": ("context before tools", "show scale and finish", "avoid staged emergency"),
        "people": "artisan only when actually supplied; stock people remain ambient and never become the business team",
        "tools": "installed systems and tool-in-use only; no isolated wrench symbolism",
        "environment": "credible residential or technical context without damage sensationalism",
        "materials": ("metal fittings", "ceramic", "water-safe surfaces"),
        "risk": "high: staged smiling worker, blue-water cliché, false emergency scene",
    },
    "peintre": {
        "subjects": ("finished interior surface", "pigment and texture detail", "protected working context"),
        "composition": ("surface plane as subject", "color relationship in room", "real transformation only from artisan"),
        "people": "hands or artisan process only when credible; no stock team identity",
        "tools": "brush or roller only in process context; never logo-like isolated prop",
        "environment": "daylit interior, facade or material sample with believable color",
        "materials": ("pigment", "plaster", "painted wood", "mineral finish"),
        "risk": "high: rainbow splash, fake before-after, oversaturated stock room",
    },
    "macon": {
        "subjects": ("masonry detail", "structural sequence", "finished architectural context"),
        "composition": ("show material scale", "document safe work context", "alternate detail and whole"),
        "people": "only safe contextual work; no hard-hat handshake cliché",
        "tools": "equipment may explain process but never dominate identity",
        "environment": "credible construction stage or completed masonry without unrelated megaproject",
        "materials": ("stone", "brick", "concrete", "mortar"),
        "risk": "high: unsafe site, unrelated skyline, invented project scale",
    },
    "electricien": {
        "subjects": ("architectural lighting", "installation detail", "controls or panel context"),
        "composition": ("light as spatial evidence", "clean routing detail", "diagram only for explanation"),
        "people": "stock people never imply certification or team membership",
        "tools": "measurement tool only in credible diagnostic context",
        "environment": "safe, orderly interior or technical installation",
        "materials": ("light", "metal", "cable routing", "control surfaces"),
        "risk": "high: lightning iconography, danger spectacle, unverified compliance badge",
    },
    "menuisier": {
        "subjects": ("joinery detail", "completed fitted interior", "workshop gesture"),
        "composition": ("grain and fit at useful scale", "detail paired with whole", "calm material light"),
        "people": "artisan hands or portrait only from supplied media; no anonymous stock craftsperson as team",
        "tools": "tool-in-use supports process; sawblade and isolated tools are clichés",
        "environment": "real workshop or interior, never generic forest as project evidence",
        "materials": ("wood grain", "joinery", "hardware", "finish"),
        "risk": "medium-high: generic forest, mass-market furniture, false bespoke claim",
    },
    "renovateur": {
        "subjects": ("residential spatial sequence", "material palette", "documented transformation"),
        "composition": ("room-to-room continuity", "before-after only matched artisan media", "balance detail and whole"),
        "people": "real occupants only with supplied rights; stock remains ambient",
        "tools": "process context only, never a generic renovation symbol",
        "environment": "believable residence or work stage, no impossible render presented as delivery",
        "materials": ("interior surfaces", "joinery", "stone", "lighting"),
        "risk": "high: luxury stock labelled project, fake transformation, invented partners",
    },
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

DIRECTION_COMPOSITION = {
    "editorial_luxury": (("measured negative space", "asymmetric editorial crop"), "medium-format editorial camera", "soft controlled daylight"),
    "conversion_premium": (("clear subject", "service context immediately legible"), "straightforward professional camera", "balanced natural light"),
    "technical_spatial": (("orthographic detail", "system relationship"), "precise technical camera", "cool even light"),
    "architectural_brutalist": (("monumental crop", "raw material edge"), "wide architectural camera", "hard directional or overcast light"),
    "warm_craft": (("gesture and material", "intimate context"), "close documentary camera", "warm workshop daylight"),
    "cinematic_luxury": (("wide establishing scene", "controlled shadow"), "slow cinematic camera", "low-key warm light"),
    "minimal_architecture": (("single clear plane", "precise negative space"), "restrained architectural camera", "bright diffuse light"),
    "material_editorial": (("macro-to-context pair", "tactile crop"), "editorial detail camera", "raking material light"),
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
    trade_policy = TRADE_POLICIES[trade]
    composition, camera, lighting = DIRECTION_COMPOSITION[art_direction]
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
        positive_queries=queries,
        negative_queries=UNIVERSAL_AVOID,
        subject_priority=trade_policy["subjects"],
        composition_priority=trade_policy["composition"] + composition,
        people_policy=trade_policy["people"],
        tool_policy=trade_policy["tools"],
        environment_policy=trade_policy["environment"],
        camera_feel=f"{camera}; {lighting}",
        material_focus=trade_policy["materials"],
        crop=f"{orientation}; preserve context; {composition[0]}",
        stock_cliche_risk=trade_policy["risk"],
    )


PHOTO_DIRECTIONS = {
    f"{trade}:{direction}:{section}": get_photo_direction(trade, direction, section)
    for trade in TRADE_SUBJECTS
    for direction in DIRECTION_MODIFIERS
    for section in SECTION_RULES
}

assert len(PHOTO_DIRECTIONS) == 192
