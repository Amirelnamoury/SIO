"""Twenty proof blueprints; every factual variant declares required data."""

from ._factory import registry

TRUST_IDS = (
    "verified_insurance_line", "verified_certification_badges", "verified_review_excerpt",
    "verified_review_summary", "verified_project_statistics", "verified_client_statistics",
    "verified_team_credentials", "verified_service_area_map", "verified_partner_directory",
    "verified_brand_authorizations", "verified_awards_ledger", "verified_guarantee_statement",
    "verified_opening_hours", "verified_emergency_availability", "verified_response_delay",
    "documented_process_proof", "artisan_project_evidence", "before_after_evidence",
    "combined_verified_fact_strip", "minimal_verified_fact_index",
)

TRUST_COMPONENTS = registry("trust", TRUST_IDS)
assert len(TRUST_COMPONENTS) == 20
