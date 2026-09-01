"""Extensible traits used by registries and compatibility scoring."""

LAYOUT_TRAITS = frozenset({
    "centered", "asymmetric", "editorial", "modular", "full_bleed", "broken_grid",
    "framed", "split", "stacked", "magazine", "portfolio", "cinematic", "rail",
    "layered", "offset", "masonry", "edge_to_edge",
})

VISUAL_TONES = frozenset({
    "minimal", "warm", "brutal", "elegant", "luxurious", "industrial", "technical",
    "playful", "institutional", "local", "tactile", "futuristic", "documentary",
    "quiet", "bold", "material", "architectural",
})

CONTENT_BEHAVIORS = frozenset({
    "information_dense", "visual_led", "conversion_led", "story_led", "project_led",
    "trust_led", "service_led", "material_led", "phone_first", "quote_first",
})

IMAGE_BEHAVIORS = frozenset({
    "full_bleed_image", "contained_image", "collage", "contact_sheet", "masonry_image",
    "cinematic_crop", "portrait_dominant", "landscape_dominant", "material_macro",
    "documentary_image", "monochrome_image", "duotone_image", "layered_image", "masked_image",
})

ENERGY_LEVELS = ("quiet", "medium", "strong", "heroic")
MEDIA_SOURCES = frozenset({"artisan", "stock", "none"})
TRADES = ("plombier", "peintre", "macon", "electricien", "menuisier", "renovateur")

ART_DIRECTIONS = (
    "editorial_luxury", "conversion_premium", "technical_spatial", "architectural_brutalist",
    "warm_craft", "cinematic_luxury", "minimal_architecture", "material_editorial",
)

BUSINESS_INTENTS = (
    "emergency", "local_quote", "premium_residential", "renovation_project",
    "technical_expertise", "portfolio", "craft", "commercial_b2b",
    "trust_first", "balanced",
)

BUSINESS_INTENT_ALIASES = {
    "quote": "local_quote", "phone": "emergency", "residential": "premium_residential",
    "renovation": "renovation_project", "technical": "technical_expertise",
    "projects": "portfolio", "local": "trust_first", "b2b": "commercial_b2b",
}


def normalize_business_intent(value: str) -> str:
    normalized = BUSINESS_INTENT_ALIASES.get(value, value)
    if normalized not in BUSINESS_INTENTS:
        return "balanced"
    return normalized

FACT_REQUIRED_FIELDS = frozenset({
    "years_experience", "project_count", "average_rating", "review_count", "rge", "qualibat",
    "qualipac", "insurance", "guarantee", "emergency_service", "response_delay", "opening_hours",
    "service_areas", "partners", "brands", "team", "prices", "availability", "statistics",
    "awards", "certifications", "client_count",
})
