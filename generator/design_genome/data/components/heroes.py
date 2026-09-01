"""Fifty structurally distinct hero blueprints."""

from ._factory import registry

HERO_IDS = (
    "full_bleed_photo_cover", "photo_left_service_intro", "photo_right_residential_intro",
    "centered_image_frame", "panorama_architectural", "cinematic_overlay_story", "editorial_photo_collage",
    "project_contact_sheet_hero", "material_macro_title", "vertical_portrait_manifesto", "floating_image_statement",
    "stacked_photos_narrative", "edge_crop_conversion", "oversized_type_local", "editorial_title_index",
    "centered_statement_quiet", "compact_conversion_panel", "mono_technical_diagnostic",
    "condensed_industrial_capability", "split_service_photo", "offset_residential_photo",
    "framed_luxury_scene", "layered_material_scene", "asymmetric_project_intro", "editorial_columns_manifesto",
    "project_canvas_feature", "gallery_led_sequence", "service_led_selector", "blueprint_spatial_scene",
    "isometric_system_explainer", "diagrammatic_process_map", "parallax_layered_material",
    "technical_nodes_network", "no_image_typographic_signal", "no_image_editorial_manifesto",
    "no_image_local_conversion", "diptych_transformation_intro", "triptych_material_intro",
    "before_after_transformation_pair", "documentary_work_log_hero", "workshop_gesture_cover",
    "lighting_atmosphere_cover", "architectural_void_statement", "brutalist_block_intro",
    "quiet_luxury_window", "residential_brief_intro", "phone_first_problem_solution",
    "quote_first_project_brief", "horizontal_rail_preview", "framed_blueprint_specification",
)

HERO_COMPONENTS = registry("hero", HERO_IDS)
assert len(HERO_COMPONENTS) == 50
