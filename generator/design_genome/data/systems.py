"""Motion, spatial and mobile capability registries."""

from ..models import MobilePersonality, MotionSystem, SpatialSystem


MOTION_SYSTEMS = {
    item.id: item for item in (
        MotionSystem("none", 0, (), 0, "none", frozenset({"quiet", "accessible"})),
        MotionSystem("micro_feedback", 1, ("hover", "focus", "button_state"), 1, "instant_state", frozenset({"conversion_led"})),
        MotionSystem("soft_fade", 1, ("opacity_reveal",), 1, "visible", frozenset({"minimal", "quiet"})),
        MotionSystem("directional_slide", 2, ("short_translate",), 1, "visible", frozenset({"service_led"})),
        MotionSystem("editorial_reveal", 2, ("line_mask", "image_reveal"), 2, "visible", frozenset({"editorial"})),
        MotionSystem("measured_stagger", 2, ("small_stagger",), 2, "visible", frozenset({"modular"})),
        MotionSystem("image_crop_reveal", 3, ("clip_path_reveal",), 2, "uncropped_image", frozenset({"visual_led"})),
        MotionSystem("subtle_parallax", 3, ("limited_parallax",), 3, "static_position", frozenset({"cinematic"})),
        MotionSystem("sticky_storytelling", 4, ("sticky_chapter",), 3, "linear_chapters", frozenset({"story_led"})),
        MotionSystem("horizontal_rail", 3, ("horizontal_scroll", "snap"), 2, "vertical_list", frozenset({"portfolio"})),
        MotionSystem("cinematic_sequence", 4, ("chapter_crossfade", "slow_scale"), 4, "linear_sequence", frozenset({"cinematic"})),
        MotionSystem("spatial_explainer", 4, ("diagram_progress", "depth_layers"), 4, "static_diagram", frozenset({"technical", "spatial"})),
    )
}

SPATIAL_SYSTEMS = {
    item.id: item for item in (
        SpatialSystem("none", 0, (), "none", "none", 0),
        SpatialSystem("diagrammatic", 1, ("svg_diagram",), "static_svg", "static_svg", 1),
        SpatialSystem("isometric", 2, ("isometric_svg",), "flat_diagram", "flat_diagram", 2),
        SpatialSystem("layered_2_5d", 2, ("layered_css",), "flat_layers", "flat_layers", 2),
        SpatialSystem("parallax_depth", 3, ("limited_parallax",), "stacked_media", "stacked_media", 3),
        SpatialSystem("css_perspective", 3, ("css_perspective",), "flat_cards", "flat_cards", 2),
        SpatialSystem("svg_spatial", 3, ("animated_svg",), "static_svg", "static_svg", 2),
        SpatialSystem("lightweight_canvas", 4, ("canvas_diagram",), "static_image", "static_image", 4),
        SpatialSystem("webgl_optional", 5, ("progressive_webgl",), "poster_image", "poster_image", 5),
    )
}

MOBILE_PERSONALITIES = {
    item.id: item for item in (
        MobilePersonality("editorial_crop", "compact_drawer", "preserve_title_then_crop", "vertical_folio", "inline", .72, "reduced", ("identity", "story", "services", "contact"), frozenset({"editorial"})),
        MobilePersonality("conversion_immediate", "compact_top_bar", "action_above_fold", "two_column_to_swipe", "sticky_bottom", .82, "micro_only", ("identity", "primary_action", "services", "proof"), frozenset({"conversion_led"})),
        MobilePersonality("technical_compact", "accordion_navigation", "flatten_diagram", "technical_list", "inline", .76, "reduced", ("identity", "capabilities", "process", "contact"), frozenset({"technical"})),
        MobilePersonality("brutalist_grid", "oversized_overlay", "retain_type_scale", "edge_scroll", "fixed_corner", .70, "limited", ("identity", "services", "projects", "contact"), frozenset({"brutal"})),
        MobilePersonality("craft_immersive", "warm_drawer", "detail_first_crop", "material_swipe", "inline", .80, "soft", ("identity", "materials", "services", "process"), frozenset({"warm", "material"})),
        MobilePersonality("cinematic_sequence", "full_screen_menu", "poster_then_story", "chapter_stack", "end_chapter", .74, "reduced", ("identity", "story", "projects", "contact"), frozenset({"cinematic"})),
        MobilePersonality("minimal_calm", "logo_menu", "statement_first", "single_image", "quiet_link", .86, "none", ("identity", "services", "contact"), frozenset({"minimal", "quiet"})),
        MobilePersonality("phone_action_dock", "compact_top_bar", "problem_then_phone", "service_list", "bottom_actions", .82, "micro_only", ("identity", "phone", "services", "area"), frozenset({"phone_first", "local"})),
        MobilePersonality("project_casebook", "project_index", "project_cover", "snap_casebook", "project_enquiry", .76, "reduced", ("identity", "projects", "services", "contact"), frozenset({"project_led"})),
        MobilePersonality("documentary_chapters", "drawer", "captioned_image", "chapter_stack", "inline", .80, "soft", ("identity", "process", "people", "services"), frozenset({"documentary"})),
        MobilePersonality("local_information", "action_dock", "compact_conversion", "service_accordion", "sticky_quote", .84, "micro_only", ("identity", "city", "services", "contact"), frozenset({"local"})),
        MobilePersonality("spatial_fallback", "compact_drawer", "static_diagram", "linear_explainer", "inline", .76, "static", ("identity", "diagram", "capabilities", "contact"), frozenset({"spatial", "technical"})),
    )
}

assert len(MOTION_SYSTEMS) == 12
assert len(SPATIAL_SYSTEMS) == 9
assert len(MOBILE_PERSONALITIES) == 12
