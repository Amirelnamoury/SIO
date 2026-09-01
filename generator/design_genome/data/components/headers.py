"""Twenty-five desktop header blueprints."""

from ._factory import registry

HEADER_IDS = (
    "classic_brand_left", "centered_brand_quiet", "utility_contact_bar", "phone_first_compact",
    "split_navigation", "floating_capsule_nav", "transparent_overlay_nav", "editorial_index_nav",
    "architectural_side_rail", "compact_sticky_nav", "mega_contact_header", "minimal_logo_only",
    "two_row_local", "local_info_strip", "dark_overlay_nav", "oversized_menu_trigger",
    "side_rail_projects", "workshop_mark_header", "blueprint_utility_header", "gallery_bottom_nav",
    "framed_canvas_header", "statement_wordmark_header", "service_category_header",
    "residential_project_header", "conversion_action_dock_header",
)

HEADER_COMPONENTS = registry("header", HEADER_IDS)
assert len(HEADER_COMPONENTS) == 25
