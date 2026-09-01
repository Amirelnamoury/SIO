"""Twenty about sections with explicit narrative and evidence policies."""

from ._factory import registry
from .profiles import ABOUT_PROFILES
from .variants import ABOUT_VARIANTS

ABOUT_GROUPS = {
    "identity": ("simple_business_identity", "residential_approach_about", "studio_statement_about"),
    "founder": ("founder_story_split", "framed_quote_about"),
    "documentary": ("workshop_documentary_about", "process_manifesto", "design_build_method", "people_and_tools_about"),
    "material": ("material_philosophy", "craft_values_index"),
    "local": ("local_commitment_about", "service_area_story"),
    "team": ("team_portrait_about",),
    "heritage": ("heritage_timeline_about",),
    "technical": ("technical_expertise_about",),
    "project": ("project_context_about",),
    "minimal": ("quiet_editorial_about", "brutalist_factless_about", "mobile_compact_about"),
}

ABOUT_COMPONENTS = registry("about", ABOUT_GROUPS, ABOUT_PROFILES, ABOUT_VARIANTS)
assert len(ABOUT_COMPONENTS) == 20
