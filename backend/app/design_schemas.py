"""Schema de validation stricte du design_profile (Site Vitrine V2, Lot 1).

Toute valeur exposee par l'API Admin doit appartenir aux registres de
generator/design_registry.py - jamais une chaine magique non verifiee. Ce
schema est deliberement separe de admin_schemas.py : c'est un objet de
lecture seule pour ce lot (voir le brief : pas de configurateur graphique
complet dans le Lot 1), jamais construit depuis une requete utilisateur."""

import sys
from pathlib import Path

from pydantic import BaseModel, TypeAdapter, field_validator
from typing import Union

# Meme bootstrap que app/admin_service.py : le package generator/ vit a la
# racine du depot, hors du package backend/app - jamais suppose deja sur
# sys.path (independant de l'ordre d'import des modules Admin).
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from generator.design_registry import (  # noqa: E402
    ABOUT_VARIANTS,
    CTA_VARIANTS,
    DESIGN_FAMILIES,
    FONT_PAIR_IDS,
    FOOTER_VARIANTS,
    GALLERY_VARIANTS,
    HEADER_VARIANTS,
    HERO_VARIANTS,
    IMAGE_TREATMENTS,
    PALETTE_SLOTS,
    RADIUS_STYLES,
    REVIEWS_VARIANTS,
    SECTION_CATALOG,
    SERVICES_VARIANTS,
    SPACING_STYLES,
)
from generator.v3.grammar import PROFILE_VALUES as V3_PROFILE_VALUES  # noqa: E402


class DesignProfileOut(BaseModel):
    design_family: str
    header_variant: str
    hero_variant: str
    services_variant: str
    gallery_variant: str
    about_variant: str
    reviews_variant: str
    cta_variant: str
    footer_variant: str
    section_order: list[str]
    palette: str
    font_pair: str
    radius_style: str
    spacing_style: str
    image_treatment: str
    design_engine_version: str
    design_signature: str

    @field_validator("design_family")
    @classmethod
    def _family_valide(cls, v):
        if v not in DESIGN_FAMILIES:
            raise ValueError(f"design_family doit etre l'une de : {sorted(DESIGN_FAMILIES)}")
        return v

    @field_validator("header_variant")
    @classmethod
    def _header_valide(cls, v):
        if v not in HEADER_VARIANTS:
            raise ValueError(f"header_variant doit etre l'une de : {sorted(HEADER_VARIANTS)}")
        return v

    @field_validator("hero_variant")
    @classmethod
    def _hero_valide(cls, v):
        if v not in HERO_VARIANTS:
            raise ValueError(f"hero_variant doit etre l'une de : {sorted(HERO_VARIANTS)}")
        return v

    @field_validator("services_variant")
    @classmethod
    def _services_valide(cls, v):
        if v not in SERVICES_VARIANTS:
            raise ValueError(f"services_variant doit etre l'une de : {sorted(SERVICES_VARIANTS)}")
        return v

    @field_validator("gallery_variant")
    @classmethod
    def _gallery_valide(cls, v):
        if v not in GALLERY_VARIANTS:
            raise ValueError(f"gallery_variant doit etre l'une de : {sorted(GALLERY_VARIANTS)}")
        return v

    @field_validator("about_variant")
    @classmethod
    def _about_valide(cls, v):
        if v not in ABOUT_VARIANTS:
            raise ValueError(f"about_variant doit etre l'une de : {sorted(ABOUT_VARIANTS)}")
        return v

    @field_validator("reviews_variant")
    @classmethod
    def _reviews_valide(cls, v):
        if v not in REVIEWS_VARIANTS:
            raise ValueError(f"reviews_variant doit etre l'une de : {sorted(REVIEWS_VARIANTS)}")
        return v

    @field_validator("cta_variant")
    @classmethod
    def _cta_valide(cls, v):
        if v not in CTA_VARIANTS:
            raise ValueError(f"cta_variant doit etre l'une de : {sorted(CTA_VARIANTS)}")
        return v

    @field_validator("footer_variant")
    @classmethod
    def _footer_valide(cls, v):
        if v not in FOOTER_VARIANTS:
            raise ValueError(f"footer_variant doit etre l'une de : {sorted(FOOTER_VARIANTS)}")
        return v

    @field_validator("section_order")
    @classmethod
    def _section_order_valide(cls, v):
        if not v or v[0] != "hero":
            raise ValueError("section_order doit commencer par 'hero'")
        inconnues = [s for s in v if s not in SECTION_CATALOG]
        if inconnues:
            raise ValueError(f"section_order contient des sections inconnues : {inconnues}")
        return v

    @field_validator("palette")
    @classmethod
    def _palette_valide(cls, v):
        if v not in PALETTE_SLOTS:
            raise ValueError(f"palette doit etre l'une de : {sorted(PALETTE_SLOTS)}")
        return v

    @field_validator("font_pair")
    @classmethod
    def _font_pair_valide(cls, v):
        if v not in FONT_PAIR_IDS:
            raise ValueError(f"font_pair doit etre l'une de : {sorted(FONT_PAIR_IDS)}")
        return v

    @field_validator("radius_style")
    @classmethod
    def _radius_valide(cls, v):
        if v not in RADIUS_STYLES:
            raise ValueError(f"radius_style doit etre l'une de : {sorted(RADIUS_STYLES)}")
        return v

    @field_validator("spacing_style")
    @classmethod
    def _spacing_valide(cls, v):
        if v not in SPACING_STYLES:
            raise ValueError(f"spacing_style doit etre l'une de : {sorted(SPACING_STYLES)}")
        return v

    @field_validator("image_treatment")
    @classmethod
    def _image_treatment_valide(cls, v):
        if v not in IMAGE_TREATMENTS:
            raise ValueError(f"image_treatment doit etre l'une de : {sorted(IMAGE_TREATMENTS)}")
        return v


class DesignGrammarOut(BaseModel):
    """Persisted V3 grammar. Every axis is registry-backed and immutable at render time."""

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

    @field_validator(*V3_PROFILE_VALUES.keys())
    @classmethod
    def _axis_valide(cls, value, info):
        allowed = V3_PROFILE_VALUES[info.field_name]
        if value not in allowed:
            raise ValueError(f"{info.field_name} doit etre l'une de : {sorted(allowed)}")
        return value

    @field_validator("design_engine_version")
    @classmethod
    def _version_v3(cls, value):
        if not str(value).startswith("v3."):
            raise ValueError("design_engine_version doit etre une version v3")
        return value


AnyDesignProfileOut = Union[DesignProfileOut, DesignGrammarOut]
_DESIGN_PROFILE_ADAPTER = TypeAdapter(AnyDesignProfileOut)


def validate_design_profile(profile: dict) -> dict:
    """Validate by explicit engine version, avoiding permissive union coercion."""
    model = DesignGrammarOut if str(profile.get("design_engine_version") or "").startswith("v3.") else DesignProfileOut
    return model(**profile).model_dump()
