"""Twenty-five headers with explicit semantic profile assignments."""

from ._factory import registry
from .profiles import HEADER_PROFILES
from .variants import HEADER_VARIANTS

HEADER_GROUPS = {
    "classic": ("classic_brand_left", "split_navigation", "compact_sticky_nav", "framed_canvas_header"),
    "centered": ("centered_brand_quiet", "minimal_logo_only"),
    "contact": ("utility_contact_bar", "phone_first_compact", "mega_contact_header", "conversion_action_dock_header"),
    "overlay": ("transparent_overlay_nav", "dark_overlay_nav"),
    "editorial": ("editorial_index_nav", "oversized_menu_trigger"),
    "rail": ("architectural_side_rail", "side_rail_projects"),
    "local": ("two_row_local", "local_info_strip", "residential_project_header"),
    "technical": ("blueprint_utility_header", "service_category_header"),
    "statement": ("floating_capsule_nav", "workshop_mark_header", "statement_wordmark_header"),
    "gallery": ("gallery_bottom_nav",),
}

HEADER_COMPONENTS = registry(
    "header", HEADER_GROUPS, HEADER_PROFILES, HEADER_VARIANTS,
    {"phone_first_compact": {"required_data": ("phone",), "required_any_data": ()}},
)
assert len(HEADER_COMPONENTS) == 25
