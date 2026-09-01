"""Business/design archetypes that orient, but never template, SiteDNA."""

from .models import SiteArchetype
from .taxonomy import TRADES


ARCHETYPE_PURPOSES = {
    "local_emergency_service": (("emergency", "local_quote"), "resolve urgent local need", "immediate legibility and action", ("services", "phone", "city"), ("ambient_optional",), ("emergency_service", "service_areas"), "problem -> action -> services -> verified availability"),
    "premium_residential": (("premium_residential", "renovation_project"), "win considered residential projects", "calm spatial and material confidence", ("services", "approach"), ("residential_ambient",), ("reviews", "process"), "scene -> services -> approach -> contact"),
    "high_end_craft": (("craft", "premium_residential"), "present bespoke craft value", "make material judgment visible", ("services", "process"), ("material", "artisan_process"), ("process",), "material -> craft -> services -> consultation"),
    "architectural_contracting": (("renovation_project", "commercial_b2b"), "establish project delivery capability", "project-led architectural structure", ("services", "process"), ("artisan_project",), ("insurance", "project_evidence"), "project -> capabilities -> process -> contact"),
    "technical_expert": (("technical_expertise", "commercial_b2b"), "make technical capability understandable", "precise information hierarchy", ("services", "process"), ("diagram", "artisan_detail"), ("certifications", "process"), "problem -> system -> proof -> diagnostic"),
    "family_business": (("trust_first", "local_quote"), "build local relational trust", "warm credible familiarity", ("services", "identity", "city"), ("artisan_portrait_optional",), ("reviews", "service_areas"), "identity -> services -> proof -> contact"),
    "project_portfolio": (("portfolio", "renovation_project"), "convert documented work into enquiries", "give projects visual priority", ("project_context", "services"), ("artisan_project",), ("project_evidence",), "project cover -> casebook -> services -> enquiry"),
    "luxury_renovation": (("premium_residential", "renovation_project"), "frame complex renovation as a guided project", "cinematic but restrained transformation", ("services", "process"), ("artisan_project", "ambient"), ("reviews", "process"), "scene -> transformation -> method -> contact"),
    "industrial_specialist": (("commercial_b2b", "technical_expertise"), "communicate B2B capability and scope", "dense industrial clarity", ("services", "sectors", "process"), ("artisan_detail",), ("certifications", "insurance"), "capability -> sectors -> proof -> contact"),
    "conversion_first_local": (("local_quote", "trust_first"), "generate qualified local enquiries", "fast scannability without cheap urgency", ("services", "city", "contact"), ("ambient_optional",), ("reviews", "service_areas"), "need -> services -> proof -> quote"),
    "editorial_studio": (("portfolio", "craft"), "express a distinctive point of view", "editorial hierarchy and rhythm", ("manifesto", "services"), ("mixed_editorial",), (), "premise -> chapters -> services -> contact"),
    "warm_artisan": (("craft", "trust_first"), "connect craft and local service", "warm documentary credibility", ("services", "process"), ("artisan_process",), ("process",), "identity -> gesture -> services -> contact"),
    "minimal_architecture": (("portfolio", "balanced"), "present selected work with restraint", "proportion and architectural calm", ("services",), ("selected_image",), (), "statement -> selected work -> contact"),
    "bold_local": (("local_quote", "balanced"), "create strong local visibility", "bold type and direct service hierarchy", ("services", "city"), ("ambient_optional",), ("service_areas",), "signal -> services -> proof -> action"),
    "documentary_craft": (("craft", "portfolio"), "demonstrate method through real process", "chronological documentary texture", ("process", "services"), ("artisan_process",), ("process",), "context -> process -> work -> contact"),
    "design_build": (("renovation_project", "premium_residential"), "explain integrated project journey", "phase-led architectural narrative", ("process", "services"), ("artisan_project",), ("process", "project_evidence"), "brief -> design -> build -> reveal -> contact"),
    "heritage_craft": (("craft", "trust_first"), "present restoration or inherited skill honestly", "material history without invented heritage", ("history", "services"), ("artisan_archive",), ("history",), "verified history -> material -> process -> contact"),
    "spatial_technical": (("technical_expertise", "commercial_b2b"), "explain systems spatially", "layered technical relationships", ("services", "system_map"), ("diagram",), ("process",), "system -> capabilities -> process -> contact"),
    "material_led": (("craft", "premium_residential"), "lead with finish and material judgment", "macro-to-context material rhythm", ("services", "materials"), ("material",), (), "material -> applications -> services -> contact"),
    "quiet_luxury": (("premium_residential", "balanced"), "signal high consideration through restraint", "quiet contrast and generous space", ("services", "approach"), ("selected_image",), ("process",), "statement -> selected services -> approach -> contact"),
}


def _a(
    id: str,
    intents: tuple[str, ...],
    traits: tuple[str, ...],
    silhouettes: tuple[str, ...],
    directions: tuple[str, ...],
    conversion: float,
    density: int,
    trust: int,
    images: int,
    trades: tuple[str, ...] = TRADES,
) -> SiteArchetype:
    mapped_intents, business, visual, content, media, trust_needs, narrative = ARCHETYPE_PURPOSES[id]
    return SiteArchetype(
        id=id,
        business_intents=frozenset(mapped_intents),
        compatible_trades=frozenset(trades),
        traits=frozenset(traits),
        preferred_silhouettes=silhouettes,
        preferred_directions=directions,
        conversion_intensity=conversion,
        target_density=density,
        trust_need=trust,
        image_need=images,
        business_purpose=business,
        visual_purpose=visual,
        content_needs=content,
        media_needs=media,
        trust_needs=trust_needs,
        recommended_narrative=narrative,
    )


ARCHETYPES = {
    item.id: item for item in (
        _a("local_emergency_service", ("emergency", "phone"), ("local", "conversion_led", "phone_first"), ("urgent_local", "phone_first_service"), ("conversion_premium",), .95, 4, 5, 1, ("plombier", "electricien")),
        _a("premium_residential", ("residential", "renovation"), ("luxurious", "visual_led", "trust_led"), ("premium_residential", "editorial_residential"), ("editorial_luxury", "cinematic_luxury"), .58, 2, 4, 6),
        _a("high_end_craft", ("bespoke", "craft"), ("warm", "tactile", "material_led"), ("craft_material_story", "workshop_journey"), ("warm_craft", "material_editorial"), .42, 2, 3, 5, ("menuisier", "peintre", "macon")),
        _a("architectural_contracting", ("architecture", "contracting"), ("architectural", "project_led", "technical"), ("architectural_contracting", "project_ledger"), ("minimal_architecture", "architectural_brutalist"), .48, 3, 4, 8, ("macon", "renovateur", "menuisier")),
        _a("technical_expert", ("technical", "expertise"), ("technical", "information_dense", "trust_led"), ("technical_capabilities", "specification_first"), ("technical_spatial", "minimal_architecture"), .68, 4, 5, 3, ("electricien", "plombier", "macon")),
        _a("family_business", ("local", "relationship"), ("warm", "local", "trust_led"), ("family_trust", "local_service_story"), ("warm_craft", "conversion_premium"), .66, 3, 5, 3),
        _a("project_portfolio", ("projects", "portfolio"), ("portfolio", "project_led", "visual_led"), ("project_ledger", "gallery_sequence"), ("minimal_architecture", "editorial_luxury"), .28, 2, 2, 10),
        _a("luxury_renovation", ("luxury", "renovation"), ("luxurious", "cinematic", "story_led"), ("transformation_story", "cinematic_residential"), ("cinematic_luxury", "editorial_luxury"), .46, 2, 4, 8, ("renovateur", "peintre", "menuisier")),
        _a("industrial_specialist", ("industrial", "b2b"), ("industrial", "technical", "information_dense"), ("industrial_capabilities", "technical_capabilities"), ("technical_spatial", "architectural_brutalist"), .55, 4, 5, 4, ("electricien", "macon", "menuisier")),
        _a("conversion_first_local", ("quote", "local"), ("conversion_led", "local", "service_led"), ("local_conversion", "quote_first_service"), ("conversion_premium", "minimal_architecture"), .90, 4, 4, 2),
        _a("editorial_studio", ("editorial", "brand"), ("editorial", "story_led", "asymmetric"), ("editorial_manifesto", "magazine_service"), ("editorial_luxury", "material_editorial"), .25, 2, 1, 6),
        _a("warm_artisan", ("craft", "local"), ("warm", "local", "documentary"), ("warm_artisan", "workshop_journey"), ("warm_craft",), .55, 3, 3, 4),
        _a("minimal_architecture", ("minimal", "projects"), ("minimal", "architectural", "quiet"), ("minimal_statement", "project_ledger"), ("minimal_architecture",), .22, 1, 2, 6),
        _a("bold_local", ("local", "visibility"), ("bold", "conversion_led", "service_led"), ("bold_local", "local_conversion"), ("conversion_premium", "architectural_brutalist"), .84, 4, 3, 2),
        _a("documentary_craft", ("craft", "process"), ("documentary", "story_led", "tactile"), ("documentary_process", "craft_material_story"), ("warm_craft", "material_editorial"), .32, 2, 3, 8),
        _a("design_build", ("design", "build"), ("architectural", "project_led", "story_led"), ("design_build_journey", "transformation_story"), ("minimal_architecture", "editorial_luxury"), .50, 3, 4, 7, ("renovateur", "macon", "menuisier")),
        _a("heritage_craft", ("heritage", "restoration"), ("warm", "editorial", "material_led"), ("heritage_story", "craft_material_story"), ("material_editorial", "warm_craft"), .30, 2, 4, 6, ("menuisier", "macon", "peintre")),
        _a("spatial_technical", ("technical", "innovation"), ("technical", "futuristic", "layered"), ("spatial_explainer", "technical_capabilities"), ("technical_spatial",), .45, 3, 4, 3, ("electricien", "plombier", "macon")),
        _a("material_led", ("materials", "finish"), ("material", "tactile", "visual_led"), ("material_library", "editorial_manifesto"), ("material_editorial", "warm_craft"), .24, 2, 2, 8, ("peintre", "menuisier", "macon", "renovateur")),
        _a("quiet_luxury", ("luxury", "calm"), ("luxurious", "quiet", "minimal"), ("quiet_luxury", "premium_residential"), ("editorial_luxury", "minimal_architecture"), .28, 1, 3, 6),
    )
}
