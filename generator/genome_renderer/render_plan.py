"""RenderPlan: the resolved, renderable plan behind a SiteDNA (rule D).

A ``SiteDNA`` is a theoretical intention -- a set of component ids and system
ids. It says nothing about whether the artisan actually has a photo the hero
can use, whether a section has anything left to say once the hero has said
it, or whether the result still honors the promised art direction. V0.1 had
no artifact that captured that distinction; a screenshot was the only way to
find out, after the fact, that a "cinematic luxury" DNA had quietly rendered
as a plain rectangle.

``build_render_plan`` produces that missing, inspectable middle layer, one
``SectionPlan`` per section that will actually render, built from exactly the
same resolution calls (``RenderContext.resolved_for_rendering``,
``media_for_section``) the HTML renderer itself uses -- so the plan and the
markup cannot silently disagree.
"""

from __future__ import annotations

from dataclasses import dataclass

from generator.design_genome.data.components import ALL_COMPONENTS
from generator.design_genome.models import ComponentDefinition

from .context import RenderContext
from .media_plan import DecisionRecord


@dataclass(frozen=True)
class SectionPlan:
    section: str
    component_id: str
    family: str
    variant_id: str
    resolved_content: dict[str, object]
    resolved_media: tuple[str, ...]
    media_role: str
    media_provenance: str
    fallback_used: bool
    fallback_reason: str
    renderability: str  # "full" | "reduced" | "omitted"
    visual_weight: int
    layout_pattern: str


@dataclass(frozen=True)
class RenderPlan:
    fixture_id: str
    site_archetype: str
    art_direction: str
    page_silhouette: str
    initial_hero_component: str
    resolved_hero_component: str
    decisions: tuple[DecisionRecord, ...]
    sections: tuple[SectionPlan, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "fixture_id": self.fixture_id,
            "site_archetype": self.site_archetype,
            "art_direction": self.art_direction,
            "page_silhouette": self.page_silhouette,
            "initial_hero_component": self.initial_hero_component,
            "resolved_hero_component": self.resolved_hero_component,
            "decisions": [
                {"field": d.field, "initial": d.initial, "resolved": d.resolved, "reason": d.reason}
                for d in self.decisions
            ],
            "sections": [
                {
                    "section": s.section, "component_id": s.component_id, "family": s.family,
                    "variant_id": s.variant_id, "resolved_content": s.resolved_content,
                    "resolved_media": list(s.resolved_media), "media_role": s.media_role,
                    "media_provenance": s.media_provenance, "fallback_used": s.fallback_used,
                    "fallback_reason": s.fallback_reason, "renderability": s.renderability,
                    "visual_weight": s.visual_weight, "layout_pattern": s.layout_pattern,
                }
                for s in self.sections
            ],
        }


def _component(component_id: str | None) -> ComponentDefinition | None:
    return ALL_COMPONENTS.get(component_id or "")


def _media_provenance(media) -> str:
    sources = {item.source_class for item in media}
    if not sources:
        return "none"
    if sources == {"artisan"}:
        return "artisan"
    if sources == {"stock"}:
        return "stock"
    return "mixed"


def build_render_plan(ctx: RenderContext, fixture_id: str) -> RenderPlan:
    resolved = ctx.resolved_for_rendering()
    dna = resolved.dna
    initial_hero = ctx.dna.hero_component
    hero_resolution = resolved.hero_resolution

    sections: list[SectionPlan] = []

    hero_component = hero_resolution.component
    hero_media = hero_resolution.media
    sections.append(SectionPlan(
        section="hero",
        component_id=hero_component.id,
        family=hero_component.family_id,
        variant_id=hero_component.variant_id,
        resolved_content={
            "has_tagline": bool(resolved.plain("tagline")),
            "has_location": bool(resolved.location),
        },
        resolved_media=tuple(item.id for item in hero_media),
        media_role="hero",
        media_provenance=_media_provenance(hero_media),
        # "no_image_intentional" is the family's own honest design, not a
        # fallback from anything -- only abstract_fallback (tolerated
        # rectangle) and recomposed (had to leave the original family) are
        # actual fallbacks. Conflating the three would score a legitimate
        # typographic hero as a media failure, which it is not.
        fallback_used=hero_resolution.mode in {"abstract_fallback", "recomposed"},
        fallback_reason=hero_resolution.reason,
        renderability="full" if hero_resolution.mode in {"media", "no_image_intentional", "recomposed"} else "reduced",
        visual_weight=hero_component.visual_weight,
        layout_pattern=hero_component.blueprint_spec.layout_pattern,
    ))

    for section_name in dna.section_order:
        if section_name in {"header", "footer", "hero"}:
            continue
        component_id = getattr(dna, f"{section_name}_component", None)
        component = _component(component_id)
        if component is None:
            continue
        if section_name in {"gallery", "about"}:
            media = resolved.media_for_section(section_name, component, limit=12 if section_name == "gallery" else 2)
        else:
            media = ()

        if section_name == "gallery":
            renderability = "full" if media else "omitted"
        elif section_name == "services":
            renderability = "full" if resolved.list("services") else "omitted"
        elif section_name == "about":
            narrative = resolved.plain("about") or resolved.plain("tagline")
            facts_present = bool(resolved.location or resolved.plain("assurance_decennale_nom"))
            if not narrative and not facts_present:
                renderability = "omitted"
            elif narrative and resolved.is_duplicate_copy(narrative):
                renderability = "reduced" if facts_present else "omitted"
            else:
                renderability = "full"
        else:
            renderability = "full"
        sections.append(SectionPlan(
            section=section_name,
            component_id=component.id,
            family=component.family_id,
            variant_id=component.variant_id,
            resolved_content={"has_services": bool(resolved.list("services"))} if section_name == "services" else {},
            resolved_media=tuple(item.id for item in media),
            media_role=section_name,
            media_provenance=_media_provenance(media),
            fallback_used=False,
            fallback_reason="",
            renderability=renderability,
            visual_weight=component.visual_weight,
            layout_pattern=component.blueprint_spec.layout_pattern,
        ))

    if "contact" not in dna.section_order and not any(s.section == "contact" for s in sections):
        # Mirrors render_site_genome's own contact fallback exactly: a real
        # slug is a real /pub/{slug}/demande-devis contract even when no
        # contact/form component was assigned. Kept in sync deliberately --
        # see render_contact's identical condition -- so the plan reports
        # what actually renders instead of under-counting it.
        if dna.form_component or resolved.plain("slug"):
            component = _component(dna.contact_component) or _component(dna.form_component)
            sections.append(SectionPlan(
                section="contact",
                component_id=component.id if component else "generic_quote_form",
                family=component.family_id if component else "contact.generic",
                variant_id=component.variant_id if component else "form-only-fallback",
                resolved_content={"form_only": component is None},
                resolved_media=(),
                media_role="contact",
                media_provenance="none",
                fallback_used=component is None,
                fallback_reason="" if component else "no contact/form component assigned; real quote-form fallback used",
                renderability="full",
                visual_weight=component.visual_weight if component else 2,
                layout_pattern=component.blueprint_spec.layout_pattern if component else "stack",
            ))

    decisions = (hero_resolution.decision,) if hero_resolution.decision else ()
    return RenderPlan(
        fixture_id=fixture_id,
        site_archetype=dna.site_archetype,
        art_direction=dna.art_direction,
        page_silhouette=dna.page_silhouette,
        initial_hero_component=initial_hero,
        resolved_hero_component=hero_component.id,
        decisions=decisions,
        sections=tuple(sections),
    )
