"""Twenty trust sections, each tied to explicit evidence."""

from ._factory import registry
from .profiles import TRUST_PROFILES

TRUST_GROUPS = {
    "insurance": ("verified_insurance_line",),
    "certifications": ("verified_certification_badges",),
    "reviews": ("verified_review_excerpt", "verified_review_summary"),
    "statistics": ("verified_project_statistics", "verified_client_statistics"),
    "team": ("verified_team_credentials",),
    "area": ("verified_service_area_map",),
    "partners": ("verified_partner_directory",),
    "brands": ("verified_brand_authorizations",),
    "awards": ("verified_awards_ledger",),
    "guarantee": ("verified_guarantee_statement",),
    "hours": ("verified_opening_hours",),
    "emergency": ("verified_emergency_availability",),
    "response": ("verified_response_delay",),
    "process": ("documented_process_proof",),
    "project": ("artisan_project_evidence",),
    "before_after": ("before_after_evidence",),
    "facts": ("combined_verified_fact_strip", "minimal_verified_fact_index"),
}

TRUST_COMPONENTS = registry("trust", TRUST_GROUPS, TRUST_PROFILES)
assert len(TRUST_COMPONENTS) == 20
