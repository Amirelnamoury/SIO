"""Contact and form blueprints with explicit conversion semantics."""

from ._factory import registry
from .profiles import CONTACT_PROFILES, FORM_PROFILES

CONTACT_GROUPS = {
    "phone": ("phone_first_contact", "floating_contact_action", "mobile_action_contact"),
    "quote": ("quote_first_contact", "compact_request_contact", "footer_contact_conversion"),
    "minimal": ("minimal_contact", "side_information_contact"),
    "split": ("split_form_contact", "residential_project_contact"),
    "panel": ("sticky_contact_panel", "dark_overlay_contact"),
    "project": ("project_brief_contact",),
    "emergency": ("emergency_contact",),
    "local": ("local_map_contact", "service_area_contact", "workshop_visit_contact"),
    "technical": ("technical_diagnostic_contact",),
    "editorial": ("editorial_contact_statement",),
    "channels": ("multi_channel_contact",),
}

FORM_GROUPS = {
    "single": ("single_column_quote_form", "contact_details_form", "site_visit_request_form", "material_consultation_form", "inline_footer_form", "full_page_enquiry_form"),
    "split": ("split_project_form", "residential_scope_form"),
    "compact": ("compact_callback_form", "emergency_minimal_form", "accordion_mobile_form"),
    "multi_step": ("multi_step_project_brief", "service_selector_form"),
    "technical": ("technical_diagnostic_form",),
    "accessible": ("accessible_minimal_form",),
}

CONTACT_COMPONENTS = registry("contact", CONTACT_GROUPS, CONTACT_PROFILES)
FORM_COMPONENTS = registry("form", FORM_GROUPS, FORM_PROFILES)
assert len(CONTACT_COMPONENTS) == 20
assert len(FORM_COMPONENTS) == 15
