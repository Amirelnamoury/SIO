"""Explicit per-family media policy for the hero section.

V0.1 treated every hero family identically: if no compatible media resolved,
substitute the same geometric ``graphic-fallback`` regardless of what the
family actually promises. That is precisely what the human visual review
flagged as wrong for cinematic/material/residential directions, and it is
what rule H of the V0.2 brief asks to formalize: some families are only
honest with real media, some tolerate an intentionally abstract or diagram
composition, and some (typographic) are a legitimate no-image design on
their own terms and must never show the rectangle at all.

This table is read by :mod:`media_plan` (``HeroMediaResolver``) to decide,
after real media resolution has already been attempted, what a family is
allowed to fall back to. It never inspects a fixture or a component id --
only the family a component was explicitly assigned to in
``data/components/heroes.py``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HeroFamilyPolicy:
    #: "requires_media" -- no real (artisan or stock) photo means the family
    #:   cannot honestly render itself; it must be recomposed into a
    #:   no-image-capable component instead of showing an abstract rectangle.
    #: "tolerant_abstract" -- the family's own visual language already is
    #:   diagrammatic/technical; the geometric fallback is an intentional
    #:   member of that language, not a cop-out.
    #: "no_media_by_design" -- the family never carries a photo; this is not
    #:   a fallback state at all.
    policy: str
    reason: str


# Keyed by ComponentDefinition.family_id ("hero.<profile_name>").
HERO_FAMILY_POLICIES: dict[str, HeroFamilyPolicy] = {
    "hero.photo_cover": HeroFamilyPolicy("requires_media", "full-bleed photo cover has no meaning without a photo"),
    "hero.split_photo": HeroFamilyPolicy("requires_media", "split composition promises a real supporting image"),
    "hero.collage": HeroFamilyPolicy("requires_media", "collage families are defined by their images"),
    "hero.cinematic": HeroFamilyPolicy("requires_media", "cinematic scale and crop require high-impact media"),
    "hero.project": HeroFamilyPolicy("requires_media", "project evidence heroes must show verified artisan work"),
    "hero.material": HeroFamilyPolicy("requires_media", "material heroes are built around a texture/macro photograph"),
    "hero.typographic": HeroFamilyPolicy("no_media_by_design", "typographic heroes are an intentional no-image composition"),
    "hero.conversion": HeroFamilyPolicy("tolerant_abstract", "conversion heroes prioritize the action path over imagery"),
    "hero.technical": HeroFamilyPolicy("tolerant_abstract", "technical heroes may use a diagram instead of a photograph"),
    "hero.spatial": HeroFamilyPolicy("tolerant_abstract", "spatial heroes are explanatory diagrams by definition"),
    "hero.transformation": HeroFamilyPolicy("requires_media", "before/after heroes require verified artisan evidence"),
    "hero.rail": HeroFamilyPolicy("requires_media", "a preview rail with nothing to preview is not a rail"),
}

DEFAULT_HERO_POLICY = HeroFamilyPolicy("tolerant_abstract", "unclassified family; defaulting to the conservative policy")


def hero_policy_for(family_id: str) -> HeroFamilyPolicy:
    return HERO_FAMILY_POLICIES.get(family_id, DEFAULT_HERO_POLICY)


# Families whose profile declares at least one genuinely no-image-capable
# variant (``blueprint_spec.media_spec.supports_no_media``). Used as the
# preferred recomposition landing zone, closest concept first.
NO_IMAGE_CAPABLE_FAMILIES: tuple[str, ...] = (
    "hero.typographic",
    "hero.technical",
    "hero.conversion",
    "hero.spatial",
)
