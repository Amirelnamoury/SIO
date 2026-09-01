"""Twenty-five CTA blueprints with explicit channel requirements."""

from ._factory import registry
from .profiles import CTA_PROFILES
from .variants import CTA_VARIANTS

CTA_GROUPS = {
    "phone": ("phone_first_cta", "floating_phone_action", "callback_request_cta", "mobile_action_dock_cta"),
    "quote": ("quote_first_cta", "sticky_quote_cta", "footer_conversion_cta", "compact_request_cta", "dual_action_contact_cta"),
    "contact": ("minimal_contact_link", "side_information_cta", "quiet_editorial_cta"),
    "project": ("split_project_cta", "project_brief_cta", "residential_consultation_cta", "site_visit_cta", "project_gallery_cta"),
    "emergency": ("emergency_phone_cta",),
    "email": ("minimal_email_cta",),
    "availability": ("availability_checked_cta", "location_aware_cta"),
    "material": ("service_specific_cta", "material_sample_cta", "technical_diagnostic_cta"),
    "statement": ("monumental_statement_cta",),
}

CTA_COMPONENTS = registry("cta", CTA_GROUPS, CTA_PROFILES, CTA_VARIANTS)
assert len(CTA_COMPONENTS) == 25
