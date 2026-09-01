"""Twenty contact systems and fifteen form-layout blueprints."""

from ._factory import registry

CONTACT_IDS = (
    "phone_first_contact", "quote_first_contact", "minimal_contact", "split_form_contact",
    "sticky_contact_panel", "floating_contact_action", "footer_contact_conversion", "side_information_contact",
    "compact_request_contact", "project_brief_contact", "emergency_contact", "residential_project_contact",
    "local_map_contact", "service_area_contact", "workshop_visit_contact", "technical_diagnostic_contact",
    "editorial_contact_statement", "dark_overlay_contact", "multi_channel_contact", "mobile_action_contact",
)

FORM_IDS = (
    "single_column_quote_form", "split_project_form", "compact_callback_form", "multi_step_project_brief",
    "service_selector_form", "emergency_minimal_form", "residential_scope_form", "technical_diagnostic_form",
    "contact_details_form", "site_visit_request_form", "material_consultation_form", "accordion_mobile_form",
    "inline_footer_form", "full_page_enquiry_form", "accessible_minimal_form",
)

CONTACT_COMPONENTS = registry("contact", CONTACT_IDS)
FORM_COMPONENTS = registry("form", FORM_IDS)
assert len(CONTACT_COMPONENTS) == 20
assert len(FORM_COMPONENTS) == 15
