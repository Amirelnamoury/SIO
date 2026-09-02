"""Page-level media allocation and hero media resolution (V0.2).

V0.1 let every section independently ask the full media pool "what can I
use?" with no page-level view. Nothing was wrong with that in principle, but
it meant no section knew whether a *more important* section (the hero) had
already claimed the only good photo, and the hero's own resolution had a
correctness bug (see ``context.media_for``) that made it fall back to the
generic graphic rectangle even when compatible stock media existed.

This module adds the missing page-level pass:

* ``HeroMediaResolver`` resolves the hero first, with the full pool, and
  decides -- from the family's declared policy, not from a fixture id --
  whether a missing photo should recompose the hero into a no-image-capable
  component instead of drawing an abstract rectangle.
* ``allocate_media`` then gives every other rendered section a reserved slice
  of what is left, so a good image already used by the hero is not also
  handed to about/gallery, and a section is never starved while an unrelated
  section holds an image it does not need.

Nothing here invents media or fixture content. It only changes which already
selected, already truth-safe media item ends up backing which section.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from generator.design_genome.data.components import ALL_COMPONENTS
from generator.design_genome.models import ComponentDefinition, SiteDNA

from .family_requirements import NO_IMAGE_CAPABLE_FAMILIES, hero_policy_for

if TYPE_CHECKING:
    from .context import RenderContext, RenderMedia


SECTION_PRIORITY: tuple[str, ...] = ("hero", "gallery", "about")


@dataclass(frozen=True)
class DecisionRecord:
    """One documented, non-magic recomposition decision (rule BD)."""

    field: str
    initial: str
    resolved: str
    reason: str


@dataclass(frozen=True)
class HeroResolution:
    media: tuple["RenderMedia", ...]
    mode: str  # "media" | "no_image_intentional" | "abstract_fallback" | "recomposed"
    reason: str
    component: ComponentDefinition
    decision: DecisionRecord | None = None


def _component_for(component_id: str | None) -> ComponentDefinition | None:
    return ALL_COMPONENTS.get(component_id or "")


def _no_image_candidates(dna: SiteDNA) -> tuple[ComponentDefinition, ...]:
    values = [
        component
        for component in ALL_COMPONENTS.values()
        if component.category == "hero" and component.family_id in NO_IMAGE_CAPABLE_FAMILIES
        and component.blueprint_spec.media_spec.get("supports_no_media")
    ]
    return tuple(sorted(values, key=lambda item: item.id))


def _pick_recomposition_target(original: ComponentDefinition, dna: SiteDNA) -> ComponentDefinition | None:
    """Choose a no-image hero honestly compatible with the resolved direction.

    Preference order: a candidate whose declared ``compatible_directions``
    includes this site's actual art direction, then one whose
    ``compatible_archetypes`` matches, then the most generic no-image
    candidate (deterministic, alphabetical -- never random). This reuses
    compatibility metadata the Design Genome already maintains; it does not
    add a new scoring model.
    """
    candidates = _no_image_candidates(dna)
    if not candidates:
        return None
    by_direction = [item for item in candidates if dna.art_direction in item.compatible_directions]
    if by_direction:
        return by_direction[0]
    by_archetype = [item for item in candidates if dna.site_archetype in item.compatible_archetypes]
    if by_archetype:
        return by_archetype[0]
    generic = [item for item in candidates if item.id == "no_image_typographic_signal"]
    return generic[0] if generic else candidates[0]


class HeroMediaResolver:
    """Resolves the hero's media (and, if needed, its component) once."""

    @staticmethod
    def resolve(ctx: "RenderContext", dna: SiteDNA) -> HeroResolution:
        component = _component_for(dna.hero_component)
        if component is None:
            return HeroResolution((), "no_image_intentional", "no hero component assigned", component)  # type: ignore[arg-type]

        declared_max = component.blueprint_spec.media_spec.get("media_count_max", 1)
        policy = hero_policy_for(component.family_id)

        if declared_max == 0 or policy.policy == "no_media_by_design":
            return HeroResolution((), "no_image_intentional", policy.reason, component)

        media = ctx.media_for(component, limit=declared_max)
        if media:
            return HeroResolution(media, "media", "compatible media resolved from available inventory", component)

        if policy.policy == "tolerant_abstract":
            return HeroResolution((), "abstract_fallback", policy.reason, component)

        # policy == "requires_media" and nothing compatible exists anywhere
        # in the inventory: recompose rather than fake a photo or show an
        # abstract rectangle the family never promised (rule H/K).
        target = _pick_recomposition_target(component, dna)
        if target is None:
            # No no-image component exists at all (should not happen given
            # the current catalog) -- fall back to the abstract rectangle as
            # the least dishonest remaining option, and say so plainly.
            return HeroResolution(
                (), "abstract_fallback",
                f"no compatible media and no no-image variant available for {component.family_id}",
                component,
            )
        decision = DecisionRecord(
            field="hero_component",
            initial=component.id,
            resolved=target.id,
            reason=f"no compatible media for {component.family_id} ({policy.reason}); "
                   f"recomposed to a no-image variant compatible with {dna.art_direction}",
        )
        return HeroResolution((), "recomposed", decision.reason, target, decision)


@dataclass(frozen=True)
class MediaAllocationPlan:
    """Section -> reserved media ids, decided once for the whole page."""

    assignments: dict[str, tuple[str, ...]] = field(default_factory=dict)
    reasons: dict[str, str] = field(default_factory=dict)

    def pool_for(self, section: str, media: tuple["RenderMedia", ...]) -> tuple["RenderMedia", ...]:
        reserved = self.assignments.get(section)
        if reserved is None:
            return media
        allowed_ids = set(reserved)
        return tuple(item for item in media if item.id in allowed_ids)


def allocate_media(
    ctx: "RenderContext",
    dna: SiteDNA,
    hero_resolution: HeroResolution,
) -> MediaAllocationPlan:
    """Reserve media per section, hero first, so nothing under-serves it.

    Only the hero is resolved before this plan exists (it must always get
    first pick of the whole pool -- rule G). Gallery and about then draw from
    whatever remains, in that priority order, so a page never ends up with a
    full gallery and an empty hero, and the same photograph is not silently
    reused as if it were three different pieces of evidence.
    """
    remaining = list(ctx.media)
    assignments: dict[str, tuple[str, ...]] = {}
    reasons: dict[str, str] = {}

    used_ids = {item.id for item in hero_resolution.media}
    remaining = [item for item in remaining if item.id not in used_ids]
    assignments["hero"] = tuple(used_ids)
    reasons["hero"] = hero_resolution.reason

    for section, component_id in (("gallery", dna.gallery_component), ("about", dna.about_component)):
        component = _component_for(component_id)
        if component is None:
            continue
        limit = 12 if section == "gallery" else 2
        candidates = ctx.media_for(component, limit=limit, pool=tuple(remaining))
        assignments[section] = tuple(item.id for item in candidates)
        reasons[section] = (
            "reserved from remaining pool after higher-priority sections"
            if candidates else "no compatible media left in the pool"
        )
        claimed = {item.id for item in candidates}
        remaining = [item for item in remaining if item.id not in claimed]

    return MediaAllocationPlan(assignments=assignments, reasons=reasons)
