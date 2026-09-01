"""Thirty-five service compositions with explicit layout semantics."""

from ._factory import registry
from .profiles import SERVICES_PROFILES

SERVICE_GROUPS = {
    "rows": ("editorial_service_rows", "numbered_service_list", "sticky_service_detail", "alternating_service_feature", "quiet_service_chapters", "editorial_service_folio"),
    "grid": ("icon_service_grid", "stacked_service_panels", "residential_room_services", "service_comparison_columns"),
    "photo": ("photo_service_cards", "split_service_media"),
    "rail": ("horizontal_service_rail",),
    "index": ("large_typographic_service_index", "local_service_directory", "scope_of_work_ledger"),
    "accordion": ("service_accordion", "compact_mobile_service_actions"),
    "matrix": ("service_matrix", "service_masonry", "service_bento"),
    "process": ("process_like_services", "service_timeline"),
    "technical": ("technical_service_table", "capability_specification", "technical_system_layers"),
    "minimal": ("minimal_service_links",),
    "bento": ("brutalist_service_stack", "cinematic_service_reveal"),
    "conversion": ("problem_solution_services", "conversion_service_selector", "service_map_and_list"),
    "material": ("material_service_catalogue", "project_type_services", "workshop_service_samples"),
}

SERVICES_COMPONENTS = registry("services", SERVICE_GROUPS, SERVICES_PROFILES)
assert len(SERVICES_COMPONENTS) == 35
