"""Strict schema for the only active Site Vitrine design grammar: V3."""

import sys
from pathlib import Path

from pydantic import BaseModel, field_validator

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from generator.v3.grammar import PROFILE_VALUES  # noqa: E402


class DesignGrammarOut(BaseModel):
    """Persisted V3 grammar, validated against the V3 source of truth."""

    art_direction: str
    page_silhouette: str
    header_system: str
    hero_system: str
    typography_system: str
    layout_grid: str
    spacing_rhythm: str
    surface_system: str
    photo_strategy: str
    image_treatment: str
    project_showcase: str
    services_composition: str
    content_density: str
    section_transitions: str
    cta_system: str
    motion_level: str
    spatial_level: str
    decoration_system: str
    footer_system: str
    mobile_personality: str
    ambience: str
    design_engine_version: str
    design_signature: str

    @field_validator(*PROFILE_VALUES.keys())
    @classmethod
    def _axis_valide(cls, value, info):
        allowed = PROFILE_VALUES[info.field_name]
        if value not in allowed:
            raise ValueError(f"{info.field_name} doit etre l'une de : {sorted(allowed)}")
        return value

    @field_validator("design_engine_version")
    @classmethod
    def _version_v3(cls, value):
        if not str(value).startswith("v3."):
            raise ValueError("design_engine_version doit etre une version v3")
        return value


def validate_design_profile(profile: dict) -> dict:
    """Reject every non-V3 profile; historical V2 records are data, not runtime input."""
    return DesignGrammarOut(**profile).model_dump()
