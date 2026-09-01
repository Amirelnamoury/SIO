"""Thirty-five service compositions that avoid a card-only vocabulary."""

from ._factory import registry

SERVICE_IDS = (
    "editorial_service_rows", "numbered_service_list", "icon_service_grid", "photo_service_cards",
    "sticky_service_detail", "horizontal_service_rail", "alternating_service_feature",
    "large_typographic_service_index", "service_accordion", "service_masonry", "service_matrix",
    "process_like_services", "technical_service_table", "minimal_service_links", "split_service_media",
    "service_bento", "stacked_service_panels", "material_service_catalogue", "residential_room_services",
    "problem_solution_services", "local_service_directory", "capability_specification", "project_type_services",
    "scope_of_work_ledger", "service_timeline", "service_comparison_columns", "service_map_and_list",
    "quiet_service_chapters", "brutalist_service_stack", "workshop_service_samples", "cinematic_service_reveal",
    "conversion_service_selector", "technical_system_layers", "editorial_service_folio",
    "compact_mobile_service_actions",
)

SERVICES_COMPONENTS = registry("services", SERVICE_IDS)
assert len(SERVICES_COMPONENTS) == 35
