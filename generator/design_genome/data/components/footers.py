"""Twenty footer blueprints with explicit information architecture."""

from ._factory import registry
from .profiles import FOOTER_PROFILES
from .variants import FOOTER_VARIANTS

FOOTER_GROUPS = {
    "minimal": ("ultra_minimal_footer", "legal_compact_footer", "centered_mark_footer"),
    "business": ("business_information_footer", "local_business_footer"),
    "navigation": ("navigation_columns_footer", "editorial_directory_footer"),
    "services": ("service_links_footer",),
    "area": ("service_area_footer",),
    "contact": ("contact_first_footer", "cta_footer_hybrid", "split_contact_footer", "mobile_action_footer"),
    "statement": ("large_brand_statement_footer", "oversized_wordmark_footer", "workshop_signature_footer"),
    "project": ("project_index_footer",),
    "technical": ("technical_spec_footer",),
    "visual": ("visual_image_footer", "dark_overlay_footer"),
}

FOOTER_COMPONENTS = registry("footer", FOOTER_GROUPS, FOOTER_PROFILES, FOOTER_VARIANTS)
assert len(FOOTER_COMPONENTS) == 20
