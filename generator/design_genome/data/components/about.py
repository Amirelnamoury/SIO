"""Twenty about/story blueprints."""

from ._factory import registry

ABOUT_IDS = (
    "simple_business_identity", "founder_story_split", "workshop_documentary_about", "material_philosophy",
    "process_manifesto", "local_commitment_about", "team_portrait_about", "heritage_timeline_about",
    "design_build_method", "quiet_editorial_about", "technical_expertise_about", "residential_approach_about",
    "craft_values_index", "project_context_about", "service_area_story", "studio_statement_about",
    "people_and_tools_about", "framed_quote_about", "brutalist_factless_about", "mobile_compact_about",
)

ABOUT_COMPONENTS = registry("about", ABOUT_IDS)
assert len(ABOUT_COMPONENTS) == 20
