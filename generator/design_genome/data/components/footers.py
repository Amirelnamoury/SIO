"""Twenty footer systems from quiet legal line to rich local directory."""

from ._factory import registry

FOOTER_IDS = (
    "ultra_minimal_footer", "business_information_footer", "navigation_columns_footer",
    "service_links_footer", "service_area_footer", "contact_first_footer", "legal_compact_footer",
    "large_brand_statement_footer", "cta_footer_hybrid", "visual_image_footer", "centered_mark_footer",
    "editorial_directory_footer", "oversized_wordmark_footer", "local_business_footer",
    "project_index_footer", "workshop_signature_footer", "technical_spec_footer", "dark_overlay_footer",
    "split_contact_footer", "mobile_action_footer",
)

FOOTER_COMPONENTS = registry("footer", FOOTER_IDS)
assert len(FOOTER_COMPONENTS) == 20
