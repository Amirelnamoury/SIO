"""Fifty heroes with resolved renderer-oriented blueprint specs."""

from ._factory import registry
from .profiles import HERO_PROFILES

HERO_GROUPS = {
    "photo_cover": ("full_bleed_photo_cover", "centered_image_frame", "panorama_architectural", "lighting_atmosphere_cover"),
    "split_photo": ("photo_left_service_intro", "photo_right_residential_intro", "split_service_photo", "offset_residential_photo", "residential_brief_intro"),
    "collage": ("editorial_photo_collage", "floating_image_statement", "stacked_photos_narrative", "diptych_transformation_intro", "triptych_material_intro"),
    "cinematic": ("cinematic_overlay_story", "framed_luxury_scene", "quiet_luxury_window"),
    "project": ("project_contact_sheet_hero", "asymmetric_project_intro", "project_canvas_feature", "gallery_led_sequence", "documentary_work_log_hero"),
    "material": ("material_macro_title", "layered_material_scene", "parallax_layered_material", "workshop_gesture_cover"),
    "typographic": ("oversized_type_local", "editorial_title_index", "centered_statement_quiet", "editorial_columns_manifesto", "no_image_typographic_signal", "no_image_editorial_manifesto", "no_image_local_conversion", "architectural_void_statement", "brutalist_block_intro"),
    "conversion": ("edge_crop_conversion", "compact_conversion_panel", "service_led_selector", "phone_first_problem_solution", "quote_first_project_brief"),
    "technical": ("mono_technical_diagnostic", "condensed_industrial_capability", "diagrammatic_process_map", "technical_nodes_network", "framed_blueprint_specification"),
    "spatial": ("blueprint_spatial_scene", "isometric_system_explainer"),
    "transformation": ("before_after_transformation_pair",),
    "rail": ("horizontal_rail_preview", "vertical_portrait_manifesto"),
}

HERO_COMPONENTS = registry(
    "hero", HERO_GROUPS, HERO_PROFILES,
    {"phone_first_problem_solution": {"required_data": ("phone",), "required_any_data": ()}},
)
assert len(HERO_COMPONENTS) == 50
