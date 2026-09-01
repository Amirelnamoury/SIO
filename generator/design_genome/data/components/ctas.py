"""Twenty-five conversion prompts with different interaction priorities."""

from ._factory import registry

CTA_IDS = (
    "phone_first_cta", "quote_first_cta", "minimal_contact_link", "split_project_cta", "sticky_quote_cta",
    "floating_phone_action", "footer_conversion_cta", "side_information_cta", "compact_request_cta",
    "project_brief_cta", "emergency_phone_cta", "residential_consultation_cta", "quiet_editorial_cta",
    "dual_action_contact_cta", "service_specific_cta", "location_aware_cta", "callback_request_cta",
    "material_sample_cta", "site_visit_cta", "technical_diagnostic_cta", "project_gallery_cta",
    "availability_checked_cta", "minimal_email_cta", "monumental_statement_cta", "mobile_action_dock_cta",
)

CTA_COMPONENTS = registry("cta", CTA_IDS)
assert len(CTA_COMPONENTS) == 25
