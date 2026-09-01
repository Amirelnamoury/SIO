"""Concrete motion, spatial and mobile capability registries."""

from ..models import MobilePersonality, MotionSystem, SpatialSystem


def _m(id, intensity, techniques, cost, fallback, traits, entry, scroll, image, text, stagger, hover, navigation, budget):
    return MotionSystem(id, intensity, techniques, cost, fallback, frozenset(traits), entry, scroll, image, text, stagger, hover, navigation, budget)


MOTION_SYSTEMS = {item.id: item for item in (
    _m("none", 0, (), 0, "none", ("quiet", "accessible"), "none", "native", "none", "none", "none", "state_only", "instant", 0),
    _m("micro_feedback", 1, ("hover", "focus", "button_state"), 1, "instant_state", ("conversion_led",), "none", "native", "none", "none", "none", "color_and_border", "instant", 20),
    _m("soft_fade", 1, ("opacity_reveal",), 1, "visible", ("minimal", "quiet"), "short_opacity", "native", "none", "short_opacity", "none", "state_only", "instant", 50),
    _m("directional_slide", 2, ("short_translate",), 1, "visible", ("service_led",), "8px_translate", "native", "none", "8px_translate", "40ms", "small_translate", "instant", 70),
    _m("editorial_reveal", 2, ("line_mask", "image_reveal"), 2, "visible", ("editorial",), "line_reveal", "native", "clip_reveal", "line_reveal", "60ms", "crop_shift", "quiet_crossfade", 100),
    _m("measured_stagger", 2, ("small_stagger",), 2, "visible", ("modular",), "opacity_translate", "native", "opacity", "opacity", "60ms_max_5", "state_only", "instant", 100),
    _m("image_crop_reveal", 3, ("clip_path_reveal",), 2, "uncropped_image", ("visual_led",), "none", "native", "clip_reveal", "none", "none", "crop_shift", "instant", 120),
    _m("subtle_parallax", 3, ("limited_parallax",), 3, "static_position", ("cinematic",), "soft_fade", "limited_depth", "max_4_percent_depth", "soft_fade", "none", "none", "crossfade", 140),
    _m("sticky_storytelling", 4, ("sticky_chapter",), 3, "linear_chapters", ("story_led",), "visible", "sticky_chapters", "chapter_swap", "chapter_swap", "none", "none", "instant", 160),
    _m("horizontal_rail", 3, ("horizontal_scroll", "snap"), 2, "vertical_list", ("portfolio",), "visible", "native_horizontal_snap", "none", "none", "none", "caption_state", "instant", 100),
    _m("cinematic_sequence", 4, ("chapter_crossfade", "slow_scale"), 4, "linear_sequence", ("cinematic",), "poster_first", "chapter_crossfade", "slow_scale_max_3_percent", "soft_fade", "none", "none", "fade", 180),
    _m("spatial_explainer", 4, ("diagram_progress", "depth_layers"), 4, "static_diagram", ("technical", "spatial"), "static_then_enhance", "diagram_progress", "layer_depth", "none", "none", "node_highlight", "instant", 180),
)}

SPATIAL_SYSTEMS = {item.id: item for item in (
    SpatialSystem("none", 0, (), "none", "none", 0),
    SpatialSystem("diagrammatic", 1, ("svg_diagram",), "static_svg", "static_svg", 1),
    SpatialSystem("isometric", 2, ("isometric_svg",), "flat_diagram", "flat_diagram", 2),
    SpatialSystem("layered_2_5d", 2, ("layered_css",), "flat_layers", "flat_layers", 2),
    SpatialSystem("parallax_depth", 3, ("limited_parallax",), "stacked_media", "stacked_media", 3),
    SpatialSystem("css_perspective", 3, ("css_perspective",), "flat_cards", "flat_cards", 2),
    SpatialSystem("svg_spatial", 3, ("animated_svg",), "static_svg", "static_svg", 2),
    SpatialSystem("lightweight_canvas", 4, ("canvas_diagram",), "static_image", "static_image", 4),
    SpatialSystem("webgl_optional", 5, ("progressive_webgl",), "poster_image", "poster_image", 5),
)}


def _p(id, navigation, hero, gallery, cta, spacing, motion, priority, traits, header, crop, scale, section_spacing):
    return MobilePersonality(id, navigation, hero, gallery, cta, spacing, motion, priority, frozenset(traits), header, crop, scale, section_spacing)


MOBILE_PERSONALITIES = {item.id: item for item in (
    _p("editorial_crop", "compact_drawer", "title_then_subject_crop", "vertical_folio", "inline", .72, "reduced", ("identity", "story", "services", "contact"), ("editorial",), 64, "editorial_subject_safe", .62, 80),
    _p("conversion_immediate", "compact_top_bar", "action_above_fold", "two_column_to_swipe", "sticky_bottom", .82, "micro_only", ("identity", "primary_action", "services", "proof"), ("conversion_led",), 56, "supporting_media_only", .72, 64),
    _p("technical_compact", "accordion_navigation", "flatten_diagram", "technical_list", "inline", .76, "reduced", ("identity", "capabilities", "process", "contact"), ("technical",), 60, "diagram_no_crop", .68, 56),
    _p("brutalist_grid", "oversized_overlay", "retain_type_signal", "edge_scroll", "fixed_corner", .70, "limited", ("identity", "services", "projects", "contact"), ("brutal",), 68, "hard_edge", .64, 72),
    _p("craft_immersive", "warm_drawer", "detail_first_crop", "material_swipe", "inline", .80, "soft", ("identity", "materials", "services", "process"), ("warm", "material"), 64, "material_detail_safe", .70, 72),
    _p("cinematic_sequence", "full_screen_menu", "poster_then_story", "chapter_stack", "end_chapter", .74, "reduced", ("identity", "story", "projects", "contact"), ("cinematic",), 64, "poster_subject_safe", .62, 88),
    _p("minimal_calm", "logo_menu", "statement_first", "single_image", "quiet_link", .86, "none", ("identity", "services", "contact"), ("minimal", "quiet"), 60, "single_subject_safe", .68, 88),
    _p("phone_action_dock", "compact_top_bar", "problem_then_phone", "service_list", "bottom_actions", .82, "micro_only", ("identity", "phone", "services", "area"), ("phone_first", "local"), 56, "ambient_optional", .72, 56),
    _p("project_casebook", "project_index", "project_cover", "snap_casebook", "project_enquiry", .76, "reduced", ("identity", "projects", "services", "contact"), ("project_led",), 64, "project_context_safe", .66, 72),
    _p("documentary_chapters", "drawer", "captioned_image", "chapter_stack", "inline", .80, "soft", ("identity", "process", "people", "services"), ("documentary",), 64, "documentary_context", .68, 72),
    _p("local_information", "action_dock", "compact_conversion", "service_accordion", "sticky_quote", .84, "micro_only", ("identity", "city", "services", "contact"), ("local",), 56, "ambient_optional", .72, 56),
    _p("spatial_fallback", "compact_drawer", "static_diagram", "linear_explainer", "inline", .76, "static", ("identity", "diagram", "capabilities", "contact"), ("spatial", "technical"), 60, "diagram_no_crop", .68, 64),
)}

assert len(MOTION_SYSTEMS) == 12
assert len(SPATIAL_SYSTEMS) == 9
assert len(MOBILE_PERSONALITIES) == 12
