"""Registry for the compositional grammar used by Site Vitrine V3."""

from __future__ import annotations

DESIGN_ENGINE_VERSION = "v3.0"

ART_DIRECTIONS = (
    "editorial_luxury",
    "bold_conversion",
    "technical_spatial",
    "architectural_brutalist",
    "warm_craft",
    "cinematic_luxury",
    "minimal_architecture",
    "material_editorial",
)

PAGE_SILHOUETTES = {
    "editorial_story": ("hero", "manifesto", "gallery", "services", "featured_project", "before_after", "process", "service_area", "contact"),
    "project_first": ("hero", "featured_project", "gallery", "manifesto", "services", "about", "contact"),
    "conversion_first": ("hero", "trust", "services", "stats", "gallery", "reviews", "service_area", "contact"),
    "cinematic_scroll": ("hero", "manifesto", "featured_project", "before_after", "gallery", "services", "contact"),
    "architectural_grid": ("hero", "gallery", "services", "process", "about", "service_area", "contact"),
    "split_narrative": ("hero", "about", "services", "featured_project", "reviews", "contact"),
    "atelier_story": ("hero", "manifesto", "about", "gallery", "services", "process", "contact"),
    "technical_spatial": ("hero", "services", "process", "featured_project", "trust", "contact"),
    "gallery_first": ("hero", "gallery", "featured_project", "services", "about", "contact"),
    "minimal_sequence": ("hero", "manifesto", "services", "gallery", "contact"),
    "brutalist_stack": ("hero", "services", "gallery", "process", "service_area", "contact"),
    "immersive_panels": ("hero", "featured_project", "manifesto", "gallery", "before_after", "contact"),
}

HEADER_SYSTEMS = ("quiet_inline", "editorial_index", "utility_conversion", "architectural_rail", "atelier_mark", "cinematic_overlay")
HERO_SYSTEMS = (
    "full_bleed_photo", "editorial_offset", "oversized_type", "split_architecture",
    "project_canvas", "conversion_panel", "isometric_spatial", "blueprint_scene",
    "material_macro", "gallery_collage", "cinematic_layered", "minimal_statement",
)
TYPOGRAPHY_SYSTEMS = (
    "editorial_serif", "luxury_serif", "grotesk_bold", "condensed_industrial",
    "swiss_neutral", "humanist_craft", "architectural_sans",
)
LAYOUT_GRIDS = ("offset_12", "strict_12", "asymmetric_8", "split_5_7", "rail_10", "fluid_editorial")
SPACING_RHYTHMS = ("compact", "measured", "spacious", "cinematic")
SURFACE_SYSTEMS = ("paper", "ink", "concrete", "timber", "signal", "gallery_white", "night_plan")
PHOTO_STRATEGIES = (
    "hero_dominant", "project_dominant", "editorial_mix", "macro_material", "craft_detail",
    "architectural_wide", "before_after_focus", "technical_detail", "cinematic_sequence", "minimal_photo",
)
IMAGE_TREATMENTS = ("natural", "warm", "monochrome", "high_contrast", "material", "cinematic", "cutout")
PROJECT_SHOWCASES = ("single_monument", "offset_diptych", "editorial_trio", "masonry_sequence", "horizontal_rail", "before_after", "numbered_catalogue")
SERVICES_COMPOSITIONS = ("typographic_index", "conversion_grid", "technical_schedule", "material_list", "monumental_stack", "editorial_columns")
CONTENT_DENSITIES = ("compact", "balanced", "airy")
SECTION_TRANSITIONS = ("none", "rule", "overlap", "color_field", "crop", "index_marker")
CTA_SYSTEMS = ("quiet_link", "dual_action", "sticky_conversion", "monumental_prompt", "project_enquiry")
MOTION_LEVELS = ("none", "subtle", "editorial", "cinematic", "spatial")
SPATIAL_LEVELS = ("none", "graphic", "layered", "interactive_light")
DECORATION_SYSTEMS = ("none", "editorial_rules", "technical_grid", "material_blocks", "brutalist_geometry", "cinematic_mask")
FOOTER_SYSTEMS = ("quiet_line", "editorial_directory", "utility_columns", "monumental_end", "atelier_signature")
MOBILE_PERSONALITIES = ("editorial_crop", "conversion_immediate", "technical_compact", "brutalist_grid", "craft_immersive", "cinematic_sequence", "minimal_calm")
AMBIENCES = ("calm", "bold", "warm", "dark", "luminous", "material")

PROFILE_VALUES = {
    "art_direction": set(ART_DIRECTIONS),
    "page_silhouette": set(PAGE_SILHOUETTES),
    "header_system": set(HEADER_SYSTEMS),
    "hero_system": set(HERO_SYSTEMS),
    "typography_system": set(TYPOGRAPHY_SYSTEMS),
    "layout_grid": set(LAYOUT_GRIDS),
    "spacing_rhythm": set(SPACING_RHYTHMS),
    "surface_system": set(SURFACE_SYSTEMS),
    "photo_strategy": set(PHOTO_STRATEGIES),
    "image_treatment": set(IMAGE_TREATMENTS),
    "project_showcase": set(PROJECT_SHOWCASES),
    "services_composition": set(SERVICES_COMPOSITIONS),
    "content_density": set(CONTENT_DENSITIES),
    "section_transitions": set(SECTION_TRANSITIONS),
    "cta_system": set(CTA_SYSTEMS),
    "motion_level": set(MOTION_LEVELS),
    "spatial_level": set(SPATIAL_LEVELS),
    "decoration_system": set(DECORATION_SYSTEMS),
    "footer_system": set(FOOTER_SYSTEMS),
    "mobile_personality": set(MOBILE_PERSONALITIES),
    "ambience": set(AMBIENCES),
}

# Directions constrain a grammar without becoming templates. Multiple valid
# systems remain available on every structural axis.
DIRECTION_RULES = {
    "editorial_luxury": {
        "silhouettes": ("editorial_story", "gallery_first", "split_narrative", "minimal_sequence"),
        "headers": ("quiet_inline", "editorial_index"),
        "heroes": ("editorial_offset", "material_macro", "gallery_collage", "minimal_statement"),
        "type": ("editorial_serif", "luxury_serif"), "surface": ("paper", "gallery_white"),
        "services": ("typographic_index", "editorial_columns"), "mobile": ("editorial_crop", "minimal_calm"),
    },
    "bold_conversion": {
        "silhouettes": ("conversion_first", "split_narrative", "brutalist_stack"),
        "headers": ("utility_conversion", "quiet_inline"),
        "heroes": ("conversion_panel", "full_bleed_photo", "oversized_type"),
        "type": ("grotesk_bold", "architectural_sans"), "surface": ("signal", "gallery_white"),
        "services": ("conversion_grid", "typographic_index"), "mobile": ("conversion_immediate",),
    },
    "technical_spatial": {
        "silhouettes": ("technical_spatial", "architectural_grid", "split_narrative"),
        "headers": ("architectural_rail", "quiet_inline"),
        "heroes": ("isometric_spatial", "blueprint_scene", "split_architecture"),
        "type": ("swiss_neutral", "architectural_sans"), "surface": ("night_plan", "ink"),
        "services": ("technical_schedule", "typographic_index"), "mobile": ("technical_compact",),
    },
    "architectural_brutalist": {
        "silhouettes": ("brutalist_stack", "architectural_grid", "project_first"),
        "headers": ("architectural_rail", "editorial_index"),
        "heroes": ("oversized_type", "split_architecture", "project_canvas"),
        "type": ("condensed_industrial", "grotesk_bold"), "surface": ("concrete", "ink"),
        "services": ("monumental_stack", "technical_schedule"), "mobile": ("brutalist_grid",),
    },
    "warm_craft": {
        "silhouettes": ("atelier_story", "split_narrative", "gallery_first"),
        "headers": ("atelier_mark", "quiet_inline"),
        "heroes": ("material_macro", "editorial_offset", "gallery_collage"),
        "type": ("humanist_craft", "editorial_serif"), "surface": ("timber", "paper"),
        "services": ("material_list", "editorial_columns"), "mobile": ("craft_immersive",),
    },
    "cinematic_luxury": {
        "silhouettes": ("cinematic_scroll", "immersive_panels", "project_first"),
        "headers": ("cinematic_overlay", "quiet_inline"),
        "heroes": ("cinematic_layered", "full_bleed_photo", "project_canvas"),
        "type": ("luxury_serif", "architectural_sans"), "surface": ("ink", "gallery_white"),
        "services": ("editorial_columns", "typographic_index"), "mobile": ("cinematic_sequence",),
    },
    "minimal_architecture": {
        "silhouettes": ("minimal_sequence", "project_first", "architectural_grid"),
        "headers": ("quiet_inline", "architectural_rail"),
        "heroes": ("minimal_statement", "project_canvas", "editorial_offset"),
        "type": ("swiss_neutral", "architectural_sans"), "surface": ("gallery_white", "paper"),
        "services": ("typographic_index", "technical_schedule"), "mobile": ("minimal_calm",),
    },
    "material_editorial": {
        "silhouettes": ("editorial_story", "atelier_story", "immersive_panels"),
        "headers": ("editorial_index", "atelier_mark"),
        "heroes": ("material_macro", "oversized_type", "editorial_offset"),
        "type": ("editorial_serif", "humanist_craft"), "surface": ("timber", "concrete", "paper"),
        "services": ("material_list", "monumental_stack"), "mobile": ("editorial_crop", "craft_immersive"),
    },
}

TRADE_DIRECTIONS = {
    "peintre": ("editorial_luxury", "material_editorial", "minimal_architecture"),
    "peinture": ("editorial_luxury", "material_editorial", "minimal_architecture"),
    "plombier": ("bold_conversion", "minimal_architecture", "technical_spatial"),
    "plomberie": ("bold_conversion", "minimal_architecture", "technical_spatial"),
    "electricien": ("technical_spatial", "minimal_architecture", "bold_conversion"),
    "electricite": ("technical_spatial", "minimal_architecture", "bold_conversion"),
    "macon": ("architectural_brutalist", "minimal_architecture", "material_editorial"),
    "maconnerie": ("architectural_brutalist", "minimal_architecture", "material_editorial"),
    "menuisier": ("warm_craft", "material_editorial", "editorial_luxury"),
    "menuiserie": ("warm_craft", "material_editorial", "editorial_luxury"),
    "renovateur": ("cinematic_luxury", "editorial_luxury", "minimal_architecture"),
    "renovation": ("cinematic_luxury", "editorial_luxury", "minimal_architecture"),
}
