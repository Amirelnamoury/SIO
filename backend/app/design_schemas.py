"""Schema de validation stricte du design_profile (Site Vitrine V2, Lot 1).

Toute valeur exposee par l'API Admin doit appartenir aux registres de
generator/design_registry.py - jamais une chaine magique non verifiee. Ce
schema est deliberement separe de admin_schemas.py : c'est un objet de
lecture seule pour ce lot (voir le brief : pas de configurateur graphique
complet dans le Lot 1), jamais construit depuis une requete utilisateur."""

import sys
from pathlib import Path

from pydantic import BaseModel, field_validator

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
