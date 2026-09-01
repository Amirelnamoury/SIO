"""Metadata inference for concise, semantic component blueprint declarations."""

from ...models import ComponentDefinition


TRAIT_WORDS = {
    "editorial": "editorial", "magazine": "editorial", "index": "editorial",
    "cinematic": "cinematic", "overlay": "cinematic", "panorama": "cinematic",
    "technical": "technical", "blueprint": "technical", "specification": "technical",
    "warm": "warm", "workshop": "warm", "craft": "tactile", "material": "material",
    "minimal": "minimal", "quiet": "quiet", "statement": "quiet",
    "local": "local", "phone": "phone_first", "quote": "quote_first",
    "conversion": "conversion_led", "action": "conversion_led", "emergency": "conversion_led",
    "project": "project_led", "casebook": "project_led", "portfolio": "portfolio",
    "gallery": "visual_led", "photo": "visual_led", "image": "visual_led", "visual": "visual_led",
    "documentary": "documentary", "industrial": "industrial", "brutalist": "brutal",
    "spatial": "spatial", "isometric": "spatial", "layered": "layered",
    "split": "split", "offset": "offset", "masonry": "masonry", "rail": "rail",
    "full_bleed": "full_bleed", "framed": "framed", "centered": "centered",
    "luxury": "luxurious", "residential": "residential", "service": "service_led",
    "trust": "trust_led", "proof": "trust_led", "story": "story_led",
}

ARCHETYPES_BY_TRAIT = {
    "technical": {"technical_expert", "industrial_specialist", "spatial_technical"},
    "conversion_led": {"conversion_first_local", "local_emergency_service", "bold_local"},
    "project_led": {"project_portfolio", "architectural_contracting", "design_build"},
    "luxurious": {"premium_residential", "luxury_renovation", "quiet_luxury"},
    "warm": {"warm_artisan", "family_business", "high_end_craft"},
    "material": {"material_led", "high_end_craft", "heritage_craft"},
    "editorial": {"editorial_studio", "quiet_luxury", "material_led"},
    "local": {"conversion_first_local", "family_business", "bold_local"},
    "documentary": {"documentary_craft", "heritage_craft", "design_build"},
    "spatial": {"spatial_technical", "technical_expert"},
    "minimal": {"minimal_architecture", "quiet_luxury"},
}

DIRECTIONS_BY_TRAIT = {
    "technical": {"technical_spatial", "minimal_architecture"},
    "conversion_led": {"conversion_premium", "architectural_brutalist"},
    "project_led": {"minimal_architecture", "editorial_luxury"},
    "luxurious": {"editorial_luxury", "cinematic_luxury"},
    "warm": {"warm_craft", "material_editorial"},
    "material": {"material_editorial", "warm_craft"},
    "editorial": {"editorial_luxury", "material_editorial"},
    "documentary": {"warm_craft", "material_editorial"},
    "spatial": {"technical_spatial"},
    "minimal": {"minimal_architecture", "editorial_luxury"},
}

TRADE_AFFINITY = {
    "technical": {"electricien": .95, "plombier": .75, "macon": .72},
    "material": {"menuisier": .96, "peintre": .88, "macon": .80, "renovateur": .72},
    "warm": {"menuisier": .92, "peintre": .74, "renovateur": .66},
    "conversion_led": {"plombier": .95, "electricien": .92, "renovateur": .64},
    "project_led": {"renovateur": .94, "macon": .86, "menuisier": .78, "peintre": .68},
}


def make_component(category: str, component_id: str, extra_traits: tuple[str, ...] = ()) -> ComponentDefinition:
    traits = set(extra_traits)
    for word, trait in TRAIT_WORDS.items():
        if word in component_id:
            traits.add(trait)
    if not traits:
        traits.add("balanced")

    archetypes = set()
    directions = set()
    trade_affinity = {}
    for trait in traits:
        archetypes.update(ARCHETYPES_BY_TRAIT.get(trait, ()))
        directions.update(DIRECTIONS_BY_TRAIT.get(trait, ()))
        for trade, score in TRADE_AFFINITY.get(trait, {}).items():
            trade_affinity[trade] = max(score, trade_affinity.get(trade, 0.0))

    required_data = set()
    required_media = set()
    allowed_sources = {"artisan", "stock", "none"}
    if category == "services":
        required_data.add("services")
    if "phone" in component_id:
        required_data.add("phone")
    if "review" in component_id or "testimonial" in component_id:
        required_data.add("reviews")
    if "insurance" in component_id:
        required_data.add("insurance")
    if "certification" in component_id or "badge" in component_id:
        required_data.add("certifications")
    if "stat" in component_id or "number" in component_id:
        required_data.add("statistics")
    if "team" in component_id or "people" in component_id:
        required_data.add("team")
    if "area" in component_id or "map" in component_id:
        required_data.add("service_areas")
    if "process" in component_id:
        required_data.add("process")
    if "partner" in component_id:
        required_data.add("partners")
    if "brand_authorization" in component_id:
        required_data.add("brands")
    if "award" in component_id:
        required_data.add("awards")
    if "guarantee" in component_id:
        required_data.add("guarantee")
    if "opening_hours" in component_id:
        required_data.add("opening_hours")
    if "emergency_availability" in component_id:
        required_data.add("emergency_service")
    if "response_delay" in component_id:
        required_data.add("response_delay")
    if "combined_verified_fact" in component_id or "minimal_verified_fact" in component_id:
        required_data.add("verified_facts")
    if "before_after" in component_id or "transformation_pair" in component_id:
        required_media.add("before_after")
        allowed_sources = {"artisan"}
    if any(word in component_id for word in ("project", "casebook", "realisation", "work_log")) and category == "gallery":
        required_media.add("artisan_project")
        allowed_sources = {"artisan"}
    if "artisan_project_evidence" in component_id:
        required_media.add("artisan_project")
        allowed_sources = {"artisan"}
    if "portrait" in component_id:
        required_media.add("portrait")
    if "panorama" in component_id:
        required_media.add("landscape")

    visual = 4 if any(word in component_id for word in ("oversized", "full_bleed", "cinematic", "monumental", "spatial")) else 2 if any(word in component_id for word in ("quiet", "minimal", "compact")) else 3
    density = 4 if any(word in component_id for word in ("matrix", "table", "directory", "mega", "technical")) else 2 if any(word in component_id for word in ("quiet", "minimal", "statement")) else 3
    energy = "heroic" if visual == 5 else "strong" if visual >= 4 else "quiet" if visual <= 2 else "medium"
    image_dependency = .9 if required_media or any(word in component_id for word in ("photo", "gallery", "image", "cinematic", "project")) else .2
    conversion = .9 if "conversion_led" in traits or category in {"cta", "contact", "form"} else .45
    editorial = .88 if "editorial" in traits or "story_led" in traits else .42
    zones = {
        "header": ("brand", "navigation", "primary_action"),
        "hero": ("eyebrow", "title", "supporting_copy", "actions", "media"),
        "services": ("section_title", "service_items", "service_detail"),
        "gallery": ("section_title", "media_items", "captions"),
        "about": ("section_title", "narrative", "supporting_media"),
        "trust": ("verified_facts", "fact_labels"),
        "cta": ("prompt", "primary_action", "secondary_action"),
        "contact": ("contact_details", "form", "context"),
        "footer": ("brand", "navigation", "legal", "contact"),
        "form": ("fields", "consent", "submit", "status"),
    }[category]
    mobile = "bottom_action" if "phone" in component_id else "horizontal_scroll" if "rail" in component_id else "stack_priority_order"
    return ComponentDefinition(
        id=component_id,
        category=category,
        traits=frozenset(traits),
        compatible_archetypes=frozenset(archetypes),
        compatible_directions=frozenset(directions),
        required_data=frozenset(required_data),
        required_media=frozenset(required_media),
        allowed_media_sources=frozenset(allowed_sources),
        density=density,
        visual_weight=visual,
        section_energy=energy,
        mobile_variant=mobile,
        trade_affinity=trade_affinity,
        conversion_score=conversion,
        editorial_score=editorial,
        image_dependency=image_dependency,
        content_zones=zones,
        notes=f"Blueprint {component_id.replace('_', ' ')}; structure only, no production markup.",
    )


def registry(category: str, ids: tuple[str, ...]) -> dict[str, ComponentDefinition]:
    return {component_id: make_component(category, component_id) for component_id in ids}
