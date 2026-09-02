"""RenderPlan: the single, authoritative resolution pass (V0.2.1).

V0.2 introduced ``RenderPlan`` as a *reporting* artifact built alongside the
renderer, both reading the same underlying methods. That was not enough: one
piece of state -- which literal copy has already been shown (``used_copy``,
for the hero/about duplication check) -- evolved *during* the render loop
itself (in ``render_site_genome``/``render_about``), one section at a time,
and ``build_render_plan`` never replayed that same evolution. The plan and
the renderer therefore each made their own independent judgement about
whether "about" should be full or reduced, and the two could disagree (they
did, on site-11: plan said ``full``, HTML said ``about--micro``).

V0.2.1's fix is structural, not a patch to one section: every decision that
can affect what actually renders -- media resolution, hero recomposition,
content-usage/duplication, per-section renderability, fallbacks, the
contact fallback -- now happens exactly once, here, walking sections in
their real render order and threading one explicit state object
(``_PlanState``) through them. The result, ``RenderPlan``, is then handed to
the renderer, which does not re-run any of this logic -- it materializes
markup from the plan's decisions (see ``renderer.render_site_genome``).
``VisualCompletenessReport`` and ``CoherenceReport`` both consume this same
finished plan, not a second resolution path.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from generator.design_genome.data.components import ALL_COMPONENTS
from generator.design_genome.models import ComponentDefinition, SiteDNA

from .coherence import CoherenceReport, build_coherence_report
from .context import RenderContext, RenderMedia
from .family_requirements import HERO_MEDIA_DISPLAY_LIMIT_BY_FAMILY, NO_MEDIA_CONSUMED_HERO_IDS
from .media_plan import DecisionRecord, HeroMediaResolver, HeroResolution, allocate_media


@dataclass(frozen=True)
class SectionPlan:
    section: str
    component_id: str
    family: str
    variant_id: str
    renderability: str  # "full" | "reduced" | "omitted"
    # Hero: "media" | "no_image_intentional" | "abstract_fallback" | "recomposed"
    # About: "narrative" | "fact_strip" | "none"
    # Everything else: "standard"
    resolved_mode: str
    resolved_content: dict[str, object]
    resolved_media: tuple[str, ...]
    content_usage: tuple[str, ...]  # literal copy this section consumes, feeding later duplication checks
    media_role: str
    media_provenance: str
    fallback_used: bool
    fallback_reason: str
    visual_weight: int
    layout_pattern: str
    coherence_status: str = "n/a"
    coherence_reasons: tuple[str, ...] = ()


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
    coherence: CoherenceReport

    @property
    def rendered_sections(self) -> tuple[SectionPlan, ...]:
        return tuple(s for s in self.sections if s.renderability != "omitted")

    def section(self, name: str) -> SectionPlan | None:
        return next((s for s in self.sections if s.section == name), None)

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
                    "variant_id": s.variant_id, "renderability": s.renderability,
                    "resolved_mode": s.resolved_mode, "resolved_content": s.resolved_content,
                    "resolved_media": list(s.resolved_media), "content_usage": list(s.content_usage),
                    "media_role": s.media_role, "media_provenance": s.media_provenance,
                    "fallback_used": s.fallback_used, "fallback_reason": s.fallback_reason,
                    "visual_weight": s.visual_weight, "layout_pattern": s.layout_pattern,
                    "coherence_status": s.coherence_status, "coherence_reasons": list(s.coherence_reasons),
                }
                for s in self.sections
            ],
            "coherence": self.coherence.to_dict(),
        }


def _component(component_id: str | None) -> ComponentDefinition | None:
    return ALL_COMPONENTS.get(component_id or "")


def _media_provenance(media: tuple[RenderMedia, ...]) -> str:
    sources = {item.source_class for item in media}
    if not sources:
        return "none"
    if sources == {"artisan"}:
        return "artisan"
    if sources == {"stock"}:
        return "stock"
    return "mixed"


@dataclass
class _PlanState:
    """Mutable scratch state threaded through one, and only one, walk of the
    sections -- this is what V0.2 was missing. Nothing outside this module
    mutates it, and it is discarded once the plan is built.
    """
    used_copy: set[str] = field(default_factory=set)

    def is_duplicate(self, text: str) -> bool:
        text = text.strip()
        return bool(text) and text in self.used_copy

    def consume(self, *texts: str) -> tuple[str, ...]:
        consumed = tuple(t.strip() for t in texts if t and t.strip())
        self.used_copy.update(consumed)
        return consumed


def _resolve_hero(ctx: RenderContext, dna: SiteDNA, state: _PlanState) -> tuple[SectionPlan, HeroResolution, SiteDNA]:
    hero_resolution = HeroMediaResolver.resolve(ctx, dna)
    if hero_resolution.decision is not None:
        dna = replace(dna, hero_component=hero_resolution.decision.resolved)
    component = hero_resolution.component
    tagline = ctx.plain("tagline")
    content_usage = state.consume(tagline) if tagline else ()

    # A handful of bespoke hero realizations (families.py) materialize as a
    # diagram/composition and never place a resolved photo in the DOM even
    # when compatible media exists (rule: technical_nodes_network -- real
    # services become nodes, not a background photo). The plan must report
    # what actually renders, not what was merely available -- see
    # family_requirements.NO_MEDIA_CONSUMED_HERO_IDS.
    consumes_media = component.id not in NO_MEDIA_CONSUMED_HERO_IDS
    effective_media = hero_resolution.media if consumes_media else ()
    display_limit = HERO_MEDIA_DISPLAY_LIMIT_BY_FAMILY.get(component.family_id)
    if display_limit is not None:
        effective_media = effective_media[:display_limit]
    # "diagram" is a distinct, honest mode: HeroMediaResolver may still say
    # "media" (compatible media genuinely exists), but the bespoke
    # realization for this component never places it in the DOM -- reporting
    # "media" here would make VisualCompletenessReport's empty-slot check
    # see a real photo slot where none was ever promised.
    resolved_mode = "diagram" if not consumes_media else hero_resolution.mode

    plan = SectionPlan(
        section="hero",
        component_id=component.id,
        family=component.family_id,
        variant_id=component.variant_id,
        renderability="reduced" if hero_resolution.mode == "abstract_fallback" else "full",
        resolved_mode=resolved_mode,
        resolved_content={"has_tagline": bool(tagline), "has_location": bool(ctx.location)},
        resolved_media=tuple(item.id for item in effective_media),
        content_usage=content_usage,
        media_role="hero",
        media_provenance=_media_provenance(effective_media),
        # no_image_intentional is the family's own honest design, not a
        # fallback from anything -- see family_requirements.py.
        fallback_used=hero_resolution.mode in {"abstract_fallback", "recomposed"},
        fallback_reason=hero_resolution.reason,
        visual_weight=component.visual_weight,
        layout_pattern=component.blueprint_spec.layout_pattern,
    )
    return plan, hero_resolution, dna


def _resolve_about(ctx: RenderContext, component: ComponentDefinition, media: tuple[RenderMedia, ...], state: _PlanState) -> SectionPlan:
    narrative = ctx.plain("about") or ctx.plain("tagline")
    facts_present = bool(ctx.location or ctx.plain("assurance_decennale_nom"))
    media_relationship = component.blueprint_spec.media_spec.get("relationship")
    resolved_media = () if media_relationship == "none" else media

    if not narrative and not facts_present:
        renderability, mode, content_usage = "omitted", "none", ()
    elif narrative and state.is_duplicate(narrative):
        # The only "narrative" available is a verbatim repeat of copy a
        # higher-priority section (the hero) already showed -- a second
        # identical paragraph adds nothing (rule Z/AA). This is decided
        # HERE, once, against the state as it stands at this point in the
        # real render order -- not re-derived later by the renderer.
        if facts_present:
            renderability, mode, content_usage = "reduced", "fact_strip", ()
        else:
            renderability, mode, content_usage = "omitted", "none", ()
    else:
        renderability, mode = "full", "narrative"
        content_usage = state.consume(narrative) if narrative else ()

    return SectionPlan(
        section="about",
        component_id=component.id,
        family=component.family_id,
        variant_id=component.variant_id,
        renderability=renderability,
        resolved_mode=mode,
        resolved_content={"has_narrative": bool(narrative), "has_facts": facts_present, "narrative_is_duplicate": bool(narrative) and mode != "narrative" and bool(narrative)},
        # The fact-strip treatment (rule Z/AA reduction) never places an
        # image -- see sections.render_about's "fact_strip" branch -- so the
        # plan must not claim media only "full" narrative actually uses.
        resolved_media=tuple(item.id for item in resolved_media) if mode == "narrative" else (),
        content_usage=content_usage,
        media_role="about",
        media_provenance=_media_provenance(resolved_media) if mode == "narrative" else "none",
        fallback_used=False,
        fallback_reason="",
        visual_weight=component.visual_weight,
        layout_pattern=component.blueprint_spec.layout_pattern,
    )


def _resolve_gallery(ctx: RenderContext, component: ComponentDefinition, media: tuple[RenderMedia, ...]) -> SectionPlan:
    renderability = "full" if media else "omitted"
    return SectionPlan(
        section="gallery", component_id=component.id, family=component.family_id, variant_id=component.variant_id,
        renderability=renderability, resolved_mode="standard",
        resolved_content={"item_count": len(media)},
        resolved_media=tuple(item.id for item in media), content_usage=(),
        media_role="gallery", media_provenance=_media_provenance(media) if media else "none",
        fallback_used=False, fallback_reason="" if media else "no compatible media left in the allocation pool",
        visual_weight=component.visual_weight, layout_pattern=component.blueprint_spec.layout_pattern,
    )


def _resolve_services(ctx: RenderContext, component: ComponentDefinition) -> SectionPlan:
    services = ctx.list("services")
    renderability = "full" if services else "omitted"
    return SectionPlan(
        section="services", component_id=component.id, family=component.family_id, variant_id=component.variant_id,
        renderability=renderability, resolved_mode="standard",
        resolved_content={"service_count": len(services)},
        resolved_media=(), content_usage=(),
        media_role="services", media_provenance="none",
        fallback_used=False, fallback_reason="" if services else "no services data available",
        visual_weight=component.visual_weight, layout_pattern=component.blueprint_spec.layout_pattern,
    )


def _resolve_trust(ctx: RenderContext, component: ComponentDefinition, trust_items_fn) -> SectionPlan:
    items = trust_items_fn(ctx, component)
    renderability = "full" if items else "omitted"
    return SectionPlan(
        section="trust", component_id=component.id, family=component.family_id, variant_id=component.variant_id,
        renderability=renderability, resolved_mode="process" if component.profile == "process" else "standard",
        resolved_content={"item_count": len(items), "profile": component.profile},
        resolved_media=(), content_usage=(),
        media_role="trust", media_provenance="none",
        fallback_used=False, fallback_reason="" if items else "no matching verified/process facts available",
        visual_weight=component.visual_weight, layout_pattern=component.blueprint_spec.layout_pattern,
    )


def _resolve_cta(ctx: RenderContext, component: ComponentDefinition, has_actions: bool) -> SectionPlan:
    renderability = "full" if has_actions else "omitted"
    return SectionPlan(
        section="cta", component_id=component.id, family=component.family_id, variant_id=component.variant_id,
        renderability=renderability, resolved_mode="standard",
        resolved_content={"has_actions": has_actions},
        resolved_media=(), content_usage=(),
        media_role="cta", media_provenance="none",
        fallback_used=False, fallback_reason="" if has_actions else "no phone/email/quote action available",
        visual_weight=component.visual_weight, layout_pattern=component.blueprint_spec.layout_pattern,
    )


def _resolve_contact(ctx: RenderContext, component: ComponentDefinition | None, has_channel_or_form: bool) -> SectionPlan | None:
    if component is not None:
        renderability = "full" if has_channel_or_form else "omitted"
        return SectionPlan(
            section="contact", component_id=component.id, family=component.family_id, variant_id=component.variant_id,
            renderability=renderability, resolved_mode="standard",
            resolved_content={"form_only": False},
            resolved_media=(), content_usage=(),
            media_role="contact", media_provenance="none",
            fallback_used=False, fallback_reason="" if has_channel_or_form else "no channels and no form available",
            visual_weight=component.visual_weight, layout_pattern=component.blueprint_spec.layout_pattern,
        )
    # No contact/form component was assigned by the Design Genome (typically
    # no verified phone/email yet). A real slug is still a real
    # /pub/{slug}/demande-devis contract (rule AE) -- see sections.py.
    if not ctx.plain("slug"):
        return None
    return SectionPlan(
        section="contact", component_id="generic_quote_form", family="contact.generic", variant_id="form-only-fallback",
        renderability="full", resolved_mode="form_only",
        resolved_content={"form_only": True},
        resolved_media=(), content_usage=(),
        media_role="contact", media_provenance="none",
        fallback_used=True, fallback_reason="no contact/form component assigned; real quote-form fallback used",
        visual_weight=2, layout_pattern="stack",
    )


def build_render_plan(ctx: RenderContext, fixture_id: str | None = None) -> RenderPlan:
    from .sections import _actions_available, _trust_items  # local import: avoids a module cycle

    fixture_id = fixture_id if fixture_id is not None else ctx.plain("slug")
    state = _PlanState()
    initial_hero = ctx.dna.hero_component

    hero_plan, hero_resolution, dna = _resolve_hero(ctx, ctx.dna, state)
    media_plan = allocate_media(ctx, dna, hero_resolution, frozenset(hero_plan.resolved_media))

    sections: list[SectionPlan] = [hero_plan]
    names = {"hero"}

    for section_name in dna.section_order:
        if section_name in {"header", "footer", "hero"} or section_name in names:
            continue
        component = _component(getattr(dna, f"{section_name}_component", None))
        if component is None:
            continue

        if section_name == "gallery":
            media = ctx.media_for(component, limit=12, pool=media_plan.pool_for("gallery", ctx.media))
            section_plan = _resolve_gallery(ctx, component, media)
        elif section_name == "services":
            section_plan = _resolve_services(ctx, component)
        elif section_name == "about":
            media = ctx.media_for(component, limit=2, pool=media_plan.pool_for("about", ctx.media))
            section_plan = _resolve_about(ctx, component, media, state)
        elif section_name == "trust":
            section_plan = _resolve_trust(ctx, component, _trust_items)
        elif section_name == "cta":
            section_plan = _resolve_cta(ctx, component, _actions_available(ctx))
        elif section_name == "contact":
            section_plan = _resolve_contact(ctx, component, _actions_available(ctx) or bool(ctx.phone_href or ctx.plain("email") or ctx.plain("adresse")))
        else:
            continue

        sections.append(section_plan)
        names.add(section_name)

    if "contact" not in names:
        fallback = _resolve_contact(ctx, _component(dna.contact_component) or _component(dna.form_component), True)
        if fallback is not None:
            sections.append(fallback)
            names.add("contact")

    # --- Coherence (rule 25: evaluate the FINAL resolved plan, not raw DNA) ---
    resolved_components = tuple(
        (s.section, _component(s.component_id))
        for s in sections
        if s.renderability != "omitted" and _component(s.component_id) is not None
    )
    coherence = build_coherence_report(fixture_id, dna.site_archetype, dna.art_direction, dna.page_silhouette, resolved_components)
    coherence_by_section = {c.section: c for c in coherence.sections}
    sections = [
        replace(s, coherence_status=coherence_by_section[s.section].status, coherence_reasons=coherence_by_section[s.section].reasons)
        if s.section in coherence_by_section else s
        for s in sections
    ]

    decisions = (hero_resolution.decision,) if hero_resolution.decision else ()
    return RenderPlan(
        fixture_id=fixture_id,
        site_archetype=dna.site_archetype,
        art_direction=dna.art_direction,
        page_silhouette=dna.page_silhouette,
        initial_hero_component=initial_hero,
        resolved_hero_component=hero_plan.component_id,
        decisions=decisions,
        sections=tuple(sections),
        coherence=coherence,
    )
