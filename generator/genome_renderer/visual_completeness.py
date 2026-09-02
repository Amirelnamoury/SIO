"""VisualCompletenessReport: a legible, non-aesthetic structural audit.

This deliberately does not -- and must not -- output a beauty score. Every
dimension is a checkable structural fact about the *final resolved*
``RenderPlan`` (rule 37 of the V0.2.1 brief: no parallel resolution here),
with a plain-language reason attached whenever a dimension is below its
threshold. The aesthetic verdict stays entirely with the human review (rule
AQ/BJ, and rule 11/17 of V0.2.1: still not a beauty/premium/sellable score).

V0.2.1 change: ``empty_slot_risk`` and ``mobile_readiness`` were flagged as
too easily 1.0 in V0.2 (the first inferred from "the renderer is supposed
to..." rather than inspecting the plan; the second outright constant). Both
now inspect the plan's actual sections and component metadata and can
genuinely score below 1.0 -- see each function's docstring for exactly what
it checks. ``art_direction_fidelity`` now also incorporates
``RenderPlan.coherence`` (rule 22): a hero with real media is no longer
sufficient on its own for a perfect score if the resolved plan is globally
incoherent (site-11's own case).
"""

from __future__ import annotations

from dataclasses import dataclass

from generator.design_genome.data.components import ALL_COMPONENTS

from .render_plan import RenderPlan


@dataclass(frozen=True)
class CompletenessDimension:
    score: float  # 0..1, a structural ratio -- never a beauty judgement
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class VisualCompletenessReport:
    fixture_id: str
    hero_readiness: CompletenessDimension
    media_readiness: CompletenessDimension
    content_density: CompletenessDimension
    commercial_completeness: CompletenessDimension
    narrative_completeness: CompletenessDimension
    section_balance: CompletenessDimension
    empty_slot_risk: CompletenessDimension
    art_direction_fidelity: CompletenessDimension
    visual_rhythm: CompletenessDimension
    mobile_readiness: CompletenessDimension

    def to_dict(self) -> dict[str, object]:
        return {
            "fixture_id": self.fixture_id,
            **{
                name: {"score": dim.score, "reasons": list(dim.reasons)}
                for name, dim in (
                    ("hero_readiness", self.hero_readiness),
                    ("media_readiness", self.media_readiness),
                    ("content_density", self.content_density),
                    ("commercial_completeness", self.commercial_completeness),
                    ("narrative_completeness", self.narrative_completeness),
                    ("section_balance", self.section_balance),
                    ("empty_slot_risk", self.empty_slot_risk),
                    ("art_direction_fidelity", self.art_direction_fidelity),
                    ("visual_rhythm", self.visual_rhythm),
                    ("mobile_readiness", self.mobile_readiness),
                )
            },
        }


_REQUIRES_MEDIA_FAMILIES = {
    "hero.photo_cover", "hero.split_photo", "hero.collage", "hero.cinematic",
    "hero.project", "hero.material", "hero.transformation", "hero.rail",
}

# Bespoke family markup (families.py) that ships its own mobile CSS override
# in styles.FAMILY_CSS, keyed to the CSS class actually used for the
# multi-column desktop layout that needs collapsing. Components not listed
# here either have no bespoke treatment (generic path, covered by the shared
# .g-layout mobile rule -- see styles.BASE_CSS) or use a small fixed-width
# column (e.g. a numeral) that does not need a collapse rule at any width.
# The check below verifies these classes actually appear inside a mobile
# media query in the real, shipped CSS -- it does not just assert this table
# is true, so removing a rule later would show up as a real score drop.
_BESPOKE_MOBILE_CSS_TARGETS = {
    "service_bento": "service-bento-grid",
    "technical_nodes_network": "hero-network-layout",
    "material_macro_title": "g-material-hero",
    "conversion_service_selector": "service-selector-grid",
    "workshop_service_samples": "service-material-samples",
    "editorial_columns_manifesto": "hero-manifesto-columns",
    "editorial_title_index": "hero-type--editorial-index",
    "architectural_void_statement": "hero-type--void",
}


def _empty_slot_risk(plan: RenderPlan) -> CompletenessDimension:
    """Inspects the final plan for a section that is rendered (``full`` or
    ``reduced``) but structurally implies a media region with nothing in it
    -- rather than assuming the renderer's own no-empty-media guarantee
    (rule 12: "ne hardcode plus 1.0 uniquement parce que des tests
    existent"). ``layout_regions()`` still guarantees no empty ``.g-media``
    div can reach the DOM (covered by its own tests); this dimension is the
    plan-level check that nothing *should* have needed one in the first
    place without that being recorded as an honest fallback.
    """
    reasons: list[str] = []
    for section in plan.rendered_sections:
        if section.section == "gallery" and not section.resolved_media:
            reasons.append(f"gallery is '{section.renderability}' with zero resolved_media")
            continue
        if section.section == "hero" and section.resolved_mode == "media" and not section.resolved_media:
            reasons.append("hero resolved_mode is 'media' but resolved_media is empty")
            continue
        component = ALL_COMPONENTS.get(section.component_id)
        if (
            component is not None
            and component.image_dependency >= 0.7
            and section.renderability == "full"
            and not section.resolved_media
            and not section.fallback_used
            and section.section not in {"services", "trust", "cta", "contact"}
        ):
            reasons.append(
                f"{section.section} ({section.component_id}) has image_dependency="
                f"{component.image_dependency} but resolved 'full' with zero media and no recorded fallback"
            )
    if reasons:
        return CompletenessDimension(round(max(0.0, 1.0 - 0.25 * len(reasons)), 3), tuple(reasons))
    return CompletenessDimension(
        1.0, ("plan contains no section that is rendered with an implied-but-unresolved media region",)
    )


def _mobile_readiness(plan: RenderPlan) -> CompletenessDimension:
    """Structural mobile-risk signals from the resolved plan's own component
    metadata and the actually-shipped CSS -- not a claim about how the page
    looks on a phone (rule 13/43: that judgement needs a real browser and
    stays with ``browser-validation.json``/human review). Checks:

    - every rendered component declares a mobile collapse_strategy and
      priority_anchor (guaranteed by the Design Genome's own component
      factory, but verified here rather than assumed);
    - the hero declares a mobile media_behaviour (relevant only when the
      hero actually carries media);
    - a bespoke multi-column family treatment (bento, network, material,
      selector, ...) has a verified mobile override in the real CSS;
    - a visible action path (contact/cta) survives to mobile at all.
    """
    reasons: list[str] = []
    checks = 0
    passed = 0

    for section in plan.rendered_sections:
        component = ALL_COMPONENTS.get(section.component_id)
        if component is None:
            continue
        checks += 1
        mobile_spec = component.blueprint_spec.mobile_spec
        if mobile_spec.get("collapse_strategy") and mobile_spec.get("priority_anchor"):
            passed += 1
        else:
            reasons.append(f"{section.section} ({component.id}) has no declared mobile collapse_strategy/priority_anchor")

    hero = plan.section("hero")
    if hero is not None and hero.resolved_media:
        component = ALL_COMPONENTS.get(hero.component_id)
        checks += 1
        if component is not None and component.blueprint_spec.mobile_spec.get("media_behavior"):
            passed += 1
        else:
            reasons.append("hero carries media but declares no mobile media_behavior")

    from .styles import FAMILY_CSS
    mobile_css = "".join(FAMILY_CSS.split("@media(max-width:900px)")[1:]) if "@media(max-width:900px)" in FAMILY_CSS else ""
    for section in plan.rendered_sections:
        target_class = _BESPOKE_MOBILE_CSS_TARGETS.get(section.component_id)
        if target_class is None:
            continue
        checks += 1
        if f".{target_class}" in mobile_css:
            passed += 1
        else:
            reasons.append(f"{section.component_id}'s .{target_class} has no verified mobile override in FAMILY_CSS")

    checks += 1
    if any(s.section in {"contact", "cta"} for s in plan.rendered_sections):
        passed += 1
    else:
        reasons.append("no contact/cta section rendered -- no visible action path survives to mobile")

    score = round(passed / checks, 3) if checks else 1.0
    if not reasons:
        reasons = ("every rendered section declares mobile collapse metadata; a conversion path is present",)
    return CompletenessDimension(score, tuple(reasons))


def assess(plan: RenderPlan) -> VisualCompletenessReport:
    hero = plan.sections[0]
    rendered_sections = list(plan.rendered_sections)

    # hero_readiness: real media, or an honest no-image/abstract composition
    # that its own family policy actually allows.
    if hero.family in _REQUIRES_MEDIA_FAMILIES and hero.fallback_used and not hero.resolved_media:
        if plan.resolved_hero_component != plan.initial_hero_component:
            hero_readiness = CompletenessDimension(0.75, (f"recomposed from {plan.initial_hero_component}: {hero.fallback_reason}",))
        else:
            hero_readiness = CompletenessDimension(0.3, (hero.fallback_reason,))
    elif hero.resolved_media:
        hero_readiness = CompletenessDimension(1.0, ())
    else:
        # No media, but this family never required it -- an intentional
        # typographic composition or a tolerant technical/spatial/conversion
        # abstract fallback are both a legitimate, full-score outcome.
        hero_readiness = CompletenessDimension(1.0, (hero.fallback_reason,) if hero.fallback_used else ())

    # media_readiness: share of media-eligible sections in an honest state.
    media_eligible = [s for s in plan.sections if s.section in {"hero", "gallery", "about"}]

    def _ready(s):
        if s.section == "about":
            return True
        if s.section == "hero":
            return bool(s.resolved_media) or not s.fallback_used
        return bool(s.resolved_media)

    media_ok = [s for s in media_eligible if _ready(s)]
    media_readiness = CompletenessDimension(
        round(len(media_ok) / len(media_eligible), 2) if media_eligible else 1.0,
        tuple(f"{s.section}: no compatible media in the allocation pool" for s in media_eligible if not _ready(s)),
    )

    # content_density / commercial_completeness: rule AD -- hero+services
    # alone is generally not a complete commercial page.
    rendered_names = {s.section for s in rendered_sections}
    substantive = rendered_names - {"hero"}
    content_density = CompletenessDimension(min(1.0, len(substantive) / 3), ())
    has_conversion_path = "contact" in rendered_names or "cta" in rendered_names
    if substantive <= {"services"} and not has_conversion_path:
        commercial_completeness = CompletenessDimension(0.35, ("only hero+services rendered, with no explicit conversion path",))
    elif not has_conversion_path:
        commercial_completeness = CompletenessDimension(0.6, ("no explicit contact/CTA section rendered",))
    else:
        commercial_completeness = CompletenessDimension(1.0, ())

    # narrative_completeness: about either says something new or was honestly reduced/omitted.
    about_plan = plan.section("about")
    if about_plan is None:
        narrative_completeness = CompletenessDimension(1.0, ("no about section in this silhouette",))
    elif about_plan.renderability == "reduced":
        narrative_completeness = CompletenessDimension(0.7, ("about narrative duplicated the hero tagline; reduced to a fact strip",))
    elif about_plan.renderability == "omitted":
        narrative_completeness = CompletenessDimension(0.5, ("about had nothing but duplicate copy and no facts; omitted",))
    else:
        narrative_completeness = CompletenessDimension(1.0, ())

    # section_balance: not everything at the same visual_weight (rule AF/AG).
    weights = {s.visual_weight for s in rendered_sections}
    section_balance = CompletenessDimension(
        1.0 if len(weights) > 1 else 0.6,
        () if len(weights) > 1 else ("every rendered section shares the same visual_weight",),
    )

    empty_slot_risk = _empty_slot_risk(plan)

    # art_direction_fidelity: V0.2.1 -- a media-led hero is necessary but not
    # sufficient. hero_anchor_consistency (from CoherenceReport) already
    # catches a resolved plan that pairs the hero's direction with a section
    # whose own traits the Design Genome scores as antagonistic to it (rule
    # 22: site-11 must not auto-score 1.0 just because its hero has a photo).
    if hero.family in _REQUIRES_MEDIA_FAMILIES and not hero.resolved_media and plan.resolved_hero_component == plan.initial_hero_component:
        media_component, media_reason = 0.2, f"{plan.art_direction} promised media-led {hero.family}; none resolved and no recomposition recorded"
    else:
        media_component, media_reason = 1.0, ""
    coherence_component = plan.coherence.hero_anchor_consistency.score
    fidelity_score = round(media_component * 0.5 + coherence_component * 0.5, 3)
    fidelity_reasons = tuple(r for r in (media_reason,) if r) + plan.coherence.hero_anchor_consistency.reasons
    art_direction_fidelity = CompletenessDimension(fidelity_score, fidelity_reasons)

    # visual_rhythm: patterns and weights should not all repeat identically.
    patterns = [s.layout_pattern for s in rendered_sections]
    repeats = len(patterns) - len(set(patterns))
    visual_rhythm = CompletenessDimension(
        max(0.4, 1.0 - repeats * 0.15),
        (f"{repeats} rendered section(s) reuse an already-used layout pattern",) if repeats else (),
    )

    mobile_readiness = _mobile_readiness(plan)

    return VisualCompletenessReport(
        fixture_id=plan.fixture_id,
        hero_readiness=hero_readiness,
        media_readiness=media_readiness,
        content_density=content_density,
        commercial_completeness=commercial_completeness,
        narrative_completeness=narrative_completeness,
        section_balance=section_balance,
        empty_slot_risk=empty_slot_risk,
        art_direction_fidelity=art_direction_fidelity,
        visual_rhythm=visual_rhythm,
        mobile_readiness=mobile_readiness,
    )
